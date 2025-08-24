# utils/logger.py
import csv
import time
import os
from datetime import datetime
from pathlib import Path


class SimpleLogger:
    def __init__(self):
        # Crear directorio logs si no existe
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Archivo CSV para trades
        today = datetime.now().strftime("%Y%m%d")
        self.trades_csv = self.log_dir / f"trades_{today}.csv"

        # Crear header si no existe
        if not self.trades_csv.exists():
            with open(self.trades_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "symbol",
                        "direction",
                        "amount",
                        "score",
                        "action",
                        "profit",
                        "balance",
                    ]
                )

        # Archivo de debug
        self.debug_file = self.log_dir / f"debug_{today}.log"

        # Contadores
        self.stats = {
            "trades_opened": 0,
            "trades_closed": 0,
            "total_profit": 0.0,
            "messages_received": 0,
            "candles_processed": 0,
            "evaluations_run": 0,
        }

    def log_trade(
        self, symbol, direction, amount, score_or_profit, action, balance=None
    ):
        """Registra un trade"""
        data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            direction,
            amount,
            score_or_profit,
            action,
            score_or_profit if action == "CLOSE" else 0,
            balance or 0,
        ]

        with open(self.trades_csv, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(data)

        if action == "OPEN":
            self.stats["trades_opened"] += 1
        elif action == "CLOSE":
            self.stats["trades_closed"] += 1
            if isinstance(score_or_profit, (int, float)):
                self.stats["total_profit"] += score_or_profit

        self.debug(f"TRADE {action}: {symbol} {direction} ${amount}")

    def debug(self, message):
        """Log de debug"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"

        # Escribir a archivo
        with open(self.debug_file, "a") as f:
            f.write(log_line)

        # También mostrar en consola si es importante
        if any(
            word in message.upper()
            for word in ["ERROR", "TRADE", "CONECTADO", "BALANCE"]
        ):
            print(log_line.strip())

    def update_stat(self, stat_name):
        """Actualiza estadística"""
        if stat_name in self.stats:
            self.stats[stat_name] += 1


# Instancia global
logger = SimpleLogger()


def exportar_log(data, log_file=None):
    """Función compatible con el código existente"""
    if len(data) >= 6:
        timestamp, symbol, direction, amount, score_or_profit, action = data[:6]
        logger.log_trade(symbol, direction, amount, score_or_profit, action)
    else:
        logger.debug(f"LOG: {data}")


def log_debug(message):
    """Log de debug"""
    logger.debug(message)


def log_websocket(event, message):
    """Log de WebSocket"""
    logger.debug(f"WS_{event}: {message}")
    if event == "MESSAGE_RECEIVED":
        logger.update_stat("messages_received")
    elif event == "CANDLE":
        logger.update_stat("candles_processed")
    elif event == "EVALUATION":
        logger.update_stat("evaluations_run")
