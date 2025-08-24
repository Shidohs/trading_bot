import websocket
import json
import threading
import time
import numpy as np
from collections import defaultdict
from rich.console import Console
from utils.logger import exportar_log

console = Console()

# ------------------- VARIABLES GLOBALES -------------------
probabilities = {"buy": 0, "sell": 0}
ultima_accion = None


class DerivWS:
    """
    Cliente WebSocket para:
      - Autorizar
      - Obtener balance
      - Suscribirse a OHLC de 1m por símbolo
      - Reconstruir MTF y evaluar estrategia en cada vela
    """

    def __init__(
        self,
        app_id,
        token,
        symbols,
        engine,
        buffers,
        features,
        strategy,
        risk,
    ):
        self.app_id = app_id
        self.token = token
        self.symbols = symbols
        self.engine = engine
        self.buffers = buffers
        self.features = features
        self.strategy = strategy
        self.risk = risk
        self.ws = None
        self.connected = False
        self.console = console
        self._lock = threading.Lock()
        self._last_candle_epoch = defaultdict(int)

    def connect(self):
        url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        threading.Thread(
            target=self.ws.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
        ).start()

    def send(self, payload):
        try:
            self.ws.send(json.dumps(payload))
        except Exception as e:
            self.console.print(f"[red]No se pudo enviar WS: {e}[/red]")

    def on_open(self, ws):
        self.console.print("🔌 [green]Conexión WS abierta. Autenticando...[/green]")
        self.send({"authorize": self.token})

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception as e:
            self.console.print(f"[red]WS JSON error: {e}[/red]")
            return

        msg_type = data.get("msg_type")
        if msg_type == "authorize":
            self.console.print("✅ [green]Autorizado[/green]. Obteniendo balance...")
            self.send({"balance": 1, "account": "current"})
            # suscribir OHLC 1m para cada símbolo
            for s in self.symbols:
                # [No verificado] payload de OHLC suscripción en Deriv:
                self.send(
                    {
                        "ticks_history": s,
                        "adjust_start_time": 1,
                        "count": 500,
                        "end": "latest",
                        "granularity": 60,
                        "subscribe": 1,
                    }
                )
        elif msg_type == "balance":
            bal = data.get("balance", {}).get("balance")
            if bal is not None:
                self.engine.set_balance(float(bal))
        elif msg_type == "candles":
            # respuesta histórica inicial
            symbol = data.get("echo_req", {}).get("ticks_history")
            candles = data.get("candles", [])
            for c in candles:
                ohlc = {
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                    "epoch": int(c["epoch"]),
                }
                self.buffers.push_ohlc_1m(symbol, ohlc)
            # evaluar al final de la carga inicial
            self._evaluate_symbol(symbol)
        elif msg_type == "ohlc":
            # stream de velas
            o = data.get("ohlc", {})
            symbol = o.get("symbol")
            epoch = int(o.get("epoch", 0))
            if symbol and epoch and epoch != self._last_candle_epoch[symbol]:
                self._last_candle_epoch[symbol] = epoch
                ohlc = {
                    "open": float(o["open"]),
                    "high": float(o["high"]),
                    "low": float(o["low"]),
                    "close": float(o["close"]),
                    "epoch": epoch,
                }
                self.buffers.push_ohlc_1m(symbol, ohlc)
                self._evaluate_symbol(symbol)
        elif msg_type == "error":
            self.console.print(f"[red]WS Error: {data.get('error')}[/red]")

    def _evaluate_symbol(self, symbol):
        feats = self.features.compute_features(symbol)
        score, direction, sigs = self.strategy.score(feats)
        # convertir score 0..1 a %
        prob = round(score * 100, 2)
        global ultima_accion, probabilities
        probabilities["buy"] = prob if direction == "CALL" else 100 - prob
        probabilities["sell"] = 100 - probabilities["buy"]
        ultima_accion = f"{symbol} {direction} {prob:.2f}% | {' '.join(sigs)}"
        # Gestión de riesgo y entrada
        # chequear límites diarios
        lim = self.risk.check_daily_limits(self.engine.balance)
        if lim == "tp":
            console.print("[yellow]✅ TP diario alcanzado. Pausando.[/yellow]")
            return
        if lim == "dd":
            console.print("[red]🛑 DD diario alcanzado. Pausando.[/red]")
            return

        if (
            score >= self.strategy.threshold
            and self.engine.can_open(symbol)
            and self.risk.can_trade_now(self.engine.balance)
        ):
            stake = self.risk.compute_stake(self.engine.balance)
            trade_id = self.engine.open_trade(
                symbol, direction, stake, duration=2, duration_unit="m"
            )
            exportar_log(
                [
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol,
                    direction,
                    stake,
                    prob,
                    "OPEN",
                ]
            )
            console.print(
                f"[green]📤 Señal {symbol} {direction} | Score={prob:.2f}% | Stake={stake}[/green]"
            )
            # [No verificado] Envío de propuesta/compra en Deriv; aquí solo lo registramos.
            # Cierre simulado tras 2 minutos con payoff fijo (para demo); sustituir por seguimiento real de contrato.
            threading.Timer(120, self._simulate_close, args=(trade_id,)).start()

    def _simulate_close(self, trade_id):
        # Simulación: 55% win rate base (solo demo). Sustituir por 'proposal_open_contract' real.
        if trade_id not in self.engine.trades:
            return
        win = np.random.rand() < 0.55
        stake = self.engine.trades[trade_id]["amount"]
        profit = round(stake * 0.9, 2) if win else -stake
        self.engine.finalize_trade(trade_id, profit)
        exportar_log(
            [
                time.strftime("%Y-%m-%d %H:%M:%S"),
                self.engine.trades[trade_id]["symbol"],
                self.engine.trades[trade_id]["contract_type"],
                stake,
                profit,
                "CLOSE",
            ]
        )
        console.print(
            f"[cyan]📦 Cierre {trade_id}: {'WIN' if profit>0 else 'LOSS'} {profit:.2f}[/cyan]"
        )

    def on_error(self, ws, error):
        self.console.print(f"[red]WS Error: {error}[/red]")

    def on_close(self, ws, code, msg):
        self.console.print("[yellow]🔌 Conexión WS cerrada[/yellow]")
