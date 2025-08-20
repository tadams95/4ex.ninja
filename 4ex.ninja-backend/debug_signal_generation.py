#!/usr/bin/env python3
"""
Quick debug script to test signal generation
"""

import asyncio
from datetime import datetime, timezone, timedelta
from services.multi_timeframe_strategy_service import MultiTimeframeStrategyService
from services.data_service import DataService


async def debug_signals():
    """Debug why no signals are being generated."""

    print("🔍 Debugging Signal Generation")
    print("=" * 50)

    strategy_service = MultiTimeframeStrategyService()
    data_service = DataService()

    # Test with a small amount of real data
    print("📡 Fetching small sample of EUR_USD data...")
    try:
        historical_data = await data_service.get_historical_data("EUR_USD", "H4", 500)

        if len(historical_data) < 100:
            print(f"❌ Insufficient data: {len(historical_data)} candles")
            return

        print(f"✅ Got {len(historical_data)} H4 candles")

        # Create timeframe data
        print("🔄 Creating timeframe data...")

        # Weekly data (42 * 4H = 1 week)
        weekly_data = []
        for i in range(0, len(historical_data), 42):
            week_slice = historical_data[i : i + 42]
            if len(week_slice) >= 10:
                weekly_data.append(week_slice[0])  # Simplified

        # Daily data (6 * 4H = 1 day)
        daily_data = []
        for i in range(0, len(historical_data), 6):
            day_slice = historical_data[i : i + 6]
            if len(day_slice) >= 3:
                daily_data.append(day_slice[0])  # Simplified

        print(
            f"📊 Created: Weekly={len(weekly_data)}, Daily={len(daily_data)}, 4H={len(historical_data)}"
        )

        # Test signal generation with sufficient data
        if (
            len(weekly_data) >= 50
            and len(daily_data) >= 50
            and len(historical_data) >= 200
        ):
            print("🎯 Testing signal generation...")

            try:
                signal = await strategy_service.generate_multi_timeframe_signal(
                    "EUR_USD", weekly_data, daily_data, historical_data
                )

                if signal:
                    print(f"✅ Signal generated!")
                    print(f"   Type: {signal.signal_type}")
                    print(f"   Price: {signal.price}")
                    print(f"   Confidence: {signal.confidence}")
                    print(f"   Timestamp: {signal.timestamp}")
                    print(f"   Timeframe: {signal.timeframe}")
                else:
                    print("⚠️ No signal generated (returned None)")

            except Exception as e:
                print(f"❌ Signal generation error: {e}")
                import traceback

                traceback.print_exc()
        else:
            print(f"⚠️ Insufficient data for signal generation:")
            print(f"   Weekly: {len(weekly_data)} (need ≥50)")
            print(f"   Daily: {len(daily_data)} (need ≥50)")
            print(f"   4H: {len(historical_data)} (need ≥200)")

    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_signals())
