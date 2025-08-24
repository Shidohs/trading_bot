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
        self.console.print("🔌 [yellow]Intentando conectar al WebSocket...[/yellow]")
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
        self.console.print("🔌 [yellow]Hilo WebSocket iniciado...[/yellow]")

    def send(self, payload):
        try:
            if self.ws:
                self.ws.send(json.dumps(payload))
        except Exception as e:
            self.console.print(f"[red]No se pudo enviar WS: {e}[/red]")

    def on_open(self, ws):
        self.console.print("🔌 [green]Conexión WS abierta. Autenticando...[/green]")
        self.send({"authorize": self.token})
        self.console.print("🔑 [green]Autenticación enviada...[/green]")

    def on_message(self, ws, message):
        self.console.print(f"[blue]Mensaje recibido: {message[:200]}...[/blue]")
        try:
            data = json.loads(message)
        except Exception as e:
            self.console.print(f"[red]WS JSON error: {e}[/red]")
            return

        msg_type = data.get("msg_type")
        self.console.print(f"[blue]Tipo de mensaje: {msg_type}[/blue]")
        if msg_type == "authorize":
            self.console.print("✅ [green]Autorizado[/green]. Obteniendo balance...")
            self.send({"balance": 1, "account": "current"})
            # suscribir OHLC 1m para cada símbolo
            for s in self.symbols:
                self.console.print(f"📡 [cyan]Suscribiendo a {s}...[/cyan]")
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
                self.console.print(f"💰 [green]Balance actualizado: {bal}[/green]")
        elif msg_type == "candles":
            symbol = data.get("echo_req", {}).get("ticks_history")
            candles = data.get("candles", [])
            self.console.print(
                f"📊 [cyan]Recibidas {len(candles)} velas para {symbol}[/cyan]"
            )
            for c in candles:
                ohlc = {
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                    "epoch": int(c["epoch"]),
                }
                self.buffers.push_ohlc_1m(symbol, ohlc)
            self._evaluate_symbol(symbol)
        elif msg_type == "ohlc":
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
            error_msg = data.get("error", {})
            self.console.print(f"[red]WS Error: {error_msg}[/red]")

    def _evaluate_symbol(self, symbol):
        feats = self.features.compute_features(symbol)
        if not feats["m1"] or not feats["m5"] or not feats["m15"]:
            console.print(
                f"[yellow]⚠️  {symbol}: Datos insuficientes para análisis[/yellow]"
            )
            return

        score, direction, sigs = self.strategy.score(feats)
        prob = round(score * 100, 2)
        global ultima_accion, probabilities
        probabilities["buy"] = prob if direction == "CALL" else 100 - prob
        probabilities["sell"] = 100 - probabilities["buy"]
        ultima_accion = f"{symbol} {direction} {prob:.2f}% | {' '.join(sigs)}"

        # Debug logging
        console.print(
            f"[cyan]🔍 {symbol}: Score={prob:.2f}% (Umbral: {self.strategy.threshold*100:.0f}%)[/cyan]"
        )
        console.print(f"   Señales: {', '.join(sigs)}")

        lim = self.risk.check_daily_limits(self.engine.balance)
        if lim == "tp":
            console.print("[yellow]✅ TP diario alcanzado. Pausando.[/yellow]")
            return
        if lim == "dd":
            console.print("[red]🛑 DD diario alcanzado. Pausando.[/red]")
            return

        can_open = self.engine.can_open(symbol)
        can_trade = self.risk.can_trade_now(self.engine.balance)

        console.print(f"   Puede abrir: {can_open}, Puede tradear: {can_trade}")

        if score >= self.strategy.threshold and can_open and can_trade:
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
                f"[green]📤 SEÑAL EJECUTADA: {symbol} {direction} | Score={prob:.2f}% | Stake={stake}[/green]"
            )
            threading.Timer(120, self._simulate_close, args=(trade_id,)).start()
        else:
            if score < self.strategy.threshold:
                console.print(
                    f"[yellow]   Score insuficiente: {score:.2f} < {self.strategy.threshold}[/yellow]"
                )
            elif not can_open:
                console.print(
                    f"[yellow]   Límite de órdenes alcanzado para {symbol}[/yellow]"
                )
            elif not can_trade:
                console.print(
                    f"[yellow]   Gestión de riesgo bloqueando trades[/yellow]"
                )

    def _simulate_close(self, trade_id):
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
        self.console.print(
            "[red]Error en la conexión WebSocket. Verifica la configuración.[/red]"
        )

    def on_close(self, ws, code, msg):
        self.console.print(
            f"[yellow]🔌 Conexión WS cerrada - Código: {code}, Mensaje: {msg}[/yellow]"
        )
        self.console.print("[yellow]Verifica la conexión y vuelve a intentar.[/yellow]")
