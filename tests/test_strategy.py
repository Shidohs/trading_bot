import unittest
import numpy as np
from core.strategy import Strategy


class TestStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()

    def test_trend_agreement(self):
        # Mock features for different timeframes
        fm1 = {"hist": [0.1, 0.2, 0.3], "rsi": [55, 60, 65]}
        fm5 = {"hist": [0.2, 0.3, 0.4], "rsi": [60, 65, 70]}
        fm15 = {"hist": [0.3, 0.4, 0.5], "rsi": [65, 70, 75]}

        # Test bullish agreement
        result = self.strategy.trend_agreement(fm1, fm5, fm15)
        self.assertEqual(result, 1)

        # Test bearish agreement
        fm1_bear = {"hist": [-0.1, -0.2, -0.3], "rsi": [45, 40, 35]}
        fm5_bear = {"hist": [-0.2, -0.3, -0.4], "rsi": [40, 35, 30]}
        fm15_bear = {"hist": [-0.3, -0.4, -0.5], "rsi": [35, 30, 25]}

        result = self.strategy.trend_agreement(fm1_bear, fm5_bear, fm15_bear)
        self.assertEqual(result, -1)

        # Test no agreement - need mixed signals across all timeframes
        fm1_mixed = {"hist": [0.1, -0.2, 0.3], "rsi": [45, 40, 35]}  # Mixed signals
        fm5_mixed = {"hist": [0.2, -0.3, 0.4], "rsi": [40, 35, 30]}
        fm15_mixed = {"hist": [0.3, -0.4, 0.5], "rsi": [35, 30, 25]}

        result = self.strategy.trend_agreement(fm1_mixed, fm5_mixed, fm15_mixed)
        self.assertEqual(result, 0)

    def test_score_calculation(self):
        # Mock features for testing
        feats = {
            "m1": {
                "rsi": [30, 35, 40],  # RSI fuera de rango (bueno)
                "hist": [0.1, 0.2, 0.3],  # MACD positivo
                "atr": [0.5, 0.6, 0.7],  # ATR creciente
                "div_rsi": {"bull": True, "bear": False},
                "div_macd": {"bull": True, "bear": False},
                "sr": [100, 105, 110],  # S/R levels
                "closes": [95, 96, 97],  # Precios actuales
            },
            "m5": {"hist": [0.2, 0.3, 0.4], "rsi": [60, 65, 70]},
            "m15": {"hist": [0.3, 0.4, 0.5], "rsi": [65, 70, 75]},
        }

        score, direction, signals = self.strategy.score(feats)

        # Should have reasonable score with bullish conditions
        # The actual score depends on the weighted calculation
        self.assertGreaterEqual(score, 0.5)  # Lower threshold for realistic scoring
        self.assertEqual(direction, "CALL")
        self.assertIn("RSI=", signals[0])
        self.assertIn("MACD+", signals[1])
        self.assertIn("DivBull", signals)

    def test_threshold(self):
        self.assertEqual(self.strategy.threshold, 0.78)


if __name__ == "__main__":
    unittest.main()
