import time
import random
from rich.console import Console
from core.ohlc_buffers import OHLCBuffers
from core.features import FeatureEngine
from core.strategy import Strategy
from core.risk import RiskManager
from core.orders import TradeEngine
from config import DEBUG, SYMBOLS

console = Console()


def debug_strategy():
    """Modo debug para probar la estrategia sin WebSocket"""
    console.print("[yellow]🔧 MODO DEBUG ACTIVADO[/yellow]")
    console.print("[yellow]📊 Probando estrategia con datos simulados...[/yellow]")

    # Inicializar componentes
    buffers = OHLCBuffers(maxlen=1000)
    features = FeatureEngine(buffers)
    risk = RiskManager()
    engine = TradeEngine(risk)
    strategy = Strategy()

    # Simular datos OHLC
    console.print("[cyan]📈 Generando datos de prueba...[/cyan]")

    for symbol in SYMBOLS:
        # Generar datos OHLC de prueba
        for i in range(100):
            ohlc = {
                "open": 100 + random.uniform(-5, 5),
                "high": 100 + random.uniform(0, 10),
                "low": 100 + random.uniform(-10, 0),
                "close": 100 + random.uniform(-5, 5),
                "epoch": int(time.time()) - (100 - i) * 60,
            }
            buffers.push_ohlc_1m(symbol, ohlc)

        # Probar cálculo de features
        feats = features.compute_features(symbol)
        if feats["m1"] and feats["m5"] and feats["m15"]:
            score, direction, signals = strategy.score(feats)
            console.print(
                f"[green]{symbol}: Score={score:.2f}, Dirección={direction}[/green]"
            )
            console.print(f"   Señales: {', '.join(signals)}")

            # Simular trade si supera el threshold
            if score >= strategy.threshold:
                console.print(
                    f"[bold green]🎯 SEÑAL DE COMPRA DETECTADA EN {symbol}[/bold green]"
                )
                console.print(
                    f"   Score: {score:.2f} (Threshold: {strategy.threshold})"
                )
                console.print(f"   Dirección: {direction}")
                console.print(f"   Señales: {', '.join(signals)}")
        else:
            console.print(
                f"[yellow]{symbol}: Datos insuficientes para análisis[/yellow]"
            )

    console.print("[green]✅ Prueba de estrategia completada[/green]")


def debug_risk_management():
    """Probar gestión de riesgo"""
    console.print("\n[cyan]🧮 Probando gestión de riesgo...[/cyan]")

    risk = RiskManager()
    engine = TradeEngine(risk)

    # Simular diferentes balances
    test_balances = [5000, 10000, 20000, 50000]

    for balance in test_balances:
        engine.set_balance(balance)
        stake = risk.compute_stake(balance)
        console.print(f"Balance: ${balance:,.2f} -> Stake: ${stake:.2f}")

        # Probar límites diarios
        limit_check = risk.check_daily_limits(balance)
        if limit_check:
            console.print(f"   Límite alcanzado: {limit_check}")

    console.print("[green]✅ Prueba de gestión de riesgo completada[/green]")


def debug_backtesting():
    """Probar funcionalidad de backtesting"""
    console.print("\n[cyan]📊 Probando backtesting...[/cyan]")

    from core.backtester import Backtester

    backtester = Backtester()

    # Simular varios trades
    for i in range(10):
        direction = "CALL" if random.random() > 0.5 else "PUT"
        entry = 1.0
        exit = entry * (1 + random.uniform(-0.2, 0.2))

        backtester.simulate_trade(
            symbol=f"R_{random.randint(10, 100)}",
            direction=direction,
            stake=100,
            entry_price=entry,
            exit_price=exit,
            duration=random.randint(1, 5),
        )

    # Calcular métricas
    metrics = backtester.calculate_metrics()
    console.print("[bold]Métricas de Backtesting:[/bold]")
    for key, value in metrics.items():
        console.print(f"   {key}: {value}")

    console.print("[green]✅ Prueba de backtesting completada[/green]")


if __name__ == "__main__":
    if DEBUG:
        console.print("[bold blue]🚀 INICIANDO MODO DEBUG COMPLETO[/bold blue]")
        console.print("[blue]====================================[/blue]")

        debug_strategy()
        debug_risk_management()
        debug_backtesting()

        console.print(
            "\n[bold green]🎯 TODAS LAS PRUEBAS DEBUG COMPLETADAS[/bold green]"
        )
    else:
        console.print(
            "[yellow]⚠️  Modo debug desactivado. Cambia DEBUG=True en config.py[/yellow]"
        )
