"""
Market Data Tests - OANDA market data fetching and storage tests

Tests for market data fetching, storage, and pagination functionality.
"""

from src.models.market_data import MarketData
from datetime import datetime, timedelta, timezone
from pprint import pprint


def fetch_paginated(
    market_data, instrument, granularity, start_date, end_date, count_per_request=5000
):
    """
    Fetch market data in paginated chunks to handle large date ranges.

    Args:
        market_data: MarketData instance
        instrument: Trading instrument (e.g., "EUR_USD")
        granularity: Timeframe (e.g., "H1", "H4", "D")
        start_date: Start date for data fetch
        end_date: End date for data fetch
        count_per_request: Number of candles per request

    Returns:
        Total number of candles fetched
    """
    total_fetched = 0
    current_start = start_date.replace(tzinfo=timezone.utc)
    end_date = end_date.replace(tzinfo=timezone.utc)

    if granularity == "H1":
        delta = timedelta(hours=1)
    elif granularity == "H4":
        delta = timedelta(hours=4)
    else:
        delta = timedelta(days=1)

    while current_start < end_date:
        try:
            # For daily candles, don't send count parameter
            if granularity == "D":
                fetched = market_data.fetch_and_store_candles(
                    instrument=instrument,
                    granularity=granularity,
                    start_date=current_start,
                    end_date=end_date,
                )
            else:
                # For H1 and H4, use count-based pagination
                fetched = market_data.fetch_and_store_candles(
                    instrument=instrument,
                    granularity=granularity,
                    start_date=current_start,
                    count=count_per_request,
                )

            if fetched == 0:
                break

            total_fetched += fetched
            print(f"Fetched {fetched} {granularity} candles from {current_start}")

            current_start = current_start + (delta * fetched)

        except Exception as e:
            print(f"Error during fetch: {e}")
            # For errors, move forward by a smaller increment to avoid skipping too much data
            current_start = current_start + (delta * 100)

    return total_fetched


def test_single_fetch():
    """Test single market data fetch."""
    print("Testing single market data fetch...")

    try:
        market_data = MarketData()

        # Test fetching recent daily data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        fetched = market_data.fetch_and_store_candles(
            instrument="EUR_USD",
            granularity="D",
            start_date=start_date,
            end_date=end_date,
        )

        print(f"✓ Fetched {fetched} daily EUR_USD candles")
        return True

    except Exception as e:
        print(f"✗ Single fetch failed: {e}")
        return False


def test_paginated_fetch():
    """Test paginated market data fetch."""
    print("Testing paginated market data fetch...")

    try:
        market_data = MarketData()

        # Test fetching larger dataset with pagination
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        total_fetched = fetch_paginated(
            market_data, "EUR_USD", "H4", start_date, end_date, count_per_request=1000
        )

        print(f"✓ Fetched {total_fetched} H4 EUR_USD candles with pagination")
        return True

    except Exception as e:
        print(f"✗ Paginated fetch failed: {e}")
        return False


def test_multiple_instruments():
    """Test fetching data for multiple instruments."""
    print("Testing multiple instrument fetch...")

    instruments = ["EUR_USD", "GBP_USD", "USD_JPY"]
    results = {}

    try:
        market_data = MarketData()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        for instrument in instruments:
            try:
                fetched = market_data.fetch_and_store_candles(
                    instrument=instrument,
                    granularity="D",
                    start_date=start_date,
                    end_date=end_date,
                )
                results[instrument] = fetched
                print(f"✓ {instrument}: {fetched} candles")

            except Exception as e:
                print(f"✗ {instrument}: Failed - {e}")
                results[instrument] = 0

        total_success = sum(1 for count in results.values() if count > 0)
        print(
            f"✓ Successfully fetched data for {total_success}/{len(instruments)} instruments"
        )
        return total_success > 0

    except Exception as e:
        print(f"✗ Multiple instrument fetch failed: {e}")
        return False


def test_granularity_variations():
    """Test different granularities."""
    print("Testing different granularities...")

    granularities = ["D", "H4", "H1"]
    results = {}

    try:
        market_data = MarketData()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)  # Short range for testing

        for granularity in granularities:
            try:
                fetched = market_data.fetch_and_store_candles(
                    instrument="EUR_USD",
                    granularity=granularity,
                    start_date=start_date,
                    end_date=end_date,
                )
                results[granularity] = fetched
                print(f"✓ {granularity}: {fetched} candles")

            except Exception as e:
                print(f"✗ {granularity}: Failed - {e}")
                results[granularity] = 0

        total_success = sum(1 for count in results.values() if count > 0)
        print(
            f"✓ Successfully fetched {total_success}/{len(granularities)} granularities"
        )
        return total_success > 0

    except Exception as e:
        print(f"✗ Granularity test failed: {e}")
        return False


def main():
    """Run all market data tests."""
    print("Market Data Fetch Tests")
    print("=" * 40)

    tests = [
        ("Single Fetch", test_single_fetch),
        ("Paginated Fetch", test_paginated_fetch),
        ("Multiple Instruments", test_multiple_instruments),
        ("Granularity Variations", test_granularity_variations),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))

    # Print summary
    print("\n" + "=" * 40)
    print("Market Data Test Results")
    print("=" * 40)

    passed = 0
    failed = 0

    for test_name, success, error in results:
        if success:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            if error:
                print(f"   Error: {error}")
            failed += 1

    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All market data tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
