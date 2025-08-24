import time


class RiskManager:
    def __init__(self):
        self.base_amount = 10.0
        self.risk_per_trade = 0.003  # 0.3% del balance
        self.stake_max_pct = 0.01  # 1% del balance
        self.stake_min = 0.35
        self.win_streak_trigger = 2
        self.win_streak_boost = 1.25
        self.loss_streak = 0
        self.win_streak = 0
        self.pause_until = 0
        self.loss_streak_pause = 24  # si alcanza esta racha, pausamos
        self.loss_pause_seconds = 120
        self.daily_tp_pct = 0.10
        self.daily_dd_pct = 0.12

        self.day_start_balance = 0.0
        self.day_stopped = False

    def compute_stake(self, balance):
        stake = max(balance * self.risk_per_trade, self.base_amount)
        stake = min(stake, balance * self.stake_max_pct)
        if self.win_streak >= self.win_streak_trigger:
            stake *= self.win_streak_boost
        if self.loss_streak >= 1:
            stake *= 0.75
        return max(self.stake_min, round(stake, 2))

    def on_trade_result(self, profit):
        if profit > 0:
            self.win_streak += 1
            self.loss_streak = 0
        elif profit < 0:
            self.loss_streak += 1
            self.win_streak = 0

        if self.loss_streak >= self.loss_streak_pause:
            self.pause_until = time.time() + self.loss_pause_seconds
            self.loss_streak = 0

    def can_trade_now(self, balance):
        if time.time() < self.pause_until:
            return False
        return balance >= self.stake_min and not self.day_stopped

    def set_day_start(self, balance):
        self.day_start_balance = balance
        self.day_stopped = False

    def check_daily_limits(self, current_balance):
        pnl = current_balance - self.day_start_balance
        if pnl >= self.day_start_balance * self.daily_tp_pct and not self.day_stopped:
            self.day_stopped = True
            return "tp"
        if pnl <= -self.day_start_balance * self.daily_dd_pct and not self.day_stopped:
            self.day_stopped = True
            return "dd"
        return None
