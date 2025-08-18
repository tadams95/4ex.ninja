#!/usr/bin/env python3
"""
Async test script for Phase 2 VaR & Correlation Dashboard API endpoints.
Tests endpoint logic directly with proper async handling.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def test_endpoints():
    """Test all risk API endpoints"""
    print("🚀 Phase 2 VaR & Correlation Dashboard API Endpoint Tests (Async)")
    print("=" * 65)

    # Import the endpoint functions
    try:
        from api.routes.risk import (
            get_var_summary,
            get_correlation_matrix,
            get_risk_status,
        )

        print("✅ Risk API endpoints imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import endpoints: {e}")
        return

    # Test results tracking
    results = {}

    # Test VaR Summary Endpoint
    print("\n🧪 Testing VaR Summary Endpoint Logic...")
    try:
        var_result = await get_var_summary()
        results["var_summary"] = "✅ PASS"
        print("   📊 VaR Summary Result:")
        print(f"   - Parametric VaR: {var_result['portfolio_var']['parametric']}")
        print(f"   - Historical VaR: {var_result['portfolio_var']['historical']}")
        print(f"   - Monte Carlo VaR: {var_result['portfolio_var']['monte_carlo']}")
        print(
            f"   - Risk Utilization: {var_result['risk_metrics']['risk_utilization']}"
        )
        print(f"   - Position Count: {len(var_result['position_breakdown'])}")

    except Exception as e:
        results["var_summary"] = "❌ FAIL"
        print(f"   ❌ Error testing VaR summary: {e}")

    # Test Correlation Matrix Endpoint
    print("\n🧪 Testing Correlation Matrix Endpoint Logic...")
    try:
        corr_result = await get_correlation_matrix()
        results["correlation_matrix"] = "✅ PASS"
        print("   📈 Correlation Matrix Result:")
        print(
            f"   - Matrix Keys: {list(corr_result['matrix'].keys()) if corr_result['matrix'] else 'Empty'}"
        )
        print(f"   - High Correlations: {corr_result['risk_alerts']['breach_count']}")
        print(f"   - Threshold: {corr_result['risk_alerts']['threshold']}")
        print(f"   - Pairs Analysis Count: {len(corr_result['pairs_analysis'])}")

    except Exception as e:
        results["correlation_matrix"] = "❌ FAIL"
        print(f"   ❌ Error testing correlation matrix: {e}")

    # Test Risk Status Endpoint
    print("\n🧪 Testing Risk Status Endpoint Logic...")
    try:
        status_result = await get_risk_status()
        results["risk_status"] = "✅ PASS"
        print("   📊 Risk Status Result:")
        print(f"   - System Status: {status_result['risk_system_status']}")
        print(
            f"   - VaR Monitor: {'✅' if status_result['var_monitor_available'] else '❌'}"
        )
        print(
            f"   - Correlation Manager: {'✅' if status_result['correlation_manager_available'] else '❌'}"
        )
        print(
            f"   - Fallback Mode: {'✅ No' if not status_result['fallback_mode'] else '⚠️ Yes'}"
        )
        print(f"   - Timestamp: {status_result['timestamp']}")

    except Exception as e:
        results["risk_status"] = "❌ FAIL"
        print(f"   ❌ Error testing risk status: {e}")

    # Summary
    print(f"\n📋 Test Summary:")
    print(f"   VaR Summary Endpoint: {results.get('var_summary', '❌ NOT TESTED')}")
    print(
        f"   Correlation Matrix Endpoint: {results.get('correlation_matrix', '❌ NOT TESTED')}"
    )
    print(f"   Risk Status Endpoint: {results.get('risk_status', '❌ NOT TESTED')}")

    passed = sum(1 for result in results.values() if "✅" in result)
    total = len(results)

    if passed == total:
        print(f"\n🎯 Overall Result: ✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 Task 1.1: Backend API Endpoints - COMPLETE!")
    else:
        print(f"\n🎯 Overall Result: ❌ SOME TESTS FAILED ({passed}/{total})")
        print("\n⚠️ Task 1.1: Backend API Endpoints - NEEDS ATTENTION")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
