# validator.py
import os
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import numpy as np

console = Console()


def validate_environment():
    """Valida variables de entorno"""
    console.print("🔍 [cyan]Validando entorno...[/cyan]")

    if not os.path.exists(".env"):
        console.print("❌ Archivo .env no encontrado")
        return False

    from dotenv import load_dotenv

    load_dotenv()

    app_id = os.getenv("APP_ID")
    token = os.getenv("TOKEN")

    if not app_id:
        console.print("❌ APP_ID no configurado en .env")
        return False
    else:
        console.print(f"✅ APP_ID: {app_id}")

    if not token:
        console.print("❌ TOKEN no configurado en .env")
        return False
    else:
        console.print(f"✅ TOKEN: {token[:20]}...")

    return True


def validate_dependencies():
    """Valida dependencias"""
    console.print("🔍 [cyan]Validando dependencias...[/cyan]")

    required = ["websocket", "rich", "numpy", "pandas", "python_dotenv"]
    missing = []

    for module in required:
        try:
            if module == "python_dotenv":
                import dotenv
            else:
                __import__(module)
            console.print(f"✅ {module}")
        except ImportError:
            console.print(f"❌ {module}")
            missing.append(module)

    return len(missing) == 0


def validate_core_modules():
    """Valida módulos core"""
    console.print("🔍 [cyan]Validando módulos core...[/cyan]")

    modules = [
        "core.ohlc_buffers",
        "core.features",
        "core.strategy",
        "core.risk",
        "core.orders",
        "utils.indicators",
    ]

    for module in modules:
        try:
            __import__(module)
            console.print(f"✅ {module}")
        except ImportError as e:
            console.print(f"❌ {module}: {e}")
            return False

    return True


def test_indicators():
    """Prueba indicadores"""
    console.print("🔍 [cyan]Probando indicadores...[/cyan]")

    try:
        from utils.indicators import calc_rsi, calc_macd

        # Datos de prueba
        test_prices = [100 + np.sin(i / 10) * 5 for i in range(50)]

        rsi = calc_rsi(test_prices, 14)
        macd, signal, hist = calc_macd(test_prices, 12, 26, 9)

        if len(rsi) > 0 and len(macd) > 0:
            console.print("✅ Indicadores funcionando")
            return True
        else:
            console.print("❌ Indicadores no funcionan")
            return False

    except Exception as e:
        console.print(f"❌ Error probando indicadores: {e}")
        return False


def main():
    """Función principal de validación"""
    console.print("🔧 [bold cyan]VALIDADOR DEL SISTEMA[/bold cyan]\n")

    tests = [
        ("Entorno", validate_environment),
        ("Dependencias", validate_dependencies),
        ("Módulos Core", validate_core_modules),
        ("Indicadores", test_indicators),
    ]

    all_passed = True

    table = Table(title="Resultados de Validación")
    table.add_column("Componente", style="cyan")
    table.add_column("Estado", style="white")

    for name, test_func in tests:
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            if not result:
                all_passed = False
        except Exception as e:
            status = f"❌ ERROR: {e}"
            all_passed = False

        table.add_row(name, status)

    console.print(table)

    if all_passed:
        console.print("\n✅ [bold green]Sistema listo para ejecutar[/bold green]")
        console.print("Puedes ejecutar: python main.py")
    else:
        console.print(
            "\n❌ [bold red]Corrige los errores antes de continuar[/bold red]"
        )

    return all_passed


if __name__ == "__main__":
    main()
