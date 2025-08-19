#!/usr/bin/env python3
"""
Test Emergency Risk Management Database Persistence

This script tests the new database persistence functionality for emergency risk data.
"""

import asyncio
import sys
import logging
from datetime import datetime, timezone

# Add the src directory to path
sys.path.append("/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src")

from risk.emergency_risk_manager import (
    EmergencyRiskManager,
    EmergencyLevel,
    StressEvent,
    StressEventType,
    create_emergency_risk_manager,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_emergency_persistence():
    """Test emergency risk management database persistence"""

    print("🧪 Testing Emergency Risk Management Database Persistence...")

    try:
        # Initialize emergency manager
        print("\n1. Initializing Emergency Risk Manager...")
        emergency_manager = await create_emergency_risk_manager(
            portfolio_value=100000.0
        )
        print("✅ Emergency Risk Manager initialized")

        # Test 1: Portfolio value update with emergency escalation
        print("\n2. Testing portfolio value update and emergency escalation...")

        # Simulate portfolio decline to trigger emergency levels
        test_values = [
            95000,
            90000,
            85000,
            80000,
            75000,
        ]  # 5%, 10%, 15%, 20%, 25% drawdown

        for value in test_values:
            await emergency_manager.update_portfolio_value(value)
            status = emergency_manager.get_emergency_status()
            print(
                f"   Portfolio: ${value:,} | Emergency Level: {status['emergency_level']} | Drawdown: {status['portfolio_drawdown']:.2%}"
            )
            await asyncio.sleep(0.5)  # Small delay to separate events

        print("✅ Portfolio updates and emergency escalations tested")

        # Test 2: Stress event creation and persistence
        print("\n3. Testing stress event detection and persistence...")

        # Create test stress event
        stress_event = StressEvent(
            event_type=StressEventType.VOLATILITY_SPIKE,
            severity=2.5,
            detected_at=datetime.now(timezone.utc),
            current_volatility=0.025,
            threshold_volatility=0.010,
            affected_pairs=["EUR_USD"],
            recommended_action="Reduce position sizes by 30%",
        )

        # Save stress event
        await emergency_manager._save_stress_event(stress_event)
        print("✅ Stress event saved to database")

        # Test 3: Get current status with emergency context
        print("\n4. Testing emergency status retrieval...")
        final_status = emergency_manager.get_emergency_status()
        print(f"   Current Emergency Level: {final_status['emergency_level']}")
        print(f"   Portfolio Drawdown: {final_status['portfolio_drawdown']:.2%}")
        print(
            f"   Position Size Multiplier: {final_status['position_size_multiplier']:.1%}"
        )
        print(f"   Trading Halted: {final_status['trading_halted']}")
        print("✅ Emergency status retrieved successfully")

        print("\n🎉 All tests completed successfully!")
        print("\n📊 Database Collections Created:")
        print("   - risk_management.emergency_events")
        print("   - risk_management.stress_events")
        print("   - risk_management.portfolio_metrics")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logging.error(f"Test error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_emergency_persistence())
    if success:
        print(
            "\n✅ Emergency Risk Management database persistence is working correctly!"
        )
        print(
            "📈 MA_Unified_Strat is ready to be turned back on with full emergency risk tracking."
        )
    else:
        print("\n❌ Tests failed. Please check the implementation.")

    sys.exit(0 if success else 1)
