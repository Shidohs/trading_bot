import numpy as np


def calcular_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    ganancias = deltas[deltas > 0].sum() / period
    perdidas = -deltas[deltas < 0].sum() / period
    if perdidas == 0:
        return 100
    rs = ganancias / perdidas
    return 100 - (100 / (1 + rs))


def ema(arr, n):
    if len(arr) == 0:
        return []
    k = 2.0 / (n + 1.0)
    out = [float(arr[0])]
    for x in arr[1:]:
        out.append(out[-1] * (1 - k) + float(x) * k)
    return out


def sma(arr, n):
    n = max(1, int(n))
    if len(arr) < n:
        return [np.mean(arr)] * len(arr) if arr else []
    res = []
    for i in range(len(arr)):
        start = max(0, i - n + 1)
        res.append(float(np.mean(arr[start : i + 1])))
    return res


def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return []
    deltas = np.diff(closes).astype(float)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    rsis = []
    for i in range(period, len(closes)):
        g = gains[i - period : i].mean()
        l = losses[i - period : i].mean()
        if l == 0:
            rs = np.inf
            rsi = 100.0
        else:
            rs = g / l
            rsi = 100 - (100 / (1 + rs))
        rsis.append(float(rsi))
    # Alinear longitud con closes
    pad = [50.0] * (len(closes) - len(rsis))
    return pad + rsis


def calc_macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        zeros = [0.0] * len(closes)
        return zeros, zeros, zeros
    e_fast = ema(closes, fast)
    e_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(e_fast, e_slow)]
    signal_line = ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist


def calc_atr(ohlc, period=14):
    # ohlc: lista de dicts {open, high, low, close, epoch}
    if len(ohlc) < period + 1:
        return [0.0] * len(ohlc)
    trs = [0.0]
    for i in range(1, len(ohlc)):
        h = float(ohlc[i]["high"])
        l = float(ohlc[i]["low"])
        pc = float(ohlc[i - 1]["close"])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    # media móvil simple de TR
    atr_series = sma(trs, period)
    return atr_series


def detect_divergence(closes, osc, lookback=20):
    """
    Detección simple de divergencias (precio vs oscilador).
    - Bullish: precio hace mínimos más bajos, oscilador mínimos más altos.
    - Bearish: precio hace máximos más altos, oscilador máximos más bajos.
    Retorna: {"bull": bool, "bear": bool}
    """
    if len(closes) < lookback + 5 or len(osc) != len(closes):
        return {"bull": False, "bear": False}
    c = closes[-lookback:]
    o = osc[-lookback:]

    # mínimos locales aproximados
    min_idx_price = np.argmin(c)
    min_idx_osc = np.argmin(o)
    # segundos mínimos: usar ventana reducida sin el mínimo principal
    c_wo = np.array(c, dtype=float)
    o_wo = np.array(o, dtype=float)
    c_wo[min_idx_price] = np.inf
    o_wo[min_idx_osc] = np.inf
    min2_idx_price = int(np.argmin(c_wo))
    min2_idx_osc = int(np.argmin(o_wo))

    bull = False
    if c[min2_idx_price] > c[min_idx_price] and o[min2_idx_osc] < o[min_idx_osc]:
        # precio hace low más bajo, oscilador hace low más alto (condición inversa a comparar pares)
        bull = True

    # máximos locales aproximados
    max_idx_price = np.argmax(c)
    max_idx_osc = np.argmax(o)
    c_wo2 = np.array(c, dtype=float)
    o_wo2 = np.array(o, dtype=float)
    c_wo2[max_idx_price] = -np.inf
    o_wo2[max_idx_osc] = -np.inf
    max2_idx_price = int(np.argmax(c_wo2))
    max2_idx_osc = int(np.argmax(o_wo2))

    bear = False
    if c[max2_idx_price] < c[max_idx_price] and o[max2_idx_osc] > o[max_idx_osc]:
        # precio hace high más alto, oscilador hace high más bajo (condición inversa a comparar pares)
        bear = True

    return {"bull": bull, "bear": bear}


def dynamic_sr_levels(closes, window=120, min_hits=3, tolerance=0.0005):
    """
    S/R dinámicos via clustering simple de precios.
    Retorna lista de niveles (float).
    """
    if len(closes) < window:
        return []
    region = np.array(closes[-window:], dtype=float)
    levels = []
    region_sorted = np.sort(region)
    # agrupamos por cercanía
    cluster = [region_sorted[0]]
    for x in region_sorted[1:]:
        if abs(x - np.mean(cluster)) <= tolerance * np.mean(cluster):
            cluster.append(x)
        else:
            if len(cluster) >= min_hits:
                levels.append(float(np.mean(cluster)))
            cluster = [x]
    if len(cluster) >= min_hits:
        levels.append(float(np.mean(cluster)))
    return levels
