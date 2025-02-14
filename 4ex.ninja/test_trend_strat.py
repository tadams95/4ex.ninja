from datetime import datetime, timezone, timedelta
from src.strategies.trend_follow_strat import TrendFollowingStrategy
import pandas as pd


def test_strategy():
    # Initialize strategy
    strategy = TrendFollowingStrategy("EUR_USD")

    # Prepare data for last 6 months with explicit timezone
    end_date = pd.Timestamp.now(tz="UTC")
    start_date = end_date - pd.Timedelta(days=180)

    # Prepare data and ensure datetime objects are timezone-aware
    strategy.prepare_data(start_date.to_pydatetime(), end_date.to_pydatetime())

    # Generate signal using timezone-aware datetime
    signal = strategy.generate_signal(end_date.to_pydatetime())
    print(f"Signal: {signal}")

    # Print some debug info
    print("\nDebug Information:")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")
    if "H1" in strategy.data:
        print(f"H1 Data Index Type: {strategy.data['H1'].index.dtype}")
        print(f"First H1 Timestamp: {strategy.data['H1'].index[0]}")
        print(f"Last H1 Timestamp: {strategy.data['H1'].index[-1]}")


if __name__ == "__main__":
    test_strategy()
