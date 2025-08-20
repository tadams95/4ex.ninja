#!/usr/bin/env python3
"""
Test script for Production Confluence Strategy
Tests the production-ready multi-timeframe confluence strategy
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.production_confluence_strategy import ProductionConfluenceStrategy
from services.data_service import DataService

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_confluence_strategy():
    """Test the production confluence strategy"""

    print("🚀 TESTING PRODUCTION CONFLUENCE STRATEGY")
    print("=" * 60)

    try:
        # Initialize services
        data_service = DataService()
        confluence_strategy = ProductionConfluenceStrategy(data_service)

        # Get strategy info
        strategy_info = confluence_strategy.get_strategy_info()
        print(f"\n📊 Strategy: {strategy_info['name']}")
        print(f"📊 Version: {strategy_info['version']}")
        print(f"📊 Timeframes: {', '.join(strategy_info['timeframes'])}")
        print(f"📊 Confluence Threshold: {strategy_info['confluence_threshold']}")
        print(f"📊 Max Risk: {strategy_info['max_risk_per_trade']*100:.1f}%")

        print(f"\n🏆 Top Performing Pairs:")
        for pair in strategy_info["top_pairs"]:
            priority = confluence_strategy.pair_priorities.get(pair, 0.5)
            print(f"   {pair}: Priority {priority:.2f}")

        # Test confluence analysis for top pairs
        print(f"\n🔍 TESTING CONFLUENCE ANALYSIS")
        print("-" * 40)

        test_pairs = ["USD_JPY", "GBP_JPY", "EUR_JPY"]  # Top performers

        for pair in test_pairs:
            print(f"\n📊 Analyzing {pair}...")

            try:
                analysis = await confluence_strategy.analyze_confluence(pair)

                if analysis:
                    print(f"✅ {pair} Confluence Found!")
                    print(f"   Confluence Score: {analysis.confluence_score:.2f}")
                    print(f"   Strength: {analysis.confluence_strength.value}")
                    print(f"   Recommended Action: {analysis.recommended_action.value}")
                    print(f"   Confidence: {analysis.confidence:.2f}")
                    print(f"   Entry Price: {analysis.entry_price:.5f}")
                    print(f"   Stop Loss: {analysis.stop_loss:.5f}")
                    print(f"   Take Profit: {analysis.take_profit:.5f}")
                    print(f"   Risk/Reward: 1:{analysis.risk_reward_ratio:.1f}")

                    print(f"   📈 Timeframe Analysis:")
                    print(
                        f"      Weekly: {analysis.weekly.trend_direction} (strength: {analysis.weekly.signal_strength:.2f})"
                    )
                    print(
                        f"      Daily: {analysis.daily.trend_direction} (strength: {analysis.daily.signal_strength:.2f})"
                    )
                    print(
                        f"      H4: {analysis.h4.trend_direction} (strength: {analysis.h4.signal_strength:.2f})"
                    )

                else:
                    print(f"❌ {pair}: No confluence found (below threshold)")

            except Exception as e:
                print(f"❌ {pair}: Error - {str(e)}")

        # Test signal generation
        print(f"\n🎯 TESTING SIGNAL GENERATION")
        print("-" * 40)

        for pair in test_pairs:
            try:
                signal = await confluence_strategy.generate_trading_signal(pair)

                if signal:
                    print(f"✅ {pair}: Signal Generated")
                    print(f"   Type: {signal.signal_type.value}")
                    print(f"   Price: {signal.price:.5f}")
                    print(f"   Confidence: {signal.confidence:.2f}")
                    print(f"   Strategy: {signal.strategy_type}")
                else:
                    print(f"❌ {pair}: No signal generated")

            except Exception as e:
                print(f"❌ {pair}: Signal generation error - {str(e)}")

        # Test full market scan
        print(f"\n🌐 TESTING FULL MARKET SCAN")
        print("-" * 40)

        try:
            confluence_setups = await confluence_strategy.scan_all_pairs()

            print(f"📊 Found {len(confluence_setups)} confluence opportunities:")

            for i, setup in enumerate(confluence_setups, 1):
                print(
                    f"   {i}. {setup.pair}: {setup.recommended_action.value} "
                    f"(Score: {setup.confluence_score:.2f}, "
                    f"Strength: {setup.confluence_strength.value}, "
                    f"R:R: 1:{setup.risk_reward_ratio:.1f})"
                )

            if not confluence_setups:
                print(
                    "   No confluence opportunities found in current market conditions"
                )

        except Exception as e:
            print(f"❌ Market scan error: {str(e)}")

        print(f"\n✅ PRODUCTION CONFLUENCE STRATEGY TEST COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Fatal error during testing: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_confluence_strategy())
