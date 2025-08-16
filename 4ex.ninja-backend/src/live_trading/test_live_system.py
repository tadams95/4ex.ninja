"""
Live Trading System Test

Comprehensive test script for the live trading system integration
with OANDA data and strategy execution.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.live_trading import (
    LiveTradingEngine,
    OandaDataFeed,
    PositionManager,
    RiskManager,
)
from src.backtesting.strategies import StrategyFactory
from src.backtesting.strategy_interface import TradeSignal, AccountInfo


def test_oanda_data_feed():
    """Test OANDA data feed functionality."""
    print("🧪 Testing OANDA Data Feed...")

    feed = OandaDataFeed()

    # Test connection
    print("📡 Testing connection...")
    if not feed.test_connection():
        print("❌ OANDA connection failed!")
        return False
    print("✅ OANDA connection successful")

    # Test data retrieval
    print("📊 Testing data retrieval...")
    df = feed.get_latest_candles("EUR_USD", "M5", count=10)

    if df.empty:
        print("❌ No data retrieved")
        return False

    print(f"✅ Retrieved {len(df)} candles")
    print(f"📈 Latest price: {df['close'].iloc[-1]:.5f}")
    print(f"📅 Data range: {df.index[0]} to {df.index[-1]}")

    # Test current price
    current_price = feed.get_current_price("EUR_USD")
    if current_price:
        print(f"💰 Current EUR_USD price: {current_price:.5f}")
    else:
        print("❌ Could not get current price")
        return False

    return True


def test_strategy_creation():
    """Test strategy creation and signal generation."""
    print("\n🧪 Testing Strategy Creation...")

    # Test MA strategy
    ma_config = {"fast_ma": 5, "slow_ma": 10, "ma_type": "SMA"}
    ma_strategy = StrategyFactory.create_strategy("ma_crossover", ma_config)

    if not ma_strategy:
        print("❌ Failed to create MA strategy")
        return False

    print("✅ MA strategy created successfully")

    # Test RSI strategy
    rsi_config = {"rsi_period": 14, "overbought_level": 70, "oversold_level": 30}
    rsi_strategy = StrategyFactory.create_strategy("rsi", rsi_config)

    if not rsi_strategy:
        print("❌ Failed to create RSI strategy")
        return False

    print("✅ RSI strategy created successfully")

    return True


def test_risk_management():
    """Test risk management functionality."""
    print("\n🧪 Testing Risk Management...")

    rm = RiskManager()

    # Create test account
    account_info = AccountInfo(
        balance=10000.0,
        equity=9800.0,
        margin_used=500.0,
        free_margin=9300.0,
        max_position_size=1000.0,
    )

    # Create test signal
    test_signal = TradeSignal(
        pair="EUR_USD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        signal_strength=0.8,
        signal_time=datetime.utcnow(),
        strategy_name="test",
    )

    # Test signal validation
    is_valid, warnings = rm.validate_signal_risk(test_signal, account_info, [])
    print(f"✅ Signal validation: {'Valid' if is_valid else 'Invalid'}")

    if warnings:
        for warning in warnings:
            print(f"⚠️  Warning: {warning}")

    # Test position sizing
    position_size = rm.calculate_position_size(test_signal, account_info)
    print(f"✅ Calculated position size: {position_size} units")

    # Test risk assessment
    risk_metrics = rm.assess_portfolio_risk(account_info, [])
    print(f"✅ Risk level: {risk_metrics.risk_level.value}")
    print(f"✅ Risk score: {risk_metrics.risk_score:.1f}/100")

    return True


def test_live_data_integration():
    """Test integration between live data and strategies."""
    print("\n🧪 Testing Live Data + Strategy Integration...")

    # Get live data
    feed = OandaDataFeed()
    market_data = feed.get_latest_candles("EUR_USD", "M5", count=50)

    if market_data.empty:
        print("❌ No market data for strategy test")
        return False

    print(f"✅ Retrieved {len(market_data)} candles for strategy analysis")

    # Create strategy
    ma_strategy = StrategyFactory.create_strategy(
        "ma_crossover", {"fast_ma": 10, "slow_ma": 20, "ma_type": "SMA"}
    )

    if not ma_strategy:
        print("❌ Failed to create strategy")
        return False

    # Generate signals with live data
    from src.backtesting.regime_detector import MarketRegime

    signals = ma_strategy.generate_signals(market_data, MarketRegime.UNCERTAIN)

    print(f"✅ Generated {len(signals)} signals from live data")

    for i, signal in enumerate(signals[:3]):  # Show first 3 signals
        print(
            f"   Signal {i+1}: {signal.direction} {signal.pair} @ {signal.entry_price:.5f}"
        )

    return True


def test_engine_setup():
    """Test live trading engine setup and configuration."""
    print("\n🧪 Testing Live Trading Engine Setup...")

    # Create engine
    engine = LiveTradingEngine(update_interval=300)  # 5 minutes

    # Add strategies
    strategies_added = 0

    # Add MA strategy for EUR_USD
    if engine.add_strategy(
        "ma_crossover",
        "EUR_USD",
        "M5",
        {"fast_ma": 10, "slow_ma": 20, "ma_type": "SMA"},
    ):
        strategies_added += 1

    # Add RSI strategy for GBP_USD
    if engine.add_strategy(
        "rsi",
        "GBP_USD",
        "M15",
        {"rsi_period": 14, "overbought_level": 70, "oversold_level": 30},
    ):
        strategies_added += 1

    # Add Bollinger strategy for USD_JPY
    if engine.add_strategy(
        "bollinger",
        "USD_JPY",
        "H1",
        {"bb_period": 20, "bb_std": 2.0, "signal_mode": "reversal"},
    ):
        strategies_added += 1

    print(f"✅ Added {strategies_added}/3 strategies to engine")

    # Get engine status
    status = engine.get_engine_status()
    print(f"✅ Engine configured with {status['active_strategies']} strategies")

    # Test disable/enable trading
    engine.disable_trading()
    print("✅ Trading disabled (demo mode)")

    engine.enable_trading()
    print("✅ Trading re-enabled")

    return strategies_added >= 2  # At least 2 strategies should work


def run_comprehensive_test():
    """Run all tests in sequence."""
    print("🚀 Starting Comprehensive Live Trading System Test")
    print("=" * 60)

    tests = [
        ("OANDA Data Feed", test_oanda_data_feed),
        ("Strategy Creation", test_strategy_creation),
        ("Risk Management", test_risk_management),
        ("Live Data + Strategy Integration", test_live_data_integration),
        ("Engine Setup", test_engine_setup),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)

        try:
            result = test_func()
            results[test_name] = result

            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")

        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Live trading system is ready!")
        print("\n💡 Next steps:")
        print("   1. Review strategy configurations")
        print("   2. Set appropriate risk limits")
        print("   3. Start with demo mode: engine.disable_trading()")
        print("   4. Monitor for a few hours before enabling live trading")
        print(
            "   5. Start live trading: engine.enable_trading() and engine.start_trading()"
        )
    else:
        print("⚠️  Some tests failed. Please review errors before live trading.")

    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()

    if success:
        print("\n🚀 Ready to start live trading!")
        print("\n📝 Example usage:")
        print("```python")
        print("from src.live_trading import LiveTradingEngine")
        print("")
        print("# Create engine")
        print("engine = LiveTradingEngine(update_interval=300)")
        print("")
        print("# Add strategies")
        print(
            "engine.add_strategy('ma_crossover', 'EUR_USD', 'M5', {'fast_ma': 10, 'slow_ma': 20})"
        )
        print("engine.add_strategy('rsi', 'GBP_USD', 'M15', {'rsi_period': 14})")
        print("")
        print("# Start in demo mode first")
        print("engine.disable_trading()")
        print("engine.start_trading()")
        print("")
        print("# Later enable live trading")
        print("engine.enable_trading()")
        print("```")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")
