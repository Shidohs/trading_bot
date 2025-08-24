import unittest
import numpy as np
from utils.indicators import (
    calc_rsi,
    calc_macd,
    calc_atr,
    detect_divergence,
    dynamic_sr_levels,
)


class TestIndicators(unittest.TestCase):

    def test_calc_rsi(self):
        # Test RSI calculation with known values - need at least period + 1 data points
        closes = list(range(100, 130))  # 30 data points
        rsi = calc_rsi(closes, period=14)

        self.assertEqual(len(rsi), len(closes))
        # RSI should be between 0 and 100
        self.assertTrue(all(0 <= x <= 100 for x in rsi if not np.isnan(x)))

    def test_calc_macd(self):
        # Test MACD calculation
        closes = list(range(100, 150))
        macd, signal, hist = calc_macd(closes)

        self.assertEqual(len(macd), len(closes))
        self.assertEqual(len(signal), len(closes))
        self.assertEqual(len(hist), len(closes))

    def test_calc_atr(self):
        # Test ATR calculation
        ohlc_data = [
            {"open": 100, "high": 105, "low": 98, "close": 102},
            {"open": 102, "high": 108, "low": 101, "close": 106},
            {"open": 106, "high": 110, "low": 104, "close": 108},
        ]

        atr = calc_atr(ohlc_data, period=2)
        self.assertEqual(len(atr), len(ohlc_data))
        self.assertTrue(all(x >= 0 for x in atr))

    def test_detect_divergence(self):
        # Test divergence detection - create a clear divergence pattern
        # Price making lower lows while oscillator makes higher lows (bullish divergence)
        closes = [
            100,
            95,
            90,
            85,
            80,
            75,
            70,
            65,
            60,
            55,
            50,
            45,
            40,
            35,
            30,
        ]  # Price consistently falling
        osc = [
            20,
            25,
            30,
            35,
            40,
            45,
            50,
            55,
            60,
            65,
            70,
            75,
            80,
            85,
            90,
        ]  # Oscillator consistently rising

        result = detect_divergence(closes, osc, lookback=15)
        # With this clear pattern, we should detect bullish divergence
        self.assertTrue(result["bull"])
        self.assertFalse(result["bear"])

        # Test bearish divergence - price making higher highs while oscillator makes lower highs
        closes_bear = [
            30,
            35,
            40,
            45,
            50,
            55,
            60,
            65,
            70,
            75,
            80,
            85,
            90,
            95,
            100,
        ]  # Price rising
        osc_bear = [
            90,
            85,
            80,
            75,
            70,
            65,
            60,
            55,
            50,
            45,
            40,
            35,
            30,
            25,
            20,
        ]  # Oscillator falling

        result_bear = detect_divergence(closes_bear, osc_bear, lookback=15)
        self.assertTrue(result_bear["bear"])
        self.assertFalse(result_bear["bull"])

    def test_dynamic_sr_levels(self):
        # Test support/resistance levels detection
        closes = [
            100,
            105,
            100,
            95,
            100,
            105,
            100,
            95,
            100,
        ]  # Oscilando alrededor de 100
        levels = dynamic_sr_levels(closes, window=5, min_hits=2)

        # Should detect 100 as a support/resistance level
        self.assertIn(100.0, levels)


if __name__ == "__main__":
    unittest.main()
