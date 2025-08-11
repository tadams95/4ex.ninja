#!/usr/bin/env python3
"""
Quick Performance and Accuracy Validation Script
Run this on your Digital Ocean droplet to validate optimizations
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from tests.performance.test_signal_optimization import PerformanceValidator
    from src.infrastructure.monitoring.memory_monitor import MemoryMonitor
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the 4ex.ninja-backend directory")
    sys.exit(1)


async def run_quick_validation():
    """Run a quick validation of all optimizations."""
    print("🚀 4EX.NINJA PERFORMANCE VALIDATION")
    print("=" * 50)
    print("Testing signal optimization improvements...")
    print()

    # Initialize validators
    performance_validator = PerformanceValidator()
    memory_monitor = MemoryMonitor()

    try:
        # Setup
        print("🔧 Initializing services...")
        await performance_validator.setup()
        await memory_monitor.initialize()
        print("✅ Services initialized\n")

        # 1. Critical MA Accuracy Test
        print("1️⃣ TESTING MA CALCULATION ACCURACY (CRITICAL)")
        print("-" * 40)
        accuracy_results = await performance_validator.validate_ma_accuracy()

        if accuracy_results["accuracy_maintained"]:
            print(
                f"✅ MA accuracy maintained (max deviation: {accuracy_results['max_deviation']:.8f})"
            )
        else:
            print(
                f"❌ CRITICAL: MA accuracy compromised! Max deviation: {accuracy_results['max_deviation']:.8f}"
            )
            print("🚨 This means your signals may be inaccurate!")
        print()

        # 2. Performance Test
        print("2️⃣ TESTING SIGNAL GENERATION PERFORMANCE")
        print("-" * 40)
        perf_results = await performance_validator.measure_signal_generation_latency()

        print(f"📊 Full calculation: {perf_results['full_calculation_time']:.3f}s")
        print(f"📊 Incremental: {perf_results['incremental_calculation_time']:.3f}s")
        print(f"📊 Improvement: {perf_results['performance_improvement']:.1f}%")

        if perf_results["target_met"]:
            print("✅ Performance target met (<500ms)")
        else:
            print("❌ Performance target not met")
        print()

        # 3. Cache Performance
        print("3️⃣ TESTING REDIS CACHE PERFORMANCE")
        print("-" * 40)
        cache_results = await performance_validator.measure_cache_performance()

        if cache_results["cache_enabled"]:
            print(f"📊 Hit ratio: {cache_results['hit_ratio']:.1f}%")
            print(f"📊 Avg GET time: {cache_results['avg_get_time']:.4f}s")

            if cache_results["target_hit_ratio_met"]:
                print("✅ Cache performance excellent")
            else:
                print("⚠️ Cache hit ratio below target")
        else:
            print("❌ Redis cache not available")
        print()

        # 4. Memory Usage
        print("4️⃣ CHECKING MEMORY USAGE")
        print("-" * 40)
        memory_results = memory_monitor.measure_memory_usage()

        print(
            f"📊 System memory: {memory_results['memory_usage_percent']:.1f}% ({memory_results['used_memory_gb']:.2f}GB)"
        )
        print(f"📊 Process memory: {memory_results['process_memory_mb']:.1f}MB")
        print(f"📊 Redis memory: {memory_results['redis_memory_estimate_mb']:.1f}MB")

        if memory_results["memory_usage_percent"] < 80:
            print("✅ Memory usage healthy")
        else:
            print("⚠️ Memory usage high")
        print()

        # 5. Notification Performance
        print("5️⃣ TESTING NOTIFICATION PERFORMANCE")
        print("-" * 40)
        notification_results = (
            await performance_validator.measure_notification_performance()
        )

        print(f"📊 Queue time: {notification_results['queue_time_ms']:.1f}ms")

        if notification_results["queue_target_met"]:
            print("✅ Notification performance excellent")
        else:
            print("❌ Notification performance needs improvement")
        print()

        # Summary
        print("=" * 50)
        print("📋 VALIDATION SUMMARY")
        print("=" * 50)

        tests_passed = 0
        total_tests = 5

        if accuracy_results["accuracy_maintained"]:
            print("✅ MA Accuracy: PASSED")
            tests_passed += 1
        else:
            print("❌ MA Accuracy: FAILED (CRITICAL)")

        if perf_results["target_met"]:
            print("✅ Performance: PASSED")
            tests_passed += 1
        else:
            print("❌ Performance: FAILED")

        if cache_results["cache_enabled"] and cache_results["target_hit_ratio_met"]:
            print("✅ Cache: PASSED")
            tests_passed += 1
        elif cache_results["cache_enabled"]:
            print("⚠️ Cache: MARGINAL")
            tests_passed += 0.5
        else:
            print("❌ Cache: DISABLED")

        if memory_results["memory_usage_percent"] < 80:
            print("✅ Memory: HEALTHY")
            tests_passed += 1
        else:
            print("⚠️ Memory: HIGH")
            tests_passed += 0.5

        if notification_results["queue_target_met"]:
            print("✅ Notifications: PASSED")
            tests_passed += 1
        else:
            print("❌ Notifications: FAILED")

        print(
            f"\n🎯 OVERALL SCORE: {tests_passed}/{total_tests} ({(tests_passed/total_tests)*100:.0f}%)"
        )

        if tests_passed >= 4:
            print("🎉 EXCELLENT! Your optimizations are working great!")
            print("✅ Ready to proceed to next development phase")
        elif tests_passed >= 3:
            print("✅ GOOD! Most optimizations working, minor issues to address")
        else:
            print("⚠️ ISSUES DETECTED! Address problems before proceeding")

        # Specific recommendations
        print("\n📝 RECOMMENDATIONS:")
        if not accuracy_results["accuracy_maintained"]:
            print("🚨 CRITICAL: Fix MA accuracy issue immediately!")
            print("   - Check Redis cache is properly storing MA states")
            print("   - Verify incremental calculation logic")

        if not perf_results["target_met"]:
            print("⚡ Optimize signal generation performance")
            print("   - Check Redis connection latency")
            print("   - Profile bottlenecks in signal processing")

        if not cache_results["cache_enabled"]:
            print("💾 Enable Redis cache for performance gains")
            print("   - Install Redis: sudo apt install redis-server")
            print("   - Start Redis: sudo systemctl start redis")

        if memory_results["memory_usage_percent"] > 80:
            print("🧠 Consider upgrading Digital Ocean droplet")
            print("   - Current usage is high, may impact performance")

    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        await performance_validator.cleanup()


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []

    try:
        import redis
    except ImportError:
        missing_deps.append("redis")

    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")

    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")

    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nInstall with: pip install " + " ".join(missing_deps))
        return False

    return True


if __name__ == "__main__":
    print("🔍 Checking dependencies...")

    if not check_dependencies():
        sys.exit(1)

    print("✅ Dependencies OK\n")

    try:
        asyncio.run(run_quick_validation())
    except KeyboardInterrupt:
        print("\n👋 Validation stopped by user")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
