import threading
import time
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from core.websocket_client import DerivWS
from core.strategy import Strategy
from core.risk import RiskManager
from core.orders import TradeEngine
from core.indicators import OHLCBuffers
from core.features import FeatureEngine

# API - TOKEN
from dotenv import load_dotenv
import os

# Cargar las variables del archivo .env
load_dotenv()

APP_ID = os.getenv("APP_ID")
TOKEN = os.getenv("TOKEN")

console = Console()


# ------------------- UI RICH (RENDER) -------------------
def render_layout(engine):
    header = Table.grid(expand=True)
    header.add_column(justify="left", style="bold cyan")
    header.add_column(justify="center", style="bold yellow")
    header.add_column(justify="right", style="bold magenta")

    status_text = "ACTIVO" if not engine.risk.day_stopped else "PAUSADO"
    bal_txt = f"{engine.balance:.2f} USD" if engine.balance else "—"
    header.add_row(
        "📊 Bot Deriv (MTF+Scoring)", f"{status_text}", f"Balance: {bal_txt}"
    )
    header_panel = Panel(header, title="Estado General", padding=(1, 2))

    cols = [
        ("ID", "id"),
        ("Símbolo", "symbol"),
        ("Tipo", "contract_type"),
        ("Dur.", "duration"),
        ("Open", "open_time"),
        ("Elapsed", "_elapsed_temp"),
        ("Monto", "amount"),
        ("Profit", "profit"),
        ("Estado", "status"),
    ]
    table = Table(expand=True, show_edge=False)
    for title, _ in cols:
        table.add_column(title, justify="center")

    now_ts = time.time()
    for o in engine.trades.values():
        o["_elapsed_temp"] = (
            f"{int(now_ts - o['_open_ts'])}s"
            if o["status"] == "Abierta"
            else o.get("elapsed", "-")
        )
        row = []
        for _, key in cols:
            v = o.get(key, "-")
            if key == "profit" and isinstance(v, (float, int)):
                color = "green" if v > 0 else "red" if v < 0 else "white"
                row.append(f"[{color}]{v:.2f}[/{color}]")
            elif isinstance(v, (float, int)):
                row.append(f"{v:.2f}")
            else:
                row.append(str(v))
        table.add_row(*row)

    orders_panel = Panel(table, title="📋 Órdenes", padding=(1, 2))

    # Probabilidades + última acción
    from core.websocket_client import probabilities, ultima_accion

    prob_panel = Panel(
        f"Compra: {probabilities.get('buy',0):.2f}% | Venta: {probabilities.get('sell',0):.2f}%\n"
        f"Última: {ultima_accion or '—'}",
        title="Prob/Señales",
        padding=(1, 2),
    )

    layout = Layout()
    layout.split_column(
        Layout(header_panel, size=5), Layout(orders_panel), Layout(prob_panel, size=4)
    )
    return layout


# ------------------- MAIN / ARRANQUE -------------------
symbols = ["R_10", "R_25", "R_50", "R_75", "R_100"]
buffers = OHLCBuffers(maxlen=1000)
features = FeatureEngine(buffers)
risk = RiskManager()
engine = TradeEngine(risk)
strategy = Strategy()
deriv = DerivWS(APP_ID, TOKEN, symbols, engine, buffers, features, strategy, risk)


def start_ui_loop():
    with Live(render_layout(engine), console=console, refresh_per_second=2) as live:
        while True:
            try:
                live.update(render_layout(engine))
                time.sleep(0.5)
            except KeyboardInterrupt:
                break


def start_all():
    console.print("\n🚀 Iniciando Bot Deriv — MTF + Scoring + Riesgo Adaptativo")
    console.print(
        "   ✅ MTF (1m/5m/15m), Divergencias, S/R, Volumen sintético (ATR), Scoring\n"
    )
    deriv.connect()
    threading.Thread(target=start_ui_loop, daemon=True).start()


if __name__ == "__main__":
    start_all()
    # Mantener vivo el hilo principal
    while True:
        time.sleep(1)
