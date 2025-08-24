# main.py
import threading
import time
import signal
import sys
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

# Importar componentes
from core.websocket_client_enhanced import DerivWS
from core.strategy import Strategy
from core.risk import RiskManager
from core.orders import TradeEngine
from core.ohlc_buffers import OHLCBuffers
from core.features import FeatureEngine
from core.correlation import CorrelationGuard
from core.ml_adapter import MLAdvisor
from core.backtester import Backtester
from utils.logger import logger

# Variables de entorno
from dotenv import load_dotenv
import os

load_dotenv()
APP_ID = os.getenv("APP_ID")
TOKEN = os.getenv("TOKEN")

console = Console()
running = True
deriv_client = None


def signal_handler(signum, frame):
    """Manejo de Ctrl+C"""
    global running, deriv_client
    console.print("\n🛑 [yellow]Cerrando bot...[/yellow]")
    running = False

    # Entrenar y guardar el modelo de ML al salir
    if deriv_client and deriv_client.strategy.ml_advisor.ml_available:
        console.print(
            "\n🧠 [cyan]Entrenando modelo de ML con los datos de la sesión...[/cyan]"
        )
        try:
            deriv_client.strategy.ml_advisor.train_from_csv()
        except Exception as e:
            console.print(f"❌ [red]Error durante el entrenamiento: {e}[/red]")

    # Mostrar estadísticas finales
    if logger:
        stats = logger.stats
        console.print("\n📊 [cyan]ESTADÍSTICAS FINALES:[/cyan]")
        for key, value in stats.items():
            console.print(f"   {key}: {value}")

    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def render_layout(engine):
    """Interfaz simplificada"""
    # Header con estado
    header = Table.grid(expand=True)
    header.add_column(justify="left", style="bold cyan")
    header.add_column(justify="center", style="bold yellow")
    header.add_column(justify="right", style="bold magenta")

    from core.websocket_client_enhanced import connection_status

    status_text = "🟢 ACTIVO" if not engine.risk.day_stopped else "🔴 PAUSADO"
    conn_text = (
        "🟢 CONECTADO" if connection_status.get("connected") else "🔴 DESCONECTADO"
    )
    bal_txt = f"{engine.balance:.2f} USD" if engine.balance else "—"

    header.add_row(
        "🤖 Bot Deriv Pro - DEBUG", f"{status_text} | {conn_text}", f"💰 {bal_txt}"
    )
    header_panel = Panel(header, title="Estado General", padding=(1, 2))

    # Tabla de trades
    table = Table(expand=True, show_edge=False)
    table.add_column("ID", justify="center")
    table.add_column("Símbolo", justify="center")
    table.add_column("Tipo", justify="center")
    table.add_column("Monto", justify="center")
    table.add_column("Tiempo", justify="center")
    table.add_column("Profit", justify="center")
    table.add_column("Estado", justify="center")

    now_ts = time.time()
    for trade in engine.trades.values():
        elapsed = (
            f"{int(now_ts - trade['_open_ts'])}s"
            if trade["status"] == "Abierta"
            else trade.get("elapsed", "-")
        )
        profit = trade.get("profit", 0)

        color = "green" if profit > 0 else "red" if profit < 0 else "white"
        profit_str = (
            f"[{color}]{profit:.2f}[/{color}]"
            if isinstance(profit, (int, float))
            else str(profit)
        )

        table.add_row(
            trade.get("id", "")[:8],
            trade.get("symbol", ""),
            trade.get("contract_type", ""),
            f"{trade.get('amount', 0):.2f}",
            elapsed,
            profit_str,
            trade.get("status", ""),
        )

    trades_panel = Panel(table, title="📋 Trades", padding=(1, 2))

    # Panel de señales
    from core.websocket_client_enhanced import probabilities, ultima_accion

    signals_text = f"🎯 Compra: {probabilities.get('buy', 0):.1f}% | Venta: {probabilities.get('sell', 0):.1f}%\n"
    signals_text += f"📊 Última: {ultima_accion or 'Esperando...'}"

    signals_panel = Panel(signals_text, title="🎯 Señales", padding=(1, 2))

    # Panel de estadísticas
    stats = logger.stats
    stats_text = f"📨 Mensajes: {connection_status.get('messages_count', 0)}\n"
    stats_text += (
        f"🎯 Evaluaciones: {deriv_client.evaluations if deriv_client else 0}\n"
    )
    stats_text += f"📤 Trades: {stats['trades_opened']}/{stats['trades_closed']}\n"
    stats_text += f"💰 P&L: {stats['total_profit']:+.2f} USD"

    stats_panel = Panel(stats_text, title="📊 Stats", padding=(1, 2))

    # Layout
    layout = Layout()
    bottom_layout = Layout(name="bottom")
    bottom_layout.split_row(Layout(signals_panel), Layout(stats_panel))

    layout.split_column(
        Layout(header_panel, size=5),
        Layout(trades_panel),
        Layout(bottom_layout, size=6),
    )

    return layout


def start_ui_loop(engine):
    """Loop de interfaz"""
    global running

    with Live(render_layout(engine), console=console, refresh_per_second=1) as live:
        while running:
            try:
                live.update(render_layout(engine))
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error UI: {e}[/red]")
                time.sleep(2)


def start_all():
    """Función principal"""
    global deriv_client

    console.print("\n🚀 [bold cyan]Bot Deriv Pro - Modo Debug[/bold cyan]")

    # Validar configuración
    if not APP_ID or not TOKEN:
        console.print("❌ [red]Configura APP_ID y TOKEN en .env[/red]")
        return

    console.print(f"✅ APP_ID: {APP_ID}")
    console.print(f"✅ TOKEN: {TOKEN[:20]}...")

    # Características del bot
    features = [
        "✅ WebSocket en tiempo real",
        "✅ Análisis MTF (1m/5m/15m)",
        "✅ Indicadores técnicos",
        "✅ Gestión de riesgo",
        "✅ Logging completo",
        "✅ Debug avanzado",
    ]

    for feature in features:
        console.print(f"   {feature}")

    console.print("\n⚙️  [cyan]Inicializando componentes...[/cyan]")

    # Crear componentes
    symbols = ["R_10", "R_25", "R_50", "R_75", "R_100"]
    buffers = OHLCBuffers(maxlen=1000)
    features_engine = FeatureEngine(buffers)
    risk = RiskManager()
    engine = TradeEngine(risk)
    strategy = Strategy()

    # Cargar modelo de ML existente al inicio
    if strategy.ml_advisor.ml_available:
        console.print("\n🧠 [cyan]Cargando modelo de ML existente...[/cyan]")
        strategy.ml_advisor.load_model()

    # Crear cliente WebSocket
    deriv_client = DerivWS(
        APP_ID, TOKEN, symbols, engine, buffers, features_engine, strategy, risk
    )

    console.print("🔌 [green]Conectando...[/green]")
    deriv_client.connect()

    # Esperar conexión
    time.sleep(3)

    console.print("🖥️  [green]Iniciando interfaz...[/green]")

    # Iniciar UI
    ui_thread = threading.Thread(target=start_ui_loop, args=(engine,), daemon=True)
    ui_thread.start()

    console.print("\n🎮 [bold green]Bot funcionando![/bold green]")
    console.print("📝 Logs en: logs/debug_YYYYMMDD.log")
    console.print("📊 Trades en: logs/trades_YYYYMMDD.csv")
    console.print("🔍 Presiona Ctrl+C para detener")


def main():
    """Punto de entrada"""
    try:
        start_all()

        # Mantener vivo
        while running:
            time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Interrupción recibida[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Error crítico: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
