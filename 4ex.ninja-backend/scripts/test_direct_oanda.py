#!/usr/bin/env python3
"""
Simple OANDA Historical Data Test

Direct test of the OANDA API to isolate the issue.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.oanda_api import OandaAPI


def test_direct_oanda_call():
    """Test direct OANDA API call with different parameters."""
    print("🔍 Testing Direct OANDA API Calls")
    print("=" * 50)

    api = OandaAPI()

    # Test 1: Simple count-based request (most reliable)
    print("\n📊 Test 1: Count-based request")
    try:
        candles = api.get_candles(instrument="EUR_USD", granularity="D", count=10)
        print(f"   Result: {len(candles) if candles else 0} candles")
        if candles and len(candles) > 0:
            print(f"   Sample: {candles[0]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Recent time range
    print("\n📊 Test 2: Recent time range")
    try:
        start_time = datetime.now() - timedelta(days=30)
        end_time = datetime.now() - timedelta(days=1)  # Yesterday

        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        print(f"   Range: {start_str} to {end_str}")

        candles = api.get_candles(
            instrument="EUR_USD", granularity="D", start=start_str, end=end_str
        )
        print(f"   Result: {len(candles) if candles else 0} candles")
        if candles and len(candles) > 0:
            print(f"   Sample: {candles[0]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Different granularities
    print("\n📊 Test 3: Different granularities")
    granularities = ["H4", "D", "W"]

    for gran in granularities:
        try:
            candles = api.get_candles(instrument="EUR_USD", granularity=gran, count=5)
            print(f"   {gran}: {len(candles) if candles else 0} candles")
        except Exception as e:
            print(f"   {gran}: Error - {e}")

    # Test 4: Different instruments
    print("\n📊 Test 4: Different instruments")
    instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]

    for instrument in instruments:
        try:
            candles = api.get_candles(instrument=instrument, granularity="D", count=5)
            print(f"   {instrument}: {len(candles) if candles else 0} candles")
        except Exception as e:
            print(f"   {instrument}: Error - {e}")


if __name__ == "__main__":
    test_direct_oanda_call()
