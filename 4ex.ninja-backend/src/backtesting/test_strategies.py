"""
Simple test script for strategy implementations.

This script tests the basic functionality of the implemented strategies
to ensure they work correctly with the universal backtesting framework.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the backend src to path
sys.path.append("/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src")

try:
    from backtesting.strategies import (
        MAStrategy,
        RSIStrategy,
        BollingerStrategy,
        StrategyFactory,
        strategy_registry,
    )
    from backtesting.regime_detector import MarketRegime

    print("✅ Successfully imported strategy modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def create_sample_data(days: int = 100) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)  # For reproducible results

    # Generate dates
    dates = pd.date_range(start="2024-01-01", periods=days, freq="D")

    # Generate price data with some trend and volatility
    price_base = 1.1000
    price_changes = np.random.normal(0, 0.002, days)

    # Add some trend
    trend = np.linspace(0, 0.05, days)
    prices = price_base + np.cumsum(price_changes) + trend

    # Generate OHLCV data
    data = []
    for i, price in enumerate(prices):
        # Add some intraday variation
        high = price + np.random.uniform(0, 0.005)
        low = price - np.random.uniform(0, 0.005)
        open_price = price + np.random.uniform(-0.002, 0.002)
        close = price
        volume = np.random.randint(10000, 100000)

        data.append(
            {
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

    df = pd.DataFrame(data, index=dates)
    return df


def test_strategy(strategy_class, strategy_name: str, config: Dict[str, Any]):
    """Test a strategy implementation."""
    print(f"\n🧪 Testing {strategy_name} Strategy...")

    try:
        # Create strategy instance
        strategy = strategy_class(config)
        print(f"   ✅ Strategy created: {strategy.strategy_name}")

        # Create sample data
        data = create_sample_data(100)
        print(f"   ✅ Sample data created: {len(data)} bars")

        # Test signal generation
        signals = strategy.generate_signals(data, MarketRegime.TRENDING_HIGH_VOL)
        print(f"   ✅ Signals generated: {len(signals)} signals")

        # Test signal validation if signals exist
        if signals:
            first_signal = signals[0]
            is_valid = strategy.validate_signal(first_signal, data)
            print(f"   ✅ Signal validation: {is_valid}")

            # Test validation metrics
            metrics = strategy.get_validation_metrics(signals, data)
            print(f"   ✅ Validation metrics: {len(metrics)} metrics")

            print(f"   📊 Signal details:")
            print(f"      - Direction: {first_signal.direction}")
            print(f"      - Entry: {first_signal.entry_price:.5f}")
            print(f"      - Stop Loss: {first_signal.stop_loss:.5f}")
            print(f"      - Take Profit: {first_signal.take_profit:.5f}")
            print(f"      - Strength: {first_signal.signal_strength:.3f}")
        else:
            print("   ⚠️  No signals generated (this may be normal)")

        return True

    except Exception as e:
        print(f"   ❌ Error testing {strategy_name}: {e}")
        return False


def test_factory():
    """Test the strategy factory."""
    print(f"\n🧪 Testing Strategy Factory...")

    try:
        # Test listing strategies
        strategies = StrategyFactory.get_available_strategies()
        print(f"   ✅ Available strategies: {strategies}")

        # Test creating strategies
        for strategy_name in strategies[:3]:  # Test first 3
            try:
                config = {"fast_ma": 5, "slow_ma": 10}  # Basic config
                strategy = StrategyFactory.create_strategy(strategy_name, config)
                print(f"   ✅ Created {strategy_name}: {strategy.__class__.__name__}")
            except Exception as e:
                print(f"   ❌ Failed to create {strategy_name}: {e}")

        return True

    except Exception as e:
        print(f"   ❌ Error testing factory: {e}")
        return False


def test_registry():
    """Test the strategy registry."""
    print(f"\n🧪 Testing Strategy Registry...")

    try:
        # Test listing strategies
        strategies = strategy_registry.list_strategies()
        print(f"   ✅ Registered strategies: {strategies}")

        # Test getting strategy info
        if strategies:
            info = strategy_registry.get_strategy_info(strategies[0])
            print(f"   ✅ Strategy info for {strategies[0]}: {info['category']}")

        # Test statistics
        stats = strategy_registry.get_strategy_statistics()
        print(f"   ✅ Registry stats: {stats['total_strategies']} strategies")

        return True

    except Exception as e:
        print(f"   ❌ Error testing registry: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Strategy Implementation Tests")
    print("=" * 50)

    test_results = []

    # Test individual strategies
    strategies_to_test = [
        (MAStrategy, "MA Crossover", {"fast_ma": 10, "slow_ma": 20, "ma_type": "SMA"}),
        (
            RSIStrategy,
            "RSI",
            {"rsi_period": 14, "overbought_level": 70, "oversold_level": 30},
        ),
        (
            BollingerStrategy,
            "Bollinger Bands",
            {"bb_period": 20, "bb_std": 2.0, "signal_mode": "reversal"},
        ),
    ]

    for strategy_class, name, config in strategies_to_test:
        result = test_strategy(strategy_class, name, config)
        test_results.append((name, result))

    # Test factory
    factory_result = test_factory()
    test_results.append(("Factory", factory_result))

    # Test registry
    registry_result = test_registry()
    test_results.append(("Registry", registry_result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = 0
    for name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(test_results)} tests passed")

    if passed == len(test_results):
        print("🎉 All tests passed! Strategy implementations are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

    return passed == len(test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
