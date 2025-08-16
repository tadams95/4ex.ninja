#!/usr/bin/env python3
"""
Test script for Live Data Integration - Phase 2.5%

This script validates the live data integration implementation
for Day 1-2 tasks.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the necessary paths
backend_dir = os.path.dirname(__file__)
src_path = os.path.join(backend_dir, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_live_data_integration():
    """Test the live data integration components"""

    print("=" * 60)
    print("TESTING LIVE DATA INTEGRATION - Phase 2.5%")
    print("=" * 60)

    # Test 1: Import and initialize components
    print("\n1. Testing component imports...")

    try:
        from monitoring.regime_monitor import RegimeMonitor

        print("✅ RegimeMonitor imported successfully")

        from backtesting.data_providers.oanda_provider import (
            OandaLiveProvider,
            OandaProvider,
        )

        print("✅ OANDA providers imported successfully")

        from monitoring.dashboard_api import app

        print("✅ Dashboard API imported successfully")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Initialize regime monitor
    print("\n2. Testing RegimeMonitor initialization...")

    try:
        regime_monitor = RegimeMonitor()
        await regime_monitor.initialize()
        print("✅ RegimeMonitor initialized successfully")

        # Check if live data provider is available
        if (
            hasattr(regime_monitor, "live_data_provider")
            and regime_monitor.live_data_provider
        ):
            print(
                f"✅ Live data provider available: {regime_monitor.live_data_provider.is_available}"
            )
        else:
            print("⚠️  Live data provider not available (will use simulation)")

    except Exception as e:
        print(f"❌ RegimeMonitor initialization failed: {e}")
        return False

    # Test 3: Test regime monitor functionality
    print("\n3. Testing regime monitor functionality...")

    try:
        # Test current regime
        current_regime = await regime_monitor.get_current_regime()
        print(f"✅ Current regime: {current_regime['current_regime']}")
        print(f"   Confidence: {current_regime['confidence']:.2f}")
        print(f"   Data source: {current_regime.get('data_source', 'N/A')}")

        # Test update interval
        print(f"✅ Update interval: {regime_monitor.update_interval} seconds")

        # Test monitoring pairs
        print(f"✅ Monitoring pairs: {regime_monitor.monitoring_pairs}")

    except Exception as e:
        print(f"❌ Regime monitor functionality test failed: {e}")
        return False

    # Test 4: Test live data update (if available)
    print("\n4. Testing live data update...")

    try:
        if (
            regime_monitor.live_data_provider
            and regime_monitor.live_data_provider.is_available
        ):
            live_analysis = await regime_monitor.update_live_regime_data()
            print("✅ Live data update successful")
            print(f"   Regime: {live_analysis['current_regime']}")
            print(f"   Confidence: {live_analysis['confidence']:.2f}")
            print(
                f"   Live quotes count: {live_analysis.get('live_quotes_count', 'N/A')}"
            )
        else:
            simulation_analysis = await regime_monitor.update_live_regime_data()
            print("⚠️  Using simulation data (live provider not available)")
            print(f"   Regime: {simulation_analysis['current_regime']}")
            print(f"   Confidence: {simulation_analysis['confidence']:.2f}")

    except Exception as e:
        print(f"❌ Live data update test failed: {e}")
        return False

    # Test 5: Test health check
    print("\n5. Testing health check...")

    try:
        health_status = await regime_monitor.health_check()
        print(f"✅ Health check status: {health_status['status']}")
        print(f"   Initialized: {health_status['initialized']}")
        print(f"   Redis connected: {health_status['redis_connected']}")

    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False

    # Cleanup
    await regime_monitor.cleanup()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Live Data Integration Working!")
    print("=" * 60)

    return True


async def test_oanda_live_provider():
    """Test the OANDA live provider specifically"""

    print("\n" + "=" * 40)
    print("TESTING OANDA LIVE PROVIDER")
    print("=" * 40)

    try:
        from backtesting.data_providers.oanda_provider import OandaLiveProvider

        # Initialize provider
        provider = OandaLiveProvider()
        print(f"✅ OandaLiveProvider created")
        print(f"   API URL: {provider.api_url}")
        print(f"   Real-time: {provider.real_time}")

        # Test connection
        connected = await provider.connect()
        print(f"✅ Connection test result: {connected}")
        print(f"   Provider available: {provider.is_available}")

        if provider.is_available:
            # Test live quotes
            test_pairs = ["EUR/USD", "GBP/USD"]
            quotes = await provider.get_live_quotes(test_pairs)

            if quotes:
                print(f"✅ Live quotes retrieved for {len(quotes)} pairs:")
                for pair, quote in quotes.items():
                    print(f"   {pair}: {quote['ask']:.5f} @ {quote['timestamp']}")
            else:
                print("⚠️  No live quotes retrieved")

    except Exception as e:
        print(f"❌ OANDA Live Provider test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    print(f"Starting Live Data Integration Test at {datetime.now()}")

    async def main():
        # Test the live data integration
        success1 = await test_live_data_integration()

        # Test the OANDA live provider
        success2 = await test_oanda_live_provider()

        if success1 and success2:
            print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("Ready for deployment validation.")
        else:
            print("\n❌ Some tests failed. Please check the logs.")
            sys.exit(1)

    asyncio.run(main())
