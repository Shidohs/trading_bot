#!/usr/bin/env python3
"""
Script para ejecutar tests automatizados del sistema de trading
"""
import unittest
import sys
from rich.console import Console

console = Console()


def run_all_tests():
    """Ejecutar todos los tests"""
    console.print("[bold blue]🧪 EJECUTANDO TESTS AUTOMATIZADOS[/bold blue]")
    console.print("[blue]====================================[/blue]")

    # Descubrir y ejecutar todos los tests
    loader = unittest.TestLoader()
    start_dir = "tests"
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Mostrar resumen
    console.print(f"\n[bold]📊 RESULTADOS DE TESTS:[/bold]")
    console.print(f"   Tests ejecutados: {result.testsRun}")
    console.print(f"   Fallos: {len(result.failures)}")
    console.print(f"   Errores: {len(result.errors)}")
    console.print(f"   Saltados: {len(result.skipped)}")

    if result.wasSuccessful():
        console.print("[bold green]✅ TODOS LOS TESTS PASARON[/bold green]")
        return True
    else:
        console.print("[bold red]❌ ALGUNOS TESTS FALLARON[/bold red]")

        # Mostrar detalles de fallos
        if result.failures:
            console.print("\n[red]FALLOS:[/red]")
            for test, traceback in result.failures:
                console.print(f"   {test}: {traceback.splitlines()[-1]}")

        # Mostrar detalles de errores
        if result.errors:
            console.print("\n[red]ERRORES:[/red]")
            for test, traceback in result.errors:
                console.print(f"   {test}: {traceback.splitlines()[-1]}")

        return False


def run_specific_test(test_name):
    """Ejecutar un test específico"""
    console.print(f"[blue]🧪 Ejecutando test: {test_name}[/blue]")

    try:
        # Importar y ejecutar el test específico
        if test_name == "strategy":
            from tests.test_strategy import TestStrategy

            suite = unittest.TestLoader().loadTestsFromTestCase(TestStrategy)
        elif test_name == "indicators":
            from tests.test_indicators import TestIndicators

            suite = unittest.TestLoader().loadTestsFromTestCase(TestIndicators)
        elif test_name == "backtester":
            from tests.test_backtester import TestBacktester

            suite = unittest.TestLoader().loadTestsFromTestCase(TestBacktester)
        else:
            console.print(f"[red]❌ Test '{test_name}' no encontrado[/red]")
            return False

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()

    except ImportError as e:
        console.print(f"[red]❌ Error importando test: {e}[/red]")
        return False


if __name__ == "__main__":
    console.print("[bold]🤖 SISTEMA DE TESTING DEL BOT DE TRADING[/bold]")
    console.print("=" * 50)

    if len(sys.argv) > 1:
        # Ejecutar test específico
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Ejecutar todos los tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
