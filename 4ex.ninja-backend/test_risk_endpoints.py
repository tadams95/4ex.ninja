#!/usr/bin/env python3
"""
Test script for Phase 2 VaR & Correlation Dashboard API endpoints
Task 1.1: Backend API Endpoints testing
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add src to path
sys.path.append("/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/src")


async def test_var_summary():
    """Test the /api/risk/var-summary endpoint logic"""
    print("🧪 Testing VaR Summary Endpoint Logic...")

    try:
        from api.routes.risk import get_var_summary, get_var_monitor

        # Test the dependency
        var_monitor = await get_var_monitor()
        print(
            f"   VaR Monitor Status: {'✅ Available' if var_monitor else '⚠️ Fallback Mode'}"
        )

        # Test the endpoint function
        result = await get_var_summary(var_monitor)

        print("   📊 VaR Summary Result:")
        print(f"   - Historical VaR: {result['current_var']['historical']:.4f}")
        print(f"   - Parametric VaR: {result['current_var']['parametric']:.4f}")
        print(f"   - Monte Carlo VaR: {result['current_var']['monte_carlo']:.4f}")
        print(f"   - Target: {result['target']:.4f}")
        print(f"   - Status: {result['status']}")
        print(f"   - Timestamp: {result['timestamp']}")

        return True

    except Exception as e:
        print(f"   ❌ Error testing VaR summary: {e}")
        return False


async def test_correlation_matrix():
    """Test the /api/risk/correlation-matrix endpoint logic"""
    print("🧪 Testing Correlation Matrix Endpoint Logic...")

    try:
        from api.routes.risk import get_correlation_matrix, get_correlation_manager

        # Test the dependency
        correlation_manager = await get_correlation_manager()
        print(
            f"   Correlation Manager Status: {'✅ Available' if correlation_manager else '⚠️ Fallback Mode'}"
        )

        # Test the endpoint function
        result = await get_correlation_matrix(correlation_manager)

        print("   📊 Correlation Matrix Result:")
        print(f"   - Matrix pairs: {list(result['correlation_matrix'].keys())}")
        print(f"   - Breach alerts: {len(result['breach_alerts'])} alerts")
        if result["breach_alerts"]:
            for alert in result["breach_alerts"]:
                print(f"     🚨 {alert}")
        print(f"   - Timestamp: {result['timestamp']}")

        return True

    except Exception as e:
        print(f"   ❌ Error testing correlation matrix: {e}")
        return False


async def test_risk_status():
    """Test the /api/risk/status endpoint logic"""
    print("🧪 Testing Risk Status Endpoint Logic...")

    try:
        from api.routes.risk import get_risk_status

        result = await get_risk_status()

        print("   📊 Risk Status Result:")
        print(f"   - System Status: {result['risk_system_status']}")
        print(f"   - VaR Monitor: {'✅' if result['var_monitor_available'] else '❌'}")
        print(
            f"   - Correlation Manager: {'✅' if result['correlation_manager_available'] else '❌'}"
        )
        print(f"   - Fallback Mode: {'⚠️ Yes' if result['fallback_mode'] else '✅ No'}")
        print(f"   - Timestamp: {result['timestamp']}")

        return True

    except Exception as e:
        print(f"   ❌ Error testing risk status: {e}")
        return False


async def main():
    """Run all endpoint tests"""
    print("🚀 Phase 2 VaR & Correlation Dashboard API Endpoint Tests")
    print("=" * 60)

    # Test each endpoint
    var_success = await test_var_summary()
    print()
    correlation_success = await test_correlation_matrix()
    print()
    status_success = await test_risk_status()
    print()

    # Summary
    print("📋 Test Summary:")
    print(f"   VaR Summary Endpoint: {'✅ PASS' if var_success else '❌ FAIL'}")
    print(
        f"   Correlation Matrix Endpoint: {'✅ PASS' if correlation_success else '❌ FAIL'}"
    )
    print(f"   Risk Status Endpoint: {'✅ PASS' if status_success else '❌ FAIL'}")

    all_passed = var_success and correlation_success and status_success
    print(
        f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )

    if all_passed:
        print("\n🎉 Task 1.1: Backend API Endpoints - COMPLETED!")
        print("✅ Ready to proceed with Task 1.2: Frontend Dashboard Shell")
    else:
        print("\n⚠️ Task 1.1: Backend API Endpoints - NEEDS ATTENTION")


if __name__ == "__main__":
    asyncio.run(main())
