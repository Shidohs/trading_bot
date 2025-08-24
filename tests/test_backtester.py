import unittest
from core.backtester import Backtester


class TestBacktester(unittest.TestCase):

    def setUp(self):
        self.backtester = Backtester(initial_balance=10000.0)

    def test_simulate_trade(self):
        # Simulate a trade and check the results
        trade_result = self.backtester.simulate_trade(
            symbol="R_10",
            direction="CALL",
            stake=100,
            entry_price=1.0,
            exit_price=1.1,
            duration=2,
        )

        self.assertEqual(trade_result["symbol"], "R_10")
        self.assertEqual(trade_result["direction"], "CALL")
        self.assertGreater(trade_result["net_pnl"], 0)  # Expecting a profit

    def test_calculate_metrics(self):
        # Simulate multiple trades
        self.backtester.simulate_trade("R_10", "CALL", 100, 1.0, 1.1, 2)
        self.backtester.simulate_trade("R_25", "PUT", 100, 1.0, 0.9, 2)

        metrics = self.backtester.calculate_metrics()

        self.assertGreater(
            metrics["final_balance"], self.backtester.initial_balance
        )  # Expecting some profit
        self.assertIn("total_pnl", metrics)
        self.assertIn("win_rate_pct", metrics)
        self.assertIn("avg_win", metrics)
        self.assertIn("avg_loss", metrics)

    def test_export_results(self):
        # Simulate a trade and export results
        self.backtester.simulate_trade("R_10", "CALL", 100, 1.0, 1.1, 2)
        export_paths = self.backtester.export_results(output_dir="test_results")

        self.assertTrue(export_paths["trades_csv"].endswith(".csv"))
        self.assertTrue(export_paths["metrics_json"].endswith(".json"))
        self.assertTrue(export_paths["equity_csv"].endswith(".csv"))


if __name__ == "__main__":
    unittest.main()
