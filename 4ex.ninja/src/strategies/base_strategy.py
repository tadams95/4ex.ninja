class BaseStrategy:
    def __init__(self):
        pass

    def execute_trade(self, signal):
        """
        Execute a trade based on the provided signal.
        """
        pass

    def evaluate_signal(self, market_data):
        """
        Evaluate the market data to generate a trading signal.
        """
        pass