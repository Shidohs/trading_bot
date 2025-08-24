import numpy as np
from collections import defaultdict, deque


class CorrelationGuard:
    def __init__(self, maxlen=1000, correlation_threshold=0.8):
        self.maxlen = maxlen
        self.correlation_threshold = correlation_threshold
        self.price_history = defaultdict(lambda: deque(maxlen=maxlen))
        self.correlation_matrix = {}

    def update_price(self, symbol, price):
        self.price_history[symbol].append(price)

    def compute_correlations(self):
        symbols = list(self.price_history.keys())
        if len(symbols) < 2:
            return {}

        # Ensure all price series have the same length
        min_length = min(len(self.price_history[s]) for s in symbols)
        if min_length < 10:  # Minimum data points for correlation
            return {}

        # Create aligned price arrays
        aligned_prices = {}
        for symbol in symbols:
            prices = list(self.price_history[symbol])[-min_length:]
            aligned_prices[symbol] = prices

        # Compute correlation matrix
        correlation_matrix = {}
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i + 1 :]:
                if sym1 != sym2:
                    corr = np.corrcoef(aligned_prices[sym1], aligned_prices[sym2])[0, 1]
                    correlation_matrix[(sym1, sym2)] = corr

        self.correlation_matrix = correlation_matrix
        return correlation_matrix

    def can_open_trade(self, symbol, current_symbols):
        """Check if opening a trade in symbol would violate correlation constraints"""
        if not current_symbols:
            return True

        self.compute_correlations()

        for open_symbol in current_symbols:
            if open_symbol == symbol:
                continue

            # Check both orderings of the symbol pair
            corr1 = self.correlation_matrix.get((symbol, open_symbol))
            corr2 = self.correlation_matrix.get((open_symbol, symbol))
            corr = corr1 if corr1 is not None else corr2

            if corr is not None and abs(corr) > self.correlation_threshold:
                return False

        return True

    def get_highly_correlated_pairs(self):
        """Return pairs of symbols with high correlation"""
        highly_correlated = []
        for (sym1, sym2), corr in self.correlation_matrix.items():
            if abs(corr) > self.correlation_threshold:
                highly_correlated.append((sym1, sym2, corr))
        return highly_correlated
