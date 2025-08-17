#!/usr/bin/env python3
"""
Test OANDA API with Pipeline Parameters

Test the exact same parameters that our data acquisition pipeline is using.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.oanda_api import OandaAPI


def test_pipeline_parameters():
    """Test with the exact parameters used by our pipeline."""
    print("🔍 Testing Pipeline Parameters")
    print("=" * 50)

    api = OandaAPI()

    # Test with the exact date range our pipeline uses
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)

    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"📅 Date Range: {start_str} to {end_str}")
    print(f"📏 Duration: {(end_date - start_date).days} days")

    # Test different timeframes with this large range
    timeframes = ["H4", "D", "W"]
    pairs = ["EUR_USD", "GBP_USD", "USD_JPY"]

    for timeframe in timeframes:
        print(f"\n📊 Testing timeframe: {timeframe}")

        for pair in pairs:
            try:
                print(f"   📈 {pair}...")
                candles = api.get_candles(
                    instrument=pair, granularity=timeframe, start=start_str, end=end_str
                )

                if candles:
                    print(f"      ✅ Success: {len(candles)} candles")
                else:
                    print(f"      ❌ No candles returned")

            except Exception as e:
                print(f"      ❌ Error: {e}")

    # Test smaller chunks
    print(f"\n📊 Testing smaller date chunks:")

    # Try 3-month chunks
    chunk_size = 90  # days
    current_date = start_date

    while current_date < end_date:
        chunk_end = min(current_date + timedelta(days=chunk_size), end_date)

        chunk_start_str = current_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        chunk_end_str = chunk_end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        print(
            f"   📅 Chunk: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}"
        )

        try:
            candles = api.get_candles(
                instrument="EUR_USD",
                granularity="D",
                start=chunk_start_str,
                end=chunk_end_str,
            )

            if candles:
                print(f"      ✅ Success: {len(candles)} candles")
                break  # Success with smaller chunk
            else:
                print(f"      ❌ No candles")

        except Exception as e:
            print(f"      ❌ Error: {e}")

        current_date = chunk_end

        # Only test first few chunks
        if current_date > start_date + timedelta(days=270):
            break


if __name__ == "__main__":
    test_pipeline_parameters()
