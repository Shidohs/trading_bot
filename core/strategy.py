from utils.indicators import sma


class Strategy:
    def __init__(self):
        # pesos configurables
        self.weights = {
            "rsi": 0.30,
            "macd": 0.25,
            "atr": 0.15,
            "mtf": 0.20,
            "div": 0.07,
            "sr": 0.03,
        }
        self.threshold = 0.78  # 78%

    @staticmethod
    def trend_agreement(fm1, fm5, fm15):
        """
        Coherencia de tendencia básica por MACD/RSI:
        True si las 3 están alineadas bull o bear; False si mixtas.
        """

        def bias(feat):
            if not feat:
                return 0
            hist = feat["hist"][-1]
            rsi = feat["rsi"][-1]
            b = 0
            if hist > 0 and rsi >= 50:
                b = 1
            elif hist < 0 and rsi <= 50:
                b = -1
            return b

        b1, b5, b15 = bias(fm1), bias(fm5), bias(fm15)
        if b1 == b5 == b15 == 1:
            return 1
        if b1 == b5 == b15 == -1:
            return -1
        return 0

    def score(self, feats):
        fm1, fm5, fm15 = feats["m1"], feats["m5"], feats["m15"]
        if not fm1 or not fm5 or not fm15:
            return 0.0, None, []

        signals = []
        # RSI componente (m1 principal)
        rsi_val = fm1["rsi"][-1]
        rsi_score = 1.0 if rsi_val < 40 or rsi_val > 60 else 0.4
        signals.append(f"RSI={rsi_val:.1f}")

        # MACD hist (m1)
        hist = fm1["hist"][-1]
        macd_score = 1.0 if hist >= 0 else 0.0
        signals.append("MACD+" if hist >= 0 else "MACD-")

        # ATR vs su SMA como proxy de volatilidad viva
        atr_series = fm1["atr"]
        atr_now = atr_series[-1]
        atr_sma = sma(atr_series, 14)[-1] if atr_series else 0.0
        atr_score = 1.0 if atr_now > atr_sma and atr_sma > 0 else 0.0
        signals.append("ATR▲" if atr_score == 1.0 else "ATR▼")

        # MTF agreement
        mtf_bias = self.trend_agreement(fm1, fm5, fm15)
        mtf_score = 1.0 if mtf_bias != 0 else 0.0
        signals.append("MTF✓" if mtf_bias != 0 else "MTF×")

        # Divergencias (m1, rsi/macd)
        div_ok = (
            fm1["div_rsi"]["bull"]
            or fm1["div_macd"]["bull"]
            or fm1["div_rsi"]["bear"]
            or fm1["div_macd"]["bear"]
        )
        div_score = 1.0 if div_ok else 0.0
        if fm1["div_rsi"]["bull"] or fm1["div_macd"]["bull"]:
            signals.append("DivBull")
        elif fm1["div_rsi"]["bear"] or fm1["div_macd"]["bear"]:
            signals.append("DivBear")
        else:
            signals.append("Div-")

        # Proximidad a S/R (si el precio está muy cerca, bajar score por posible rebote)
        price = fm1["closes"][-1]
        sr_levels = fm1["sr"]
        sr_penalty = 0.0
        if sr_levels:
            nearest = min(sr_levels, key=lambda lv: abs(lv - price))
            if abs(nearest - price) / max(1e-9, price) < 0.0006:
                sr_penalty = 0.3
                signals.append("⚠SRnear")
            else:
                signals.append("SRok")
        sr_score = max(0.0, 1.0 - sr_penalty)

        # scoring ponderado
        w = self.weights
        raw = (
            w["rsi"] * rsi_score
            + w["macd"] * macd_score
            + w["atr"] * atr_score
            + w["mtf"] * mtf_score
            + w["div"] * div_score
            + w["sr"] * sr_score
        )

        # dirección sugerida por sesgo MTF y MACD
        direction = "CALL" if mtf_bias >= 0 and hist >= 0 else "PUT"
        return float(raw), direction, signals
