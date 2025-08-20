#!/usr/bin/env python3
"""
Debug script to examine timestamp formats between OANDA data and backtest system
"""

import asyncio
from datetime import datetime, timezone, timedelta
from services.data_service import DataService


async def debug_timestamps():
    """Debug timestamp formats to identify timezone mismatch."""

    print("🔍 Debugging Timestamp Formats")
    print("=" * 50)

    # Initialize data service
    data_service = DataService()

    # Test 1: Fetch a small amount of real OANDA data
    print("📡 Fetching 10 real OANDA candles...")
    try:
        real_data = await data_service.get_historical_data("EUR_USD", "H4", 10)

        if real_data:
            print(f"✅ Fetched {len(real_data)} real candles")
            print("\n📊 Sample OANDA timestamp formats:")
            for i, candle in enumerate(real_data[:3]):
                print(f"  Candle {i+1}:")
                print(f"    Timestamp: {candle.timestamp}")
                print(f"    Type: {type(candle.timestamp)}")
                print(f"    Timezone info: {candle.timestamp.tzinfo}")
                print(f"    ISO format: {candle.timestamp.isoformat()}")
        else:
            print("❌ No real data returned")

    except Exception as e:
        print(f"❌ Real data fetch failed: {e}")

    print("\n" + "=" * 50)

    # Test 2: Check current datetime formats used in backtest
    print("🕐 Current backtest datetime formats:")

    naive_now = datetime.now()
    aware_now = datetime.now(timezone.utc)

    print(f"  Naive datetime.now(): {naive_now}")
    print(f"  Type: {type(naive_now)}")
    print(f"  Timezone info: {naive_now.tzinfo}")

    print(f"\n  Aware datetime.now(timezone.utc): {aware_now}")
    print(f"  Type: {type(aware_now)}")
    print(f"  Timezone info: {aware_now.tzinfo}")

    # Test 3: Try subtraction to see what fails
    print("\n" + "=" * 50)
    print("🧪 Testing datetime subtraction scenarios:")

    try:
        # This should work (both aware)
        result1 = aware_now - aware_now
        print(f"✅ aware - aware = {result1}")
    except Exception as e:
        print(f"❌ aware - aware failed: {e}")

    try:
        # This should work (both naive)
        result2 = naive_now - naive_now
        print(f"✅ naive - naive = {result2}")
    except Exception as e:
        print(f"❌ naive - naive failed: {e}")

    try:
        # This should fail (mixed)
        result3 = aware_now - naive_now
        print(f"✅ aware - naive = {result3}")
    except Exception as e:
        print(f"❌ aware - naive failed: {e}")

    try:
        # This should fail (mixed)
        result4 = naive_now - aware_now
        print(f"✅ naive - aware = {result4}")
    except Exception as e:
        print(f"❌ naive - aware failed: {e}")

    # Test 4: If we have real data, test mixing it with backtest dates
    if "real_data" in locals() and real_data:
        print("\n" + "=" * 50)
        print("🔄 Testing mixed timestamp operations:")

        oanda_timestamp = real_data[0].timestamp
        backtest_start = datetime.now(timezone.utc) - timedelta(days=5 * 365)
        backtest_end = datetime.now(timezone.utc)

        print(
            f"  OANDA timestamp: {oanda_timestamp} (tzinfo: {oanda_timestamp.tzinfo})"
        )
        print(f"  Backtest start: {backtest_start} (tzinfo: {backtest_start.tzinfo})")
        print(f"  Backtest end: {backtest_end} (tzinfo: {backtest_end.tzinfo})")

        try:
            # Test if we can compare/subtract OANDA timestamp with backtest dates
            if oanda_timestamp > backtest_start:
                print("✅ oanda_timestamp > backtest_start comparison works")

            diff = backtest_end - oanda_timestamp
            print(f"✅ backtest_end - oanda_timestamp = {diff}")

        except Exception as e:
            print(f"❌ Mixed timestamp operation failed: {e}")

    print("\n" + "=" * 50)
    print("🎯 Summary: Look for timezone mismatches above!")


if __name__ == "__main__":
    asyncio.run(debug_timestamps())
