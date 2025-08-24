# core/websocket_client_enhanced.py
import websocket
import json
import threading
import time
import numpy as np
from collections import defaultdict
from queue import Queue
from rich.console import Console
from utils.logger import exportar_log, log_debug, log_websocket
from config import WS_PING_INTERVAL, WS_PING_TIMEOUT, WS_RECONNECT_DELAY

console = Console()

# Variables globales
probabilities = {"buy": 0, "sell": 0}
ultima_accion = None
connection_status = {
    "connected": False,
    "authorized": False,
    "balance_received": False,
    "messages_count": 0,
}


class DerivWS:
    def __init__(
        self, app_id, token, symbols, engine, buffers, features, strategy, risk
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
        self._last_candle_epoch = defaultdict(int)
        self.debug_mode = True
        self.tick_buffers = defaultdict(list)  # Para acumular ticks por símbolo
        self.last_candle_time = defaultdict(float)  # Última vela creada por símbolo
        self.message_queue = Queue()

        # Contadores para debug
        self.message_count = 0
        self.evaluations = 0
        self.trades_opened = 0

    def debug_print(self, message, level="INFO"):
        """Sistema de debug simplificado"""
        if self.debug_mode:
            timestamp = time.strftime("%H:%M:%S")
            colors = {
                "INFO": "cyan",
                "SUCCESS": "green",
                "WARNING": "yellow",
                "ERROR": "red",
            }
            color = colors.get(level, "white")
            console.print(f"[{color}][{timestamp}] {message}[/{color}]")
            log_debug(f"{level}: {message}")

    def connect(self):
        self.debug_print("🔌 Conectando al WebSocket de Deriv...", "INFO")
        url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"

        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        # Iniciar WebSocket en hilo separado
        ws_thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs={"ping_interval": WS_PING_INTERVAL, "ping_timeout": WS_PING_TIMEOUT},
            daemon=True,
        )
        ws_thread.start()
        self.debug_print("🔌 Hilo WebSocket iniciado", "SUCCESS")

        # Iniciar procesador de mensajes en un hilo separado
        processor_thread = threading.Thread(target=self._message_processor, daemon=True)
        processor_thread.start()
        self.debug_print("⚙️  Hilo de procesamiento iniciado", "SUCCESS")

        # Iniciar monitor de actividad
        monitor_thread = threading.Thread(target=self._activity_monitor, daemon=True)
        monitor_thread.start()

    def _activity_monitor(self):
        """Monitor que reporta el estado cada minuto y verifica la conexión"""
        last_message_count = self.message_count
        inactivity_counter = 0

        while True:
            time.sleep(60)  # Cada minuto

            status_report = f"📊 ESTADO: Conectado={connection_status['connected']}, "
            status_report += f"Autorizado={connection_status['authorized']}, "
            status_report += f"Mensajes={self.message_count}, "
            status_report += f"Evaluaciones={self.evaluations}, "
            status_report += f"Trades={self.trades_opened}"

            self.debug_print(status_report, "INFO")

            # Verificar actividad de mensajes
            if self.message_count == last_message_count:
                inactivity_counter += 1
                self.debug_print(
                    f"⚠️  Sin actividad de mensajes por {inactivity_counter} minutos",
                    "WARNING",
                )

                # Si no hay actividad por 3 minutos, verificar conexión
                if inactivity_counter >= 3:
                    self.debug_print(
                        "🔄 Inactividad prolongada, verificando conexión...", "WARNING"
                    )
                    if not self.connected or not (
                        self.ws and self.ws.sock and self.ws.sock.connected
                    ):
                        self.debug_print(
                            "❌ Conexión perdida, intentando reconectar...", "ERROR"
                        )
                        self._reconnect()
                        inactivity_counter = 0
            else:
                inactivity_counter = 0
                last_message_count = self.message_count

            # Verificar si el WebSocket sigue conectado
            if self.ws and hasattr(self.ws, "sock") and self.ws.sock:
                try:
                    # Intentar enviar un ping para verificar la conexión
                    self.ws.sock.ping()
                except Exception as e:
                    self.debug_print(f"❌ Error verificando conexión: {e}", "ERROR")
                    self._reconnect()

    def send(self, payload):
        """Envío con logging"""
        try:
            if self.ws and self.ws.sock:
                message = json.dumps(payload)
                self.ws.send(message)
                msg_type = payload.get("msg_type", list(payload.keys())[0])
                self.debug_print(f"📤 Enviado: {msg_type}", "INFO")
                return True
            else:
                self.debug_print("❌ WebSocket no conectado", "ERROR")
                return False
        except Exception as e:
            self.debug_print(f"❌ Error enviando: {e}", "ERROR")
            return False

    def on_open(self, ws):
        self.debug_print("🔌 Conexión WebSocket abierta", "SUCCESS")
        connection_status["connected"] = True
        self.connected = True

        # Enviar autorización
        success = self.send({"authorize": self.token})
        if success:
            self.debug_print("🔑 Autorización enviada", "INFO")

    def on_message(self, ws, message):
        """Añade mensaje a la cola para procesamiento asíncrono"""
        self.message_queue.put(message)

    def _message_processor(self):
        """Procesa mensajes de la cola en un bucle continuo"""
        while True:
            message = self.message_queue.get()
            if message is None:
                break

            self.message_count += 1
            connection_status["messages_count"] = self.message_count
            if self.message_count % 100 == 0:
                log_websocket("MESSAGE_RECEIVED", f"Mensaje #{self.message_count}")

            try:
                data = json.loads(message)
                msg_type = data.get("msg_type", "unknown")

                if self.message_count % 10 == 0:
                    self.debug_print(
                        f"📨 Mensaje #{self.message_count}: {msg_type}", "INFO"
                    )

                if msg_type == "authorize":
                    if data.get("authorize"):
                        connection_status["authorized"] = True
                        self.debug_print("✅ Autorización exitosa", "SUCCESS")
                        self.send({"balance": 1, "account": "current"})
                    else:
                        error_msg = data.get("error", {}).get(
                            "message", "Error desconocido"
                        )
                        self.debug_print(
                            f"❌ Autorización fallida: {error_msg}", "ERROR"
                        )

                elif msg_type == "balance":
                    balance_info = data.get("balance", {})
                    if balance_info:
                        balance = balance_info.get("balance", 0)
                        self.engine.set_balance(float(balance))
                        connection_status["balance_received"] = True
                        self.debug_print(f"💰 Balance: {balance} USD", "SUCCESS")
                        self._start_subscriptions()

                elif msg_type == "candles":
                    self._handle_historical_candles(data)

                elif msg_type == "ohlc":
                    self._handle_live_candle(data)

                elif msg_type == "error":
                    error_info = data.get("error", {})
                    error_msg = error_info.get("message", "Error desconocido")
                    self.debug_print(f"❌ Error del servidor: {error_msg}", "ERROR")

                elif msg_type == "tick":
                    self._handle_tick(data)

                elif msg_type == "history":
                    self._handle_tick_history(data)

            except Exception as e:
                self.debug_print(f"❌ Error procesando mensaje: {e}", "ERROR")
            finally:
                self.message_queue.task_done()

    def _start_subscriptions(self):
        """Inicia suscripciones"""
        self.debug_print("📡 Iniciando suscripciones...", "INFO")

        for symbol in self.symbols:
            success = self.send(
                {
                    "ticks_history": symbol,
                    "adjust_start_time": 1,
                    "count": 5000,
                    "end": "latest",
                    "granularity": 60,
                    "subscribe": 1,
                }
            )
            if success:
                self.debug_print(f"📡 Suscrito a {symbol}", "SUCCESS")

    def _handle_tick_history(self, data):
        """Maneja historial de ticks y los convierte en velas"""
        echo_req = data.get("echo_req", {})
        symbol = echo_req.get("ticks_history")
        history = data.get("history", {})
        prices = history.get("prices", [])
        times = history.get("times", [])

        if not symbol or not prices:
            return

        self.debug_print(
            f"📊 Historial de {len(prices)} ticks para {symbol}", "SUCCESS"
        )

        # Convertir ticks en velas de 1 minuto
        candles = self._ticks_to_candles(prices, times)

        # Procesar velas
        for candle in candles:
            self.buffers.push_ohlc_1m(symbol, candle)

        log_websocket("CANDLE", f"Convertidas {len(candles)} velas para {symbol}")
        self._evaluate_symbol(symbol)

    def _handle_tick(self, data):
        """Maneja tick individual"""
        tick = data.get("tick", {})
        symbol = tick.get("symbol")
        price = tick.get("quote")
        epoch = tick.get("epoch")

        if not all([symbol, price, epoch]):
            return

        # Acumular tick
        self.tick_buffers[symbol].append({"price": float(price), "epoch": int(epoch)})

        # Verificar si hay que crear una nueva vela (cada 5 segundos)
        now = time.time()
        if now - self.last_candle_time.get(symbol, 0) > 5:
            self.last_candle_time[symbol] = now
            current_minute = int(epoch) // 60
            self._create_candle_from_ticks(symbol, current_minute)

    def _create_candle_from_ticks(self, symbol, minute_timestamp):
        """Crea una vela OHLC a partir de ticks acumulados"""
        ticks = self.tick_buffers[symbol]

        if not ticks:
            return

        # Filtrar ticks del minuto específico
        minute_ticks = [t for t in ticks if int(t["epoch"]) // 60 == minute_timestamp]

        if not minute_ticks:
            return

        prices = [t["price"] for t in minute_ticks]

        ohlc = {
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "epoch": minute_timestamp * 60,
        }

        self.buffers.push_ohlc_1m(symbol, ohlc)
        self.debug_print(f"📈 Vela creada {symbol}: {ohlc['close']:.5f}", "INFO")
        log_websocket("CANDLE", f"Vela creada {symbol}")

        # Limpiar ticks antiguos (mantener solo últimos 200)
        if len(self.tick_buffers[symbol]) > 200:
            self.tick_buffers[symbol] = self.tick_buffers[symbol][-200:]

        self._evaluate_symbol(symbol)

    def _ticks_to_candles(self, prices, times):
        """Convierte arrays de precios y tiempos en velas OHLC"""
        if not prices or not times:
            return []

        candles = []
        current_minute = None
        minute_prices = []

        for price, timestamp in zip(prices, times):
            minute = int(timestamp) // 60

            if current_minute is None:
                current_minute = minute

            if minute == current_minute:
                minute_prices.append(float(price))
            else:
                # Crear vela para el minuto anterior
                if minute_prices:
                    candles.append(
                        {
                            "open": minute_prices[0],
                            "high": max(minute_prices),
                            "low": min(minute_prices),
                            "close": minute_prices[-1],
                            "epoch": current_minute * 60,
                        }
                    )

                # Empezar nuevo minuto
                current_minute = minute
                minute_prices = [float(price)]

        # Agregar última vela
        if minute_prices and current_minute is not None:
            candles.append(
                {
                    "open": minute_prices[0],
                    "high": max(minute_prices),
                    "low": min(minute_prices),
                    "close": minute_prices[-1],
                    "epoch": current_minute * 60,
                }
            )

        return candles

    def _handle_historical_candles(self, data):
        """Maneja velas históricas"""
        echo_req = data.get("echo_req", {})
        symbol = echo_req.get("ticks_history")
        candles = data.get("candles", [])

        if symbol and candles:
            self.debug_print(
                f"📊 {len(candles)} velas históricas para {symbol}", "SUCCESS"
            )

            for candle in candles:
                ohlc = {
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "epoch": int(candle["epoch"]),
                }
                self.buffers.push_ohlc_1m(symbol, ohlc)

            log_websocket("CANDLE", f"Procesadas {len(candles)} velas para {symbol}")
            self._evaluate_symbol(symbol)

    def _handle_live_candle(self, data):
        """Maneja velas en vivo"""
        ohlc_data = data.get("ohlc", {})
        symbol = ohlc_data.get("symbol")
        epoch = int(ohlc_data.get("epoch", 0))

        if symbol and epoch != self._last_candle_epoch[symbol]:
            self._last_candle_epoch[symbol] = epoch

            ohlc = {
                "open": float(ohlc_data["open"]),
                "high": float(ohlc_data["high"]),
                "low": float(ohlc_data["low"]),
                "close": float(ohlc_data["close"]),
                "epoch": epoch,
            }

            self.buffers.push_ohlc_1m(symbol, ohlc)
            self.debug_print(f"📈 Nueva vela {symbol}: {ohlc['close']:.5f}", "INFO")
            log_websocket("CANDLE", f"Nueva vela {symbol}")

            self._evaluate_symbol(symbol)

    def _evaluate_symbol(self, symbol):
        """Evaluación con debug"""
        self.evaluations += 1
        log_websocket("EVALUATION", f"Evaluando {symbol} (#{self.evaluations})")

        # Verificar datos suficientes para todas las temporalidades
        m1_ok = len(self.buffers.m1.get(symbol, [])) >= 35
        m5_ok = len(self.buffers.m5.get(symbol, [])) >= 35
        m15_ok = len(self.buffers.m15.get(symbol, [])) >= 35

        if not all([m1_ok, m5_ok, m15_ok]):
            if self.evaluations % 50 == 0:  # Loguear solo de vez en cuando
                self.debug_print(
                    f"⚠️  {symbol}: Esperando datos suficientes (M1:{m1_ok}, M5:{m5_ok}, M15:{m15_ok})",
                    "WARNING",
                )
            return

        try:
            # Calcular features
            feats = self.features.compute_features(symbol)
            if not all([feats["m1"], feats["m5"], feats["m15"]]):
                self.debug_print(f"❌ {symbol}: Error calculando features", "ERROR")
                return

            # Obtener score y duración dinámica
            (
                score,
                direction,
                duration,
                signals,
                feature_vector,
            ) = self.strategy.score(feats)
            prob = score * 100

            # Actualizar variables globales
            global ultima_accion, probabilities
            probabilities["buy"] = prob if direction == "CALL" else 100 - prob
            probabilities["sell"] = 100 - probabilities["buy"]
            ultima_accion = f"{symbol} {direction} {prob:.1f}%"

            # Log detallado cada cierto tiempo
            if self.evaluations % 20 == 0 or prob > 75:
                self.debug_print(
                    f"🎯 {symbol}: Score={prob:.1f}%, Dir={direction}", "INFO"
                )
                self.debug_print(f"   Señales: {', '.join(signals[:3])}", "INFO")

            # Verificar si se puede tradear
            lim = self.risk.check_daily_limits(self.engine.balance)
            if lim:
                if lim == "tp":
                    self.debug_print("✅ Take Profit diario alcanzado", "SUCCESS")
                else:
                    self.debug_print("🛑 Drawdown diario alcanzado", "WARNING")
                return

            can_open = self.engine.can_open(symbol)
            can_trade = self.risk.can_trade_now(self.engine.balance)

            # Abrir trade si cumple condiciones
            if score >= self.strategy.threshold and can_open and can_trade:
                stake = self.risk.compute_stake(self.engine.balance)
                trade_id = self.engine.open_trade(
                    symbol, direction, stake, feature_vector, duration=duration
                )

                self.trades_opened += 1

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

                self.debug_print(
                    f"🚀 TRADE ABIERTO #{self.trades_opened}: {symbol} {direction}",
                    "SUCCESS",
                )
                self.debug_print(
                    f"   Stake: {stake} USD, Score: {prob:.1f}%", "SUCCESS"
                )

                # Programar cierre
                threading.Timer(120, self._simulate_close, args=(trade_id,)).start()

        except Exception as e:
            self.debug_print(f"❌ Error evaluando {symbol}: {e}", "ERROR")

    def _simulate_close(self, trade_id):
        """Simula cierre de trade"""
        if trade_id not in self.engine.trades:
            return

        win = np.random.rand() < 0.55
        trade = self.engine.trades[trade_id]
        stake = trade["amount"]
        profit = round(stake * 0.9, 2) if win else -stake

        self.engine.finalize_trade(trade_id, profit)

        exportar_log(
            [
                time.strftime("%Y-%m-%d %H:%M:%S"),
                trade["symbol"],
                trade["contract_type"],
                stake,
                profit,
                "CLOSE",
            ]
        )

        result = "WIN" if profit > 0 else "LOSS"
        self.debug_print(
            f"📦 TRADE CERRADO: {trade_id} {result} {profit:+.2f}", "SUCCESS"
        )

    def _reconnect(self):
        """Intenta reconectar el WebSocket"""
        self.debug_print("🔄 Iniciando proceso de reconexión...", "WARNING")
        try:
            # Cerrar conexión existente si está abierta
            if self.ws and self.ws.sock:
                self.ws.close()

            # Esperar un momento antes de reconectar
            time.sleep(2)

            # Reconectar
            self.connect()
            self.debug_print("✅ Reconexión iniciada", "SUCCESS")
        except Exception as e:
            self.debug_print(f"❌ Error en reconexión: {e}", "ERROR")
            # Reintentar después de un delay
            threading.Timer(WS_RECONNECT_DELAY, self._reconnect).start()

    def on_error(self, ws, error):
        self.debug_print(f"❌ Error WebSocket: {error}", "ERROR")
        # Intentar reconexión en caso de error
        if "timed out" in str(error) or "ping" in str(error).lower():
            self.debug_print(
                "🔄 Error de timeout detectado, intentando reconectar...", "WARNING"
            )
            threading.Timer(WS_RECONNECT_DELAY, self._reconnect).start()

    def on_close(self, ws, code, msg):
        self.debug_print(f"🔌 Conexión cerrada: {code} - {msg}", "WARNING")
        connection_status["connected"] = False
        self.connected = False

        # Intentar reconexión automática si no es un cierre intencional
        if code != 1000:  # 1000 es cierre normal
            self.debug_print(
                f"🔄 Intentando reconectar en {WS_RECONNECT_DELAY} segundos...",
                "WARNING",
            )
            threading.Timer(WS_RECONNECT_DELAY, self._reconnect).start()
