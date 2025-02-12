from src.models.market_data import MarketData
from datetime import datetime, timedelta, timezone
from pprint import pprint


def fetch_paginated(
    market_data, instrument, granularity, start_date, end_date, count_per_request=5000
):
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
            if granularity in ("H1", "H4"):
                fetched = market_data.fetch_and_store_candles(
                    instrument=instrument,
                    granularity=granularity,
                    start_date=current_start,
                    count=count_per_request,
                )
            else:
                fetched = market_data.fetch_and_store_candles(
                    instrument=instrument,
                    granularity=granularity,
                    start_date=current_start,
                    end_date=end_date,
                    count=count_per_request,
                )

            if fetched == 0:
                break

            total_fetched += fetched
            print(f"Fetched {fetched} {granularity} candles from {current_start}")

            # Move forward by the number of candles fetched
            current_start = current_start + (delta * fetched)

        except Exception as e:
            print(f"Error during fetch: {e}")
            current_start = current_start + (delta * count_per_request)
            continue

    return total_fetched


def test_market_data():
    market_data = MarketData()
    now = datetime.now(timezone.utc)
    ten_years = timedelta(days=3650)

    # For H1 use pagination
    print("\nFetching H1 candles for 10 years with pagination...")
    start_date_h1 = (now - ten_years).replace(tzinfo=timezone.utc)
    total_h1 = fetch_paginated(
        market_data,
        instrument="EUR_USD",
        granularity="H1",
        start_date=start_date_h1,
        end_date=now,
    )
    print(f"Total H1 candles fetched: {total_h1}")

    # For H4 use pagination
    print("\nFetching H4 candles for 10 years with pagination...")
    start_date_h4 = (now - ten_years).replace(tzinfo=timezone.utc)
    total_h4 = fetch_paginated(
        market_data,
        instrument="EUR_USD",
        granularity="H4",
        start_date=start_date_h4,
        end_date=now,
    )
    print(f"Total H4 candles fetched: {total_h4}")

    # # Daily candles
    # print("\nFetching Daily candles for 10 years...")
    # start_date_d = (now - ten_years).replace(tzinfo=timezone.utc)
    # total_d = fetch_paginated(
    #     market_data,
    #     instrument="EUR_USD",
    #     granularity="D",
    #     start_date=start_date_d,
    #     end_date=now,
    # )
    # print(f"Total Daily candles fetched: {total_d}")


if __name__ == "__main__":
    test_market_data()
