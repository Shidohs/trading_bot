from collections import deque, defaultdict


class OHLCBuffers:
    """
    Mantiene OHLC 1m en vivo y construye 5m y 15m por agregación.
    """

    def __init__(self, maxlen=1000):
        self.m1 = defaultdict(lambda: deque(maxlen=maxlen))  # symbol -> list[dict ohlc]
        self.m5 = defaultdict(lambda: deque(maxlen=maxlen))
        self.m15 = defaultdict(lambda: deque(maxlen=maxlen))

    def push_ohlc_1m(self, symbol, ohlc):
        # ohlc: {"open":..,"high":..,"low":..,"close":..,"epoch":..}
        self.m1[symbol].append(ohlc)
        self._rebuild_higher_tf(symbol)

    def _rebuild_higher_tf(self, symbol):
        def aggregate(src, minutes):
            arr = list(src)
            if not arr:
                return []
            out = []
            bucket = []
            last_bucket_start = None
            for c in arr:
                # agrupar por intervalos de 'minutes' minutos con base en epoch//60
                minute_index = int(c["epoch"] // 60)
                bucket_index = minute_index - (minute_index % minutes)
                if last_bucket_start is None:
                    last_bucket_start = bucket_index
                if bucket_index != last_bucket_start:
                    out.append(self._aggregate_bucket(bucket))
                    bucket = []
                    last_bucket_start = bucket_index
                bucket.append(c)
            if bucket:
                out.append(self._aggregate_bucket(bucket))
            return out

        m1 = self.m1[symbol]
        self.m5[symbol].clear()
        self.m15[symbol].clear()
        for k in aggregate(m1, 5):
            self.m5[symbol].append(k)
        for k in aggregate(m1, 15):
            self.m15[symbol].append(k)

    @staticmethod
    def _aggregate_bucket(bucket):
        if not bucket:
            return {}
        o = float(bucket[0]["open"])
        h = max(float(x["high"]) for x in bucket)
        l = min(float(x["low"]) for x in bucket)
        c = float(bucket[-1]["close"])
        epoch = int(bucket[-1]["epoch"])
        return {"open": o, "high": h, "low": l, "close": c, "epoch": epoch}
