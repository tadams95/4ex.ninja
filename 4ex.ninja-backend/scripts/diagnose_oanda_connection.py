#!/usr/bin/env python3
"""
OANDA Connection Diagnostic Script

This script tests the OANDA API connection and identifies issues
with data retrieval for Step 1.2.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import OANDA API
try:
    from api.oanda_api import OandaAPI
    from config.settings import API_KEY, ACCOUNT_ID

    print("✅ OANDA API imports successful")
    print(
        f"📋 API Key: {'*' * (len(API_KEY) - 4) + API_KEY[-4:] if API_KEY else 'NOT SET'}"
    )
    print(f"📋 Account ID: {ACCOUNT_ID if ACCOUNT_ID else 'NOT SET'}")
except ImportError as e:
    print(f"❌ Failed to import OANDA API: {e}")
    sys.exit(1)


def test_oanda_connection():
    """Test basic OANDA API connection."""
    print("\n🔍 Testing OANDA API Connection")
    print("=" * 50)

    try:
        # Initialize API
        api = OandaAPI()
        print("✅ OANDA API initialized")

        # Test account access
        print("📊 Testing account access...")
        account_details = api.get_account_details()

        if account_details:
            print(f"✅ Account access successful")
            print(f"   📋 Account ID: {account_details.get('id', 'Unknown')}")
            print(f"   💰 Balance: {account_details.get('balance', 'Unknown')}")
            print(f"   💱 Currency: {account_details.get('currency', 'Unknown')}")
            return True
        else:
            print("❌ Failed to get account details")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_instruments():
    """Test available instruments."""
    print("\n🔍 Testing Available Instruments")
    print("=" * 50)

    try:
        api = OandaAPI()
        instruments = api.get_instruments()

        if instruments:
            print(f"✅ Found {len(instruments)} available instruments")

            # Check for our target pairs
            target_pairs = [
                "EUR_USD",
                "GBP_USD",
                "USD_JPY",
                "AUD_USD",
                "USD_CAD",
                "USD_CHF",
            ]
            available_pairs = [inst.get("name", "") for inst in instruments]

            print(f"\n📈 Target pair availability:")
            for pair in target_pairs:
                if pair in available_pairs:
                    print(f"   ✅ {pair} - Available")
                else:
                    print(f"   ❌ {pair} - Not available")

            return True
        else:
            print("❌ No instruments found")
            return False

    except Exception as e:
        print(f"❌ Instruments test failed: {e}")
        return False


def test_current_pricing():
    """Test current pricing data."""
    print("\n🔍 Testing Current Pricing")
    print("=" * 50)

    try:
        api = OandaAPI()
        test_pairs = ["EUR_USD", "GBP_USD", "USD_JPY"]

        for pair in test_pairs:
            print(f"📊 Testing {pair}...")
            price = api.get_current_price(pair)

            if price:
                print(f"   ✅ Current price: {price}")
            else:
                print(f"   ❌ No price data")

        return True

    except Exception as e:
        print(f"❌ Pricing test failed: {e}")
        return False


def test_historical_data():
    """Test historical data retrieval with different date ranges."""
    print("\n🔍 Testing Historical Data Retrieval")
    print("=" * 50)

    try:
        api = OandaAPI()

        # Test different date ranges
        test_cases = [
            {
                "name": "Recent data (1 week)",
                "start": (datetime.now() - timedelta(days=7)).strftime(
                    "%Y-%m-%dT%H:%M:%S.000Z"
                ),
                "end": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "count": None,
            },
            {
                "name": "Recent data (1 month)",
                "start": (datetime.now() - timedelta(days=30)).strftime(
                    "%Y-%m-%dT%H:%M:%S.000Z"
                ),
                "end": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "count": None,
            },
            {
                "name": "Fixed count (50 candles)",
                "start": None,
                "end": None,
                "count": 50,
            },
        ]

        for test_case in test_cases:
            print(f"\n📊 {test_case['name']}:")

            # Test EUR_USD with Daily granularity
            candles = api.get_candles(
                instrument="EUR_USD",
                granularity="D",
                count=test_case["count"],
                start=test_case["start"],
                end=test_case["end"],
            )

            if candles and len(candles) > 0:
                print(f"   ✅ Retrieved {len(candles)} candles")
                # Show sample data
                first_candle = candles[0]
                if isinstance(first_candle, dict) and "mid" in first_candle:
                    print(
                        f"   📈 Sample: O:{first_candle['mid']['o']} H:{first_candle['mid']['h']} L:{first_candle['mid']['l']} C:{first_candle['mid']['c']}"
                    )
                elif isinstance(first_candle, dict):
                    print(f"   📈 Sample candle keys: {list(first_candle.keys())}")
            else:
                print(f"   ❌ No candles retrieved")

        return True

    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
        return False


def main():
    """Main diagnostic function."""
    print("🚀 OANDA API Diagnostic Tool")
    print("=" * 60)

    results = {
        "connection": test_oanda_connection(),
        "instruments": test_instruments(),
        "pricing": test_current_pricing(),
        "historical": test_historical_data(),
    }

    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.title()}: {status}")

    overall_success = all(results.values())

    if overall_success:
        print("\n🎉 All tests passed! OANDA API is working correctly.")
        print("💡 The issue may be with date ranges or specific timeframes.")
    else:
        print("\n⚠️ Some tests failed. Check the details above.")

    print("\n📋 Recommendations:")
    if not results["connection"]:
        print("   - Check API credentials in .env file")
        print("   - Verify account permissions")
    if not results["instruments"]:
        print("   - Check account access level")
        print("   - Verify instrument permissions")
    if not results["historical"]:
        print("   - Try shorter date ranges")
        print("   - Check granularity settings")
        print("   - Verify data availability for requested periods")

    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
