from src.models.market_data import MarketData
from datetime import datetime, timedelta, timezone
from pprint import pprint


def test_market_data():
    market_data = MarketData()
    now = datetime.now(timezone.utc)

    # Test 1: Fetch and store H1 data
    print("\nFetching H1 candles...")
    start_date = now - timedelta(days=1)
    fetched_count = market_data.fetch_and_store_candles(
        instrument="EUR_USD", granularity="H1", start_date=start_date, end_date=now
    )
    print(f"Fetched and stored {fetched_count} H1 candles")

    h1_candles = market_data.get_candles(
        instrument="EUR_USD", granularity="H1", start_date=start_date, end_date=now
    )
    print(f"Retrieved {len(h1_candles)} H1 candles from database")

    # Test 2: Fetch and store M15 data
    print("\nFetching M15 candles...")
    fetched_count = market_data.fetch_and_store_candles(
        instrument="EUR_USD", granularity="M15", count=100
    )
    print(f"Fetched and stored {fetched_count} M15 candles")

    m15_candles = market_data.get_candles(
        instrument="EUR_USD", granularity="M15", count=100
    )
    print(f"Retrieved {len(m15_candles)} M15 candles from database")

    # Test 3: Fetch and store Daily data
    print("\nFetching Daily candles...")
    week_ago = now - timedelta(days=7)
    fetched_count = market_data.fetch_and_store_candles(
        instrument="EUR_USD", granularity="D", start_date=week_ago, end_date=now
    )
    print(f"Fetched and stored {fetched_count} Daily candles")

    daily_candles = market_data.get_candles(
        instrument="EUR_USD", granularity="D", start_date=week_ago, end_date=now
    )
    print(f"\nRetrieved {len(daily_candles)} Daily candles from database:")
    if daily_candles:
        pprint(daily_candles[0])  # Print first candle as example


if __name__ == "__main__":
    test_market_data()
