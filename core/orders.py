import time


class TradeEngine:
    def __init__(self, risk):
        self.risk = risk
        self.balance = 0.0
        self.initial_balance = 0.0
        self.trades = {}
        self.trades_today = []
        self.open_contracts = {}
        self.not_offered_cache = {}
        self.max_open_per_symbol = 2
        self.max_open_total = 8

    def set_balance(self, bal):
        if self.initial_balance == 0.0:
            self.initial_balance = bal
            self.risk.set_day_start(bal)
        self.balance = bal

    def can_open(self, symbol):
        if (
            len([t for t in self.trades.values() if t["status"] == "Abierta"])
            >= self.max_open_total
        ):
            return False
        if (
            len(
                [
                    t
                    for t in self.trades.values()
                    if t["status"] == "Abierta" and t["symbol"] == symbol
                ]
            )
            >= self.max_open_per_symbol
        ):
            return False
        return True

    def open_trade(self, symbol, direction, stake, duration=2, duration_unit="m"):
        trade_id = f"T{int(time.time()*1000)}"
        self.trades[trade_id] = {
            "id": trade_id,
            "symbol": symbol,
            "contract_type": direction,
            "amount": stake,
            "open_time": time.strftime("%H:%M:%S"),
            "_open_ts": time.time(),
            "status": "Abierta",
            "profit": 0.0,
            "duration": duration,
            "duration_unit": duration_unit,
        }
        return trade_id

    def finalize_trade(self, trade_id, profit):
        if trade_id not in self.trades:
            return
        t = self.trades[trade_id]
        t["status"] = "Cerrada"
        t["profit"] = profit
        t["elapsed"] = f"{int(time.time() - t['_open_ts'])}s"
        self.balance += profit
        self.trades_today.append(profit)
        self.risk.on_trade_result(profit)
