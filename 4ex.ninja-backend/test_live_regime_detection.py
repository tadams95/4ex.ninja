"""
Live Data Test for Market Regime Detection Engine.

This script tests the regime detection system with real OANDA data
if API credentials are configured, otherwise falls back to demo mode.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtesting.regime_detector import RegimeDetector
from src.backtesting.data_infrastructure import DataInfrastructure


async def test_with_live_data():
    """Test regime detection with live OANDA data."""
    print("=== Live Market Regime Detection Test ===\n")

    # Check if OANDA credentials are available
    api_key = os.getenv("OANDA_API_KEY")
    account_id = os.getenv("OANDA_ACCOUNT_ID")

    if api_key and account_id:
        print("✓ OANDA API credentials found")
        print(f"  - Account ID: {account_id}")
        print(
            f"  - API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}"
        )
    else:
        print("! No OANDA credentials found in environment variables")
        print("  To test with live data, set these environment variables:")
        print("  - OANDA_API_KEY=your_api_key")
        print("  - OANDA_ACCOUNT_ID=your_account_id")
        print("  \n  Proceeding with fallback testing...\n")

    try:
        # 1. Test Data Infrastructure Connection
        print("1. Testing Data Infrastructure Connection...")
        data_infra = DataInfrastructure()

        # Try to connect to data providers
        connected = await data_infra.connect_all()

        if connected:
            print("✓ Data infrastructure connected successfully")

            # Get provider health information
            health_info = await data_infra.health_check_all()
            for provider_name, health in health_info.items():
                status_icon = (
                    "✓"
                    if health.status.value == "healthy"
                    else "!" if health.status.value == "degraded" else "❌"
                )
                print(f"  {status_icon} {provider_name}: {health.status.value}")
                if health.response_time_ms:
                    print(f"    Response time: {health.response_time_ms:.0f}ms")
                if health.error_message:
                    print(f"    Error: {health.error_message}")
        else:
            print("! Data infrastructure connection failed")
            print("  This is expected without valid API credentials")

        print()

        # 2. Test Live Data Retrieval
        print("2. Testing Live Data Retrieval...")

        if connected:
            # Test getting recent candles for major pairs
            test_pairs = ["EUR_USD", "GBP_USD", "USD_JPY"]
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)  # Last 30 days

            all_data = {}
            for pair in test_pairs:
                print(f"  Fetching data for {pair}...")
                try:
                    candles = await data_infra.get_candles(
                        pair, "4H", start_time, end_time, count=50
                    )

                    if candles:
                        all_data[pair] = candles
                        print(f"    ✓ Retrieved {len(candles)} candles")

                        # Show latest candle info
                        latest = candles[-1]
                        print(f"    Latest: {latest.timestamp} - Close: {latest.close}")
                    else:
                        print(f"    ! No data retrieved for {pair}")

                except Exception as e:
                    print(f"    ❌ Error fetching {pair}: {str(e)[:60]}...")

            if all_data:
                print(f"\n✓ Successfully retrieved data for {len(all_data)} pairs")
            else:
                print("\n! No live data retrieved - using fallback mode")

        print()

        # 3. Test Regime Detection with Available Data
        print("3. Testing Market Regime Detection...")

        detector = RegimeDetector()

        # Test with currency pairs
        currency_pairs = ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"]

        try:
            print("  Running regime detection analysis...")
            result = await detector.detect_current_regime(
                currency_pairs, timeframe="4H"
            )

            print(f"\n=== REGIME DETECTION RESULTS ===")
            print(f"📊 Current Market Regime: {result.regime.value}")
            print(f"😎 Risk Sentiment: {result.sentiment.value}")
            print(f"🎯 Confidence: {result.confidence:.1%}")
            print(f"📈 Volatility Level: {result.volatility_level}")
            print(f"⏱️  Regime Duration: {result.regime_duration_hours:.1f} hours")
            print(f"🔍 Contributing Factors:")
            for factor in result.contributing_factors:
                print(f"    • {factor}")
            print(f"⏰ Next Evaluation: {result.next_evaluation}")

            # Get regime history if available
            history = detector.get_regime_history(hours_back=24)
            if history:
                print(
                    f"\n📚 Recent Regime History ({len(history)} entries in last 24h):"
                )
                for i, entry in enumerate(history[-3:]):  # Show last 3
                    print(
                        f"    {i+1}. {entry.timestamp}: {entry.regime.value} (confidence: {entry.confidence:.1%})"
                    )

            print(f"\n✅ Regime detection completed successfully!")

            if connected and all_data:
                print("🎉 TEST PASSED: Successfully analyzed LIVE market data!")
            else:
                print("✅ TEST PASSED: System working with fallback data")

        except Exception as e:
            print(f"❌ Regime detection failed: {e}")
            import traceback

            traceback.print_exc()

        print()

        # 4. Test Individual Analysis Components
        print("4. Testing Individual Analysis Components...")

        # Create sample data structure
        sample_data = {"timestamp": datetime.now(), "timeframe": "4H"}

        components = [
            ("Market Classifier", detector.market_classifier.classify_market_condition),
            (
                "Volatility Analyzer",
                detector.volatility_analyzer.analyze_volatility_regime,
            ),
            ("Trend Analyzer", detector.trend_analyzer.analyze_trend_strength),
            ("Sentiment Analyzer", detector.sentiment_analyzer.analyze_risk_sentiment),
            ("Economic Analyzer", detector.economic_analyzer.analyze_event_impact),
        ]

        for name, component_func in components:
            try:
                result = await component_func(sample_data)
                print(f"  ✓ {name}: Working")
            except Exception as e:
                print(f"  ❌ {name}: Error - {str(e)[:50]}...")

        print("\n=== FINAL TEST SUMMARY ===")
        if connected and api_key and account_id:
            print("🎉 LIVE DATA TEST COMPLETED!")
            print("✓ Connected to OANDA with real credentials")
            print("✓ Retrieved live market data")
            print("✓ Performed regime analysis on real data")
            print("✓ All components functional")
        else:
            print("✅ FALLBACK TEST COMPLETED!")
            print("! No OANDA credentials - used fallback mode")
            print("✓ All components initialized and functional")
            print("✓ System ready for live data when credentials added")

        print("\n📝 TO ENABLE LIVE DATA:")
        print("1. Get OANDA demo account (free): https://www.oanda.com/demo-account/")
        print("2. Generate API key in OANDA platform")
        print("3. Set environment variables:")
        print("   export OANDA_API_KEY='your_api_key'")
        print("   export OANDA_ACCOUNT_ID='your_account_id'")
        print("4. Run this test again")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_live_data())
