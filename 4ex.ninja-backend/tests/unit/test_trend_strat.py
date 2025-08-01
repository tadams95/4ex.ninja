"""
Trend Strategy Tests - Testing trend following strategy functionality

Tests for the trend following strategy implementation including signal generation,
data preparation, and strategy validation.
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from src.strategies.trend_follow_strat import TrendFollowingStrategy
import pandas as pd

from src.strategies.base_strategy import SignalType

# Don't need to test this, just a demo


def test_strategy_initialization():
    """Test strategy initialization."""
    print("Testing strategy initialization...")

    try:
        strategy = TrendFollowingStrategy("EUR_USD")
        assert strategy.instrument == "EUR_USD"
        print("✓ Strategy initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Strategy initialization failed: {e}")
        return False


def test_data_preparation():
    """Test data preparation functionality."""
    print("Testing data preparation...")

    try:
        strategy = TrendFollowingStrategy("EUR_USD")

        # Prepare data for last month
        end_date = pd.Timestamp.now(tz="UTC")
        start_date = end_date - pd.Timedelta(days=30)

        strategy.prepare_data(start_date.to_pydatetime(), end_date.to_pydatetime())

        # Check if data was loaded
        if "H1" in strategy.data and not strategy.data["H1"].empty:
            print(
                f"✓ Data prepared successfully - {len(strategy.data['H1'])} H1 candles loaded"
            )
            return True
        else:
            print("✗ No H1 data loaded")
            return False

    except Exception as e:
        print(f"✗ Data preparation failed: {e}")
        return False


def test_signal_generation():
    """Test signal generation functionality."""
    print("Testing signal generation...")

    try:
        strategy = TrendFollowingStrategy("EUR_USD")

        # Prepare data for last 6 months with explicit timezone
        end_date = pd.Timestamp.now(tz="UTC")
        start_date = end_date - pd.Timedelta(days=180)

        strategy.prepare_data(start_date.to_pydatetime(), end_date.to_pydatetime())

        if "H1" not in strategy.data or strategy.data["H1"].empty:
            print("✗ No data available for signal generation")
            return False

        h1_timestamps = strategy.data["H1"].index

        print("\nAnalyzing signals across recent H1 candles...")
        buy_signals = 0
        sell_signals = 0
        no_signals = 0

        # Test signal generation on recent candles
        test_count = min(100, len(h1_timestamps))  # Test last 100 candles or available

        for timestamp in h1_timestamps[-test_count:]:
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize("UTC")

            signal = strategy.generate_signal(timestamp)

            # Compare using SignalType enum directly
            if signal.type == SignalType.BUY:
                buy_signals += 1
                if buy_signals <= 3:  # Show first 3 BUY signals
                    print(f"\n🟢 BUY Signal at {timestamp}:")
                    print(f"Entry: {signal.price:.5f}")
                    print(f"Stop Loss: {signal.stop_loss:.5f}")
                    print(f"Take Profit: {signal.take_profit:.5f}")

            elif signal.type == SignalType.SELL:
                sell_signals += 1
                if sell_signals <= 3:  # Show first 3 SELL signals
                    print(f"\n🔴 SELL Signal at {timestamp}:")
                    print(f"Entry: {signal.price:.5f}")
                    print(f"Stop Loss: {signal.stop_loss:.5f}")
                    print(f"Take Profit: {signal.take_profit:.5f}")

            else:
                no_signals += 1

        # Print summary
        total_tested = buy_signals + sell_signals + no_signals
        print(f"\n--- Signal Generation Summary ---")
        print(f"Total candles tested: {total_tested}")
        print(f"BUY signals: {buy_signals}")
        print(f"SELL signals: {sell_signals}")
        print(f"No signals: {no_signals}")

        if total_tested > 0:
            print(
                f"Signal rate: {((buy_signals + sell_signals) / total_tested * 100):.1f}%"
            )

        print("✓ Signal generation completed successfully")
        return True

    except Exception as e:
        print(f"✗ Signal generation failed: {e}")
        return False


def test_signal_validation():
    """Test signal validation and consistency."""
    print("Testing signal validation...")

    try:
        strategy = TrendFollowingStrategy("EUR_USD")

        # Prepare data
        end_date = pd.Timestamp.now(tz="UTC")
        start_date = end_date - pd.Timedelta(days=30)

        strategy.prepare_data(start_date.to_pydatetime(), end_date.to_pydatetime())

        if "H1" not in strategy.data or strategy.data["H1"].empty:
            print("✗ No data available for signal validation")
            return False

        h1_timestamps = strategy.data["H1"].index
        valid_signals = 0
        invalid_signals = 0

        # Test recent candles
        test_count = min(50, len(h1_timestamps))

        for timestamp in h1_timestamps[-test_count:]:
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize("UTC")

            signal = strategy.generate_signal(timestamp)

            # Validate signal structure
            if hasattr(signal, "type") and hasattr(signal, "price"):
                # For BUY signals
                if signal.type == SignalType.BUY:
                    if (
                        hasattr(signal, "stop_loss")
                        and hasattr(signal, "take_profit")
                        and signal.stop_loss < signal.price < signal.take_profit
                    ):
                        valid_signals += 1
                    else:
                        invalid_signals += 1

                # For SELL signals
                elif signal.type == SignalType.SELL:
                    if (
                        hasattr(signal, "stop_loss")
                        and hasattr(signal, "take_profit")
                        and signal.take_profit < signal.price < signal.stop_loss
                    ):
                        valid_signals += 1
                    else:
                        invalid_signals += 1

                # For NO signals
                else:
                    valid_signals += 1  # No signal is valid
            else:
                invalid_signals += 1

        print(f"Valid signals: {valid_signals}")
        print(f"Invalid signals: {invalid_signals}")

        if invalid_signals == 0:
            print("✓ All signals are valid")
            return True
        else:
            print(f"✗ Found {invalid_signals} invalid signals")
            return False

    except Exception as e:
        print(f"✗ Signal validation failed: {e}")
        return False


def main():
    """Run all trend strategy tests."""
    print("Trend Following Strategy Tests")
    print("=" * 40)

    tests = [
        ("Strategy Initialization", test_strategy_initialization),
        ("Data Preparation", test_data_preparation),
        ("Signal Generation", test_signal_generation),
        ("Signal Validation", test_signal_validation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))

    # Print summary
    print("\n" + "=" * 40)
    print("Trend Strategy Test Results")
    print("=" * 40)

    passed = 0
    failed = 0

    for test_name, success, error in results:
        if success:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            if error:
                print(f"   Error: {error}")
            failed += 1

    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All trend strategy tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
