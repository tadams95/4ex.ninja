import unittest
from src.strategies.base_strategy import BaseStrategy

class TestBaseStrategy(unittest.TestCase):

    def setUp(self):
        self.strategy = BaseStrategy()

    def test_execute_trade(self):
        # Example test for execute_trade method
        result = self.strategy.execute_trade('buy', 100)
        self.assertTrue(result)

    def test_evaluate_signal(self):
        # Example test for evaluate_signal method
        signal = self.strategy.evaluate_signal({'price': 100, 'indicator': 'rsi'})
        self.assertIn(signal, ['buy', 'sell', 'hold'])

if __name__ == '__main__':
    unittest.main()