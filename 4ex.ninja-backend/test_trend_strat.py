from enum import Enum
from datetime import datetime, timezone, timedelta
from src.strategies.trend_follow_strat import TrendFollowingStrategy
import pandas as pd

from src.strategies.base_strategy import SignalType

# Don't need to test this, just a demo


def test_strategy():
    # Initialize strategy
    strategy = TrendFollowingStrategy("EUR_USD")

    # Prepare data for last 6 months with explicit timezone
    end_date = pd.Timestamp.now(tz="UTC")
    start_date = end_date - pd.Timedelta(days=180)

    strategy.prepare_data(start_date.to_pydatetime(), end_date.to_pydatetime())

    h1_timestamps = strategy.data["H1"].index

    print("\nAnalyzing signals across all H1 candles...")
    buy_signals = 0
    sell_signals = 0

    for timestamp in h1_timestamps[-5000:]:  # Analyze more candles
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")

        signal = strategy.generate_signal(timestamp)

        # Compare using SignalType enum directly
        if signal.type == SignalType.BUY:
            buy_signals += 1
            print(f"\n🟢 BUY Signal at {timestamp}:")
            print(f"Entry: {signal.price:.5f}")
            print(f"Stop Loss: {signal.stop_loss:.5f}")
            print(f"Take Profit: {signal.take_profit:.5f}")
            print("-" * 50)

        elif signal.type == SignalType.SELL:
            sell_signals += 1
            print(f"\n🔴 SELL Signal at {timestamp}:")
            print(f"Entry: {signal.price:.5f}")
            print(f"Stop Loss: {signal.stop_loss:.5f}")
            print(f"Take Profit: {signal.take_profit:.5f}")
            print("-" * 50)

    # Print summary
    print("\nStrategy Analysis Summary:")
    print(f"Period: {start_date} to {end_date}")
    print(f"Total H1 candles analyzed: {len(h1_timestamps)}")
    print(f"Total BUY signals: {buy_signals}")
    print(f"Total SELL signals: {sell_signals}")
    print(f"Total signals generated: {buy_signals + sell_signals}")


if __name__ == "__main__":
    test_strategy()
