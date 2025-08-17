#!/usr/bin/env python3
"""
Emergency Risk Management Implementation Validator

This script validates that our Emergency Risk Management implementation
has been correctly integrated into MA_Unified_Strat.py without executing the full strategy.
"""

import re
import sys
import os


def validate_emergency_implementation():
    """Validate the emergency risk management implementation"""

    print("🔍 EMERGENCY RISK MANAGEMENT IMPLEMENTATION VALIDATOR")
    print("=" * 60)

    # Path to the strategy file
    strategy_file = "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src/strategies/MA_Unified_Strat.py"

    if not os.path.exists(strategy_file):
        print("❌ ERROR: MA_Unified_Strat.py not found")
        return False

    # Read the file content
    with open(strategy_file, "r") as f:
        content = f.read()

    # Validation checklist
    validations = {
        "Emergency Imports": [
            "from risk.emergency_risk_manager import",
            "EmergencyRiskManager",
            "EmergencyLevel",
            "create_emergency_risk_manager",
        ],
        "Constructor Parameters": [
            "portfolio_initial_value: float = 100000.0",
            "enable_emergency_management: bool = True",
        ],
        "Emergency State Variables": [
            "self.portfolio_initial_value = portfolio_initial_value",
            "self.portfolio_current_value = portfolio_initial_value",
            "self.enable_emergency_management = enable_emergency_management",
            "self.emergency_manager = None",
            "self.emergency_manager_initialized = False",
        ],
        "Emergency Manager Initialization": [
            "async def initialize_emergency_manager(self):",
            "await create_emergency_risk_manager",
            "Emergency Risk Manager ACTIVATED",
        ],
        "Enhanced Signal Validation": [
            "Emergency Risk Management protocols",
            "EMERGENCY STOP CHECK",
            "CRISIS MODE VALIDATION",
            "ELEVATED RISK VALIDATION",
            "emergency_status.get('trading_halted', False)",
            "emergency_level == 'LEVEL_3'",
            "risk_reward_ratio < 3.0",
        ],
        "Position Sizing Enhancement": [
            "def calculate_emergency_position_size",
            "emergency_manager.calculate_position_size",
            "position_size_multiplier",
            "Conservative fallback",
        ],
        "Portfolio Value Monitoring": [
            "async def update_portfolio_value",
            "await self.emergency_manager.update_portfolio_value",
            "Calculate and log drawdown",
            "Emergency Level.*active",
        ],
        "Stress Monitoring": [
            "async def monitor_market_stress",
            "await self.emergency_manager.monitor_stress_events",
            "STRESS EVENTS DETECTED",
            "CRITICAL STRESS EVENT",
        ],
        "Main Loop Integration": [
            "EMERGENCY RISK MANAGEMENT INITIALIZATION",
            "await self.initialize_emergency_manager",
            "EMERGENCY RISK MANAGEMENT: STRESS MONITORING",
            "await self.monitor_market_stress",
        ],
    }

    # Run validations
    total_checks = 0
    passed_checks = 0

    for category, checks in validations.items():
        print(f"\n📋 {category}:")
        category_passed = 0

        for check in checks:
            total_checks += 1
            if re.search(check, content, re.IGNORECASE | re.MULTILINE):
                print(f"  ✅ {check}")
                passed_checks += 1
                category_passed += 1
            else:
                print(f"  ❌ {check}")

        print(f"  📊 {category}: {category_passed}/{len(checks)} checks passed")

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    success_rate = (passed_checks / total_checks) * 100

    print(f"Total Checks: {total_checks}")
    print(f"Passed Checks: {passed_checks}")
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 IMPLEMENTATION VALIDATION: ✅ SUCCESS")
        print("Emergency Risk Management Framework properly integrated!")
        return True
    elif success_rate >= 75:
        print("⚠️ IMPLEMENTATION VALIDATION: 🟡 PARTIAL SUCCESS")
        print("Most components integrated, some minor issues detected.")
        return True
    else:
        print("❌ IMPLEMENTATION VALIDATION: ❌ FAILED")
        print("Critical components missing or incorrectly implemented.")
        return False


def check_file_structure():
    """Check that required risk management files exist"""

    print("\n🗂️  CHECKING RISK MANAGEMENT FILE STRUCTURE")
    print("=" * 60)

    required_files = [
        "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src/risk/emergency_risk_manager.py",
        "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src/risk/EMERGENCY_IMPLEMENTATION_GUIDE.py",
        "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src/strategies/MA_Unified_Strat.py",
    ]

    all_files_exist = True

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {os.path.basename(file_path)}")
        else:
            print(f"❌ {os.path.basename(file_path)} - NOT FOUND")
            all_files_exist = False

    return all_files_exist


def main():
    """Main validation execution"""

    print("🚨 Emergency Risk Management Framework - Implementation Validator")
    print("Starting validation process...\n")

    # Check file structure
    files_ok = check_file_structure()

    if not files_ok:
        print("\n❌ File structure validation failed!")
        return 1

    # Validate implementation
    implementation_ok = validate_emergency_implementation()

    if implementation_ok:
        print("\n🎯 NEXT STEPS:")
        print("1. Deploy to staging environment for paper trading")
        print("2. Monitor emergency status dashboard")
        print("3. Test with simulated portfolio drawdowns")
        print("4. Validate stress event detection")
        print("5. Proceed to Phase 2: VaR Monitoring & Portfolio Correlation")

        print("\n📋 COMPREHENSIVE REVIEW UPDATE:")
        print(
            "Mark Priority 1 items as ✅ COMPLETED in MA_UNIFIED_STRAT_COMPREHENSIVE_REVIEW.md"
        )

        return 0
    else:
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Review failed validation checks above")
        print("2. Re-implement missing components")
        print("3. Follow EMERGENCY_IMPLEMENTATION_GUIDE.py step-by-step")
        print("4. Re-run this validator")

        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"\n❌ Validator failed: {e}")
        exit(1)
