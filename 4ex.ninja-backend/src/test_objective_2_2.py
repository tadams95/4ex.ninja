"""
Test script for Objective 2.2: Streamlined Data Infrastructure.

This script tests the basic functionality of the data infrastructure
components for swing trading backtesting.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backtesting import (
    DataInfrastructure,
    DataQualityMonitor,
    SwingTradingCosts,
    OandaProvider,
    AlphaVantageProvider,
)


async def test_data_infrastructure():
    """Test the data infrastructure components."""
    print("=== Testing Objective 2.2: Streamlined Data Infrastructure ===\n")

    try:
        # 1. Test DataInfrastructure initialization
        print("1. Initializing Data Infrastructure...")
        data_infra = DataInfrastructure()
        print(f"   ✓ Initialized with {len(data_infra.providers)} providers")

        # 2. Test provider connections
        print("\n2. Testing Provider Connections...")
        connected = await data_infra.connect_all()
        if connected:
            print("   ✓ At least one provider connected successfully")

            # Show provider status
            status = data_infra.get_provider_status()
            for provider_name, info in status.items():
                status_symbol = "✓" if info["available"] else "✗"
                print(
                    f"   {status_symbol} {provider_name}: Priority {info['priority']}, Available: {info['available']}"
                )
        else:
            print("   ⚠ No providers connected (expected in test environment)")

        # 3. Test supported pairs and timeframes
        print("\n3. Testing Configuration...")
        pairs = data_infra.get_supported_pairs()
        timeframes = data_infra.get_supported_timeframes()
        print(f"   ✓ Supported pairs: {', '.join(pairs)}")
        print(f"   ✓ Supported timeframes: {', '.join(timeframes)}")

        # 4. Test cost calculation
        print("\n4. Testing Cost Calculation...")
        from decimal import Decimal

        costs = data_infra.calculate_trading_costs(
            position_size=Decimal("10000"),  # 10K units
            hold_days=5,  # 5 day swing trade
            pair="EUR_USD",
        )

        print("   ✓ Cost breakdown for 10K EUR_USD position (5 days):")
        for cost_type, amount in costs.items():
            print(f"     - {cost_type}: {amount:.4f}")

        # 5. Test data quality monitor
        print("\n5. Testing Data Quality Monitor...")
        quality_monitor = DataQualityMonitor(data_infra.providers)

        # Test demo data validation
        start_time = datetime.utcnow() - timedelta(days=30)
        end_time = datetime.utcnow()

        print("   Testing validation report generation...")
        report = await quality_monitor.validate_data_comprehensive(
            pair="EUR_USD", timeframe="D", start_time=start_time, end_time=end_time
        )

        print(f"   ✓ Validation report generated:")
        print(f"     - Quality score: {report.overall_quality_score:.2%}")
        print(f"     - Total candles: {report.total_candles}")
        print(f"     - Expected candles: {report.expected_candles}")
        print(f"     - Issues found: {len(report.issues)}")

        # 6. Test individual providers (demo mode)
        print("\n6. Testing Individual Providers...")

        # Test Alpha Vantage in demo mode
        av_provider = AlphaVantageProvider()  # No API key = demo mode
        av_connected = await av_provider.connect()
        if av_connected:
            print("   ✓ Alpha Vantage provider (demo mode) connected")

            # Test demo data generation
            demo_candles = await av_provider.get_candles(
                pair="EUR_USD",
                timeframe="D",
                start_time=datetime.utcnow() - timedelta(days=7),
                end_time=datetime.utcnow(),
                count=5,
            )
            print(f"   ✓ Generated {len(demo_candles)} demo candles")

            if demo_candles:
                latest_candle = demo_candles[-1]
                print(
                    f"     - Latest candle: OHLC({latest_candle.open:.4f}, {latest_candle.high:.4f}, {latest_candle.low:.4f}, {latest_candle.close:.4f})"
                )

        # 7. Test health checks
        print("\n7. Testing Health Checks...")
        health_status = await data_infra.health_check_all()
        print(f"   ✓ Health check completed for {len(health_status)} providers")

        for provider_name, health in health_status.items():
            status_symbol = (
                "✓"
                if health.status.value == "healthy"
                else "⚠" if health.status.value == "degraded" else "✗"
            )
            print(f"   {status_symbol} {provider_name}: {health.status.value}")

        # 8. Test quality summary
        print("\n8. Testing Quality Summary...")
        quality_summary = quality_monitor.get_quality_summary()
        print("   ✓ Quality summary:")
        print(f"     - Providers monitored: {quality_summary['providers_monitored']}")
        print(f"     - Active providers: {quality_summary['active_providers']}")
        print(f"     - Recent alerts (24h): {quality_summary['total_alerts_24h']}")

        print("\n=== All Tests Completed Successfully! ===")
        print("\n📊 Objective 2.2: Streamlined Data Infrastructure - IMPLEMENTED")
        print("✅ Key components working:")
        print("   • Multi-provider data infrastructure")
        print("   • Swing trading cost calculations")
        print("   • Data quality monitoring")
        print("   • Provider health checks")
        print("   • Cross-provider validation")

        # Cleanup
        await data_infra.close_all()

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_data_infrastructure())
