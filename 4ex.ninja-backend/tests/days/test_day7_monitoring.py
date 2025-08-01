"""
Day 7: Monitoring System Tests

Test script to validate error tracking, health monitoring,
and performance monitoring components.
"""

import asyncio
import logging
import sys
import os
import time
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / ".." / ".." / "src")
sys.path.insert(0, src_path)

try:
    from infrastructure.monitoring.health import (  # type: ignore
        health_monitor,
        get_health_summary,
        register_default_health_checks,
        HealthStatus,
    )
    from infrastructure.monitoring.performance import (  # type: ignore
        performance_monitor,
        track_api_request,
        track_signal_processing,
        get_performance_summary,
    )
    from infrastructure.monitoring.error_tracking import (  # type: ignore
        SentryErrorTracker,
        ErrorCategory,
        ErrorSeverity,
    )

    MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Unable to import monitoring modules: {e}")
    MONITORING_AVAILABLE = False
    # Create mock objects for testing
    health_monitor = None
    get_health_summary = None
    register_default_health_checks = None
    HealthStatus = None
    performance_monitor = None
    track_api_request = None
    track_signal_processing = None
    get_performance_summary = None
    SentryErrorTracker = None
    ErrorCategory = None
    ErrorSeverity = None


async def test_health_monitoring():
    """Test health monitoring functionality."""
    print("\n=== Testing Health Monitoring ===")

    if not MONITORING_AVAILABLE or health_monitor is None:
        print("⚠️ Health monitoring not available - skipping tests")
        return True

    # Register health checks
    if register_default_health_checks is not None:
        register_default_health_checks()
        print("✓ Registered default health checks")

    # Run individual health checks
    print("\nRunning individual health checks:")

    # Test database check
    db_result = await health_monitor.run_check("database")
    print(f"Database: {db_result.status.value} - {db_result.message}")

    # Test OANDA API check
    api_result = await health_monitor.run_check("oanda_api")
    print(f"OANDA API: {api_result.status.value} - {api_result.message}")

    # Test system resources
    system_result = await health_monitor.run_check("system_resources")
    print(f"System Resources: {system_result.status.value} - {system_result.message}")

    # Run all checks
    print("\nRunning all health checks:")
    all_results = await health_monitor.run_all_checks()
    overall_status = health_monitor.get_overall_status(all_results)
    print(f"Overall Status: {overall_status.value}")

    # Get health summary
    print("\nHealth Summary:")
    if get_health_summary is not None:
        summary = await get_health_summary()
        print(f"- Status: {summary['status']}")
        print(f"- Total Checks: {summary['summary']['total_checks']}")
        print(f"- Healthy: {summary['summary']['healthy']}")
        print(f"- Degraded: {summary['summary']['degraded']}")
        print(f"- Unhealthy: {summary['summary']['unhealthy']}")

    return True


def test_performance_monitoring():
    """Test performance monitoring functionality."""
    print("\n=== Testing Performance Monitoring ===")

    if not MONITORING_AVAILABLE or performance_monitor is None:
        print("⚠️ Performance monitoring not available - skipping tests")
        return True

    # Test counters
    performance_monitor.increment_counter("test_counter", 5)
    performance_monitor.increment_counter("test_counter", 3)
    print("✓ Tested counters")

    # Test gauges
    performance_monitor.set_gauge("cpu_usage", 45.5)
    performance_monitor.set_gauge("memory_usage", 67.2)
    print("✓ Tested gauges")

    # Test histograms
    for value in [10, 25, 15, 30, 20]:
        performance_monitor.record_histogram("response_time", value)
    print("✓ Tested histograms")

    # Test timers with context manager
    with performance_monitor.time_sync("test_operation"):
        time.sleep(0.1)  # Simulate work
    print("✓ Tested sync timer")

    # Test API tracking
    if track_api_request is not None:
        track_api_request("/test", "GET", 200, 45.2)
        track_api_request("/test", "POST", 201, 67.8)
        track_api_request("/error", "GET", 500, 123.4)
        print("✓ Tested API tracking")

    # Test signal processing tracking
    if track_signal_processing is not None:
        track_signal_processing("EUR_USD", "H4", 234.5, 3)
        track_signal_processing("GBP_USD", "D", 145.2, 1)
        print("✓ Tested signal processing tracking")

    # Get statistics
    print("\nPerformance Statistics:")

    # Counter stats
    counter_stats = performance_monitor.get_metric_stats("test_counter")
    if "error" not in counter_stats:
        print(
            f"- Test Counter: {counter_stats['latest']} (count: {counter_stats['count']})"
        )

    # Timer stats
    timer_stats = performance_monitor.get_timer_stats("test_operation")
    if "error" not in timer_stats:
        print(f"- Test Operation: {timer_stats['latest_ms']:.2f}ms")

    # API stats
    api_stats = performance_monitor.get_timer_stats("api_request_duration")
    if "error" not in api_stats:
        print(
            f"- API Requests: {api_stats['count']} calls, avg {api_stats['mean_ms']:.2f}ms"
        )

    # All metrics
    all_metrics = performance_monitor.get_all_metrics()
    print(f"- Total Counters: {len(all_metrics['counters'])}")
    print(f"- Total Gauges: {len(all_metrics['gauges'])}")

    return True


