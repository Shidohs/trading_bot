import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path


class Backtester:
    def __init__(self, initial_balance=10000.0, commission_rate=0.001, slippage=0.0005):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.trades = []
        self.equity_curve = []
        self.current_positions = {}

    def simulate_trade(
        self, symbol, direction, stake, entry_price, exit_price, duration
    ):
        """Simulate a trade with slippage and commissions"""
        # Apply slippage
        effective_entry = (
            entry_price * (1 + self.slippage)
            if direction == "CALL"
            else entry_price * (1 - self.slippage)
        )
        effective_exit = (
            exit_price * (1 - self.slippage)
            if direction == "CALL"
            else exit_price * (1 + self.slippage)
        )

        # Calculate PnL
        if direction == "CALL":
            pnl = stake * ((effective_exit - effective_entry) / effective_entry)
        else:  # PUT
            pnl = stake * ((effective_entry - effective_exit) / effective_entry)

        # Apply commissions
        commission = stake * self.commission_rate * 2  # Entry and exit
        net_pnl = pnl - commission

        trade_result = {
            "symbol": symbol,
            "direction": direction,
            "stake": stake,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "effective_entry": effective_entry,
            "effective_exit": effective_exit,
            "pnl": pnl,
            "commission": commission,
            "net_pnl": net_pnl,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        self.trades.append(trade_result)
        self.balance += net_pnl
        self.equity_curve.append(self.balance)

        return trade_result

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return {}

        net_pnls = [t["net_pnl"] for t in self.trades]
        total_pnl = sum(net_pnls)
        total_return = (self.balance - self.initial_balance) / self.initial_balance

        # Win rate
        winning_trades = [t for t in self.trades if t["net_pnl"] > 0]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0

        # Average win/loss
        avg_win = (
            np.mean([t["net_pnl"] for t in winning_trades]) if winning_trades else 0
        )
        losing_trades = [t for t in self.trades if t["net_pnl"] <= 0]
        avg_loss = (
            np.mean([t["net_pnl"] for t in losing_trades]) if losing_trades else 0
        )

        # Sharpe ratio (simplified)
        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
        sharpe = (
            np.mean(returns) / np.std(returns) * np.sqrt(252)
            if len(returns) > 1 and np.std(returns) > 0
            else 0
        )

        # Max drawdown
        peak = self.initial_balance
        max_drawdown = 0
        for value in self.equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        metrics = {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "total_pnl": total_pnl,
            "total_return_pct": total_return * 100,
            "win_rate_pct": win_rate * 100,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else float("inf"),
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_drawdown * 100,
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
        }

        return metrics

    def export_results(self, output_dir="backtest_results"):
        """Export backtest results to CSV and JSON"""
        os.makedirs(output_dir, exist_ok=True)

        # Export trades
        trades_df = pd.DataFrame(self.trades)
        trades_csv_path = os.path.join(output_dir, "trades.csv")
        trades_df.to_csv(trades_csv_path, index=False)

        # Export metrics
        metrics = self.calculate_metrics()
        metrics_json_path = os.path.join(output_dir, "metrics.json")
        with open(metrics_json_path, "w") as f:
            json.dump(metrics, f, indent=2)

        # Export equity curve
        equity_df = pd.DataFrame({"equity": self.equity_curve})
        equity_csv_path = os.path.join(output_dir, "equity_curve.csv")
        equity_df.to_csv(equity_csv_path, index=False)

        return {
            "trades_csv": trades_csv_path,
            "metrics_json": metrics_json_path,
            "equity_csv": equity_csv_path,
        }

    def walk_forward_test(self, data, train_ratio=0.7, retrain_interval=30):
        """Perform walk-forward validation"""
        results = []
        total_samples = len(data)
        train_size = int(total_samples * train_ratio)

        for i in range(train_size, total_samples, retrain_interval):
            train_data = data[:i]
            test_data = data[i : i + retrain_interval]

            # Train model on train_data (placeholder)
            # model.train(train_data)

            # Test on test_data
            test_results = self._test_on_data(test_data)
            results.append(test_results)

        return results

    def _test_on_data(self, data):
        """Test strategy on given data (placeholder implementation)"""
        # This should be implemented with actual strategy logic
        return {"test_results": "placeholder"}
