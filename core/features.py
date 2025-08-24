from utils.indicators import (
    calc_rsi,
    calc_macd,
    calc_atr,
    detect_divergence,
    dynamic_sr_levels,
)


class FeatureEngine:
    def __init__(self, buffers):
        self.buffers = buffers

    def compute_features(self, symbol):
        """
        Calcula features por TF: RSI, MACD, ATR, divergencias, S/R y volumen sintético (ATR).
        """
        f = {}

        def tf_features(ohlc_deque, tag):
            arr = list(ohlc_deque)
            if len(arr) < 35:
                return None
            closes = [float(x["close"]) for x in arr]
            highs = [float(x["high"]) for x in arr]
            lows = [float(x["low"]) for x in arr]

            rsi = calc_rsi(closes, 14)
            macd, sig, hist = calc_macd(closes, 12, 26, 9)
            atr = calc_atr(arr, 14)

            # volumen sintético (usamos ATR como proxy)
            vol_synth = atr

            # divergencias con RSI y MACD(hist)
            div_rsi = detect_divergence(closes, rsi, lookback=25)
            div_macd = detect_divergence(closes, hist, lookback=25)

            # S/R dinámicos
            sr = dynamic_sr_levels(closes, window=min(200, len(closes)))

            return {
                "closes": closes,
                "highs": highs,
                "lows": lows,
                "rsi": rsi,
                "macd": macd,
                "signal": sig,
                "hist": hist,
                "atr": atr,
                "vol_synth": vol_synth,
                "div_r极": div_rsi,
                "div_macd": div_macd,
                "sr": sr,
            }

        f["m1"] = tf_features(self.buffers.m1[symbol], "m1")
        f["m5"] = tf_features(self.buffers.m5[symbol], "m5")
        f["m15"] = tf_features(self.buffers.m15[symbol], "m15")
        return f
