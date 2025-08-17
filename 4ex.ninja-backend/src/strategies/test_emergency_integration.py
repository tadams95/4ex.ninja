#!/usr/bin/env python3
"""
Test Emergency Risk Management Integration with MA_Unified_Strat.py

This script validates that the Emergency Risk Management Framework is properly integrated
into the MovingAverageCrossStrategy class without breaking existing functionality.
"""

import asyncio
import logging
import pandas as pd
import sys
import os
from datetime import datetime, timezone

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the enhanced strategy
from strategies.MA_Unified_Strat import MovingAverageCrossStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_emergency_integration():
    """Test the emergency risk management integration"""

    logger.info("🧪 Starting Emergency Risk Management Integration Test")

    # Test configuration (using EUR_USD_H4 equivalent)
    test_config = {
        "pair": "EUR_USD",
        "timeframe": "H4",
        "slow_ma": 50,
        "fast_ma": 20,
        "atr_period": 14,
        "sl_atr_multiplier": 1.5,
        "tp_atr_multiplier": 2.0,
        "min_atr_value": 0.0001,
        "min_rr_ratio": 1.0,
        "sleep_seconds": 60,  # Fast testing
        "min_candles": 200,
        "portfolio_initial_value": 10000.0,  # Test with smaller portfolio
        "enable_emergency_management": True,
    }

    try:
        # Initialize strategy with emergency management
        logger.info(
            "📊 Initializing MovingAverageCrossStrategy with Emergency Risk Management..."
        )
        strategy = MovingAverageCrossStrategy(**test_config)

        # Test 1: Verify emergency management is enabled
        assert (
            strategy.enable_emergency_management == True
        ), "Emergency management should be enabled"
        assert (
            strategy.portfolio_initial_value == 10000.0
        ), "Portfolio initial value should be set"
        assert (
            strategy.emergency_manager is None
        ), "Emergency manager should not be initialized yet"
        logger.info("✅ Test 1 PASSED: Emergency management configuration verified")

        # Test 2: Initialize emergency manager
        logger.info("🚨 Testing emergency manager initialization...")
        await strategy.initialize_emergency_manager()

        assert (
            strategy.emergency_manager is not None
        ), "Emergency manager should be initialized"
        assert (
            strategy.emergency_manager_initialized == True
        ), "Emergency manager initialized flag should be True"
        logger.info("✅ Test 2 PASSED: Emergency manager initialization successful")

        # Test 3: Test emergency status check
        logger.info("📊 Testing emergency status retrieval...")
        emergency_status = strategy.emergency_manager.get_emergency_status()

        assert (
            "emergency_level" in emergency_status
        ), "Emergency status should contain emergency_level"
        assert (
            "trading_halted" in emergency_status
        ), "Emergency status should contain trading_halted"
        assert (
            emergency_status["emergency_level"] == "NORMAL"
        ), "Initial emergency level should be NORMAL"
        assert (
            emergency_status["trading_halted"] == False
        ), "Trading should not be halted initially"
        logger.info("✅ Test 3 PASSED: Emergency status retrieval successful")

        # Test 4: Test signal validation with emergency management
        logger.info("🔍 Testing enhanced signal validation...")

        # Test normal signal validation
        valid_signal = strategy.validate_signal(
            signal=1, atr=0.0002, risk_reward_ratio=2.0
        )
        assert valid_signal == True, "Valid signal should pass validation"

        # Test invalid signal validation
        invalid_signal = strategy.validate_signal(
            signal=1, atr=0.00001, risk_reward_ratio=0.5
        )
        assert invalid_signal == False, "Invalid signal should fail validation"

        logger.info("✅ Test 4 PASSED: Enhanced signal validation working")

        # Test 5: Test position sizing calculation
        logger.info("💰 Testing emergency position sizing...")

        base_size = 1000.0
        adjusted_size = strategy.calculate_emergency_position_size(base_size=base_size)

        assert isinstance(adjusted_size, float), "Adjusted size should be a float"
        assert adjusted_size > 0, "Adjusted size should be positive"
        logger.info(f"Position sizing: ${base_size} → ${adjusted_size}")
        logger.info("✅ Test 5 PASSED: Emergency position sizing working")

        # Test 6: Test portfolio value update
        logger.info("📈 Testing portfolio value update...")

        initial_value = strategy.portfolio_current_value
        new_value = 9500.0  # 5% loss
        await strategy.update_portfolio_value(new_value)

        assert (
            strategy.portfolio_current_value == new_value
        ), "Portfolio value should be updated"

        # Check if emergency level changed (should still be NORMAL for 5% loss)
        emergency_status = strategy.emergency_manager.get_emergency_status()
        assert (
            emergency_status["emergency_level"] == "NORMAL"
        ), "Emergency level should still be NORMAL"
        logger.info("✅ Test 6 PASSED: Portfolio value update working")

        # Test 7: Test stress monitoring with mock data
        logger.info("🚨 Testing stress monitoring...")

        # Create mock price data
        mock_data = pd.DataFrame(
            {
                "open": [1.1000, 1.1010, 1.1020, 1.1030, 1.1040],
                "high": [1.1005, 1.1015, 1.1025, 1.1035, 1.1045],
                "low": [1.0995, 1.1005, 1.1015, 1.1025, 1.1035],
                "close": [1.1002, 1.1012, 1.1022, 1.1032, 1.1042],
                "time": pd.date_range(start="2025-01-01", periods=5, freq="4H"),
            }
        )
        mock_data.set_index("time", inplace=True)

        stress_events = await strategy.monitor_market_stress(mock_data)
        assert isinstance(stress_events, list), "Stress events should be a list"
        logger.info(f"Stress monitoring detected {len(stress_events)} events")
        logger.info("✅ Test 7 PASSED: Stress monitoring working")

        # Test 8: Test with emergency management disabled
        logger.info("🔴 Testing with emergency management disabled...")

        disabled_config = test_config.copy()
        disabled_config["enable_emergency_management"] = False

        disabled_strategy = MovingAverageCrossStrategy(**disabled_config)
        assert (
            disabled_strategy.enable_emergency_management == False
        ), "Emergency management should be disabled"

        # Should still validate signals normally
        valid_signal_disabled = disabled_strategy.validate_signal(
            signal=1, atr=0.0002, risk_reward_ratio=2.0
        )
        assert (
            valid_signal_disabled == True
        ), "Signal validation should work without emergency management"

        logger.info("✅ Test 8 PASSED: Disabled emergency management working")

        logger.info(
            "🎉 ALL TESTS PASSED! Emergency Risk Management integration successful!"
        )

        # Print summary
        print("\n" + "=" * 80)
        print("🎯 EMERGENCY RISK MANAGEMENT INTEGRATION TEST RESULTS")
        print("=" * 80)
        print("✅ Emergency Risk Management Framework successfully integrated")
        print("✅ All 8 test cases passed")
        print("✅ Backward compatibility maintained")
        print("✅ Ready for paper trading validation")
        print("=" * 80)

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print("❌ EMERGENCY RISK MANAGEMENT INTEGRATION TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print("=" * 80)
        return False


async def main():
    """Main test execution"""
    success = await test_emergency_integration()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        exit(1)