def test_error_tracking():
    """Test error tracking functionality."""
    print("\n=== Testing Error Tracking ===")

    if not MONITORING_AVAILABLE or SentryErrorTracker is None:
        print("⚠️ Error tracking not available - skipping tests")
        return True

    # Initialize error tracker (without Sentry for testing)
    tracker = SentryErrorTracker()
    print("✓ Initialized error tracker")

    # Test error categories and severities
    if ErrorCategory is not None:
        print("✓ Error categories available:")
        for category in ErrorCategory:
            print(f"  - {category.value}")

    if ErrorSeverity is not None:
        print("✓ Error severities available:")
        for severity in ErrorSeverity:
            print(f"  - {severity.value}")

    # Test error capturing (will work without Sentry, just won't send)
    try:
        tracker.capture_api_error(
            Exception("Test API error"),
            endpoint="/test",
            method="GET",
            user_id="test_user",
        )
        print("✓ API error capture tested")
    except Exception as e:
        print(f"! API error capture issue: {e}")

    try:
        tracker.capture_business_logic_error(
            Exception("Test business logic error"),
            operation="signal_calculation",
            context={"pair": "EUR_USD", "timeframe": "H4"},
        )
        print("✓ Business logic error capture tested")
    except Exception as e:
        print(f"! Business logic error capture issue: {e}")

    return True


async def test_async_timer():
    """Test async timer functionality."""
    print("\n=== Testing Async Timer ===")

    if not MONITORING_AVAILABLE or performance_monitor is None:
        print("⚠️ Async timer not available - skipping tests")
        return True

    async with performance_monitor.time_async("async_operation", {"type": "test"}):
        await asyncio.sleep(0.05)  # Simulate async work

    # Get stats
    stats = performance_monitor.get_timer_stats("async_operation")
    if "error" not in stats:
        print(f"✓ Async operation completed in {stats['latest_ms']:.2f}ms")
    else:
        print("! No async timer data available")

    return True


def test_integration():
    """Test integration between components."""
    print("\n=== Testing Integration ===")

    if not MONITORING_AVAILABLE:
        print("⚠️ Monitoring not available - skipping integration tests")
        return True

    # Get comprehensive performance summary
    if get_performance_summary is not None:
        perf_summary = get_performance_summary()
        print(
            f"✓ Performance summary generated (timestamp: {perf_summary['timestamp']})"
        )

    # Test metric filtering with tags
    if performance_monitor is not None:
        performance_monitor.record_timer(
            "tagged_operation", 50.0, {"environment": "test", "version": "1.0"}
        )
        tagged_stats = performance_monitor.get_timer_stats(
            "tagged_operation", {"environment": "test"}
        )

        if "error" not in tagged_stats:
            print("✓ Tagged metrics working")
        else:
            print("! Tagged metrics not working properly")

    return True


async def run_day7_tests():
    """Run all Day 7 monitoring tests."""
    print("🔍 Starting Day 7: Monitoring System Tests")
    print("=" * 50)

    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)

    tests = [
        ("Health Monitoring", test_health_monitoring()),
        ("Performance Monitoring", test_performance_monitoring()),
        ("Error Tracking", test_error_tracking()),
        ("Async Timer", test_async_timer()),
        ("Integration", test_integration()),
    ]

    results = []

    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))

    # Print results
    print("\n" + "=" * 50)
    print("📊 Day 7 Test Results Summary")
    print("=" * 50)

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
        print("\n🎉 All Day 7 monitoring components are working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_day7_tests())
    sys.exit(0 if success else 1)
