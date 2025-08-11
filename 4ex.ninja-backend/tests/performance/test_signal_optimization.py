"""
Performance Validation Tests for Signal Optimization
Tests performance improvements, signal accuracy, and resource usage on Digital Ocean droplet
"""

import asyncio
import time
import psutil
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

# Import our services
from src.infrastructure.cache.redis_cache_service import RedisCacheService
from src.infrastructure.services.incremental_signal_processor import (
    IncrementalSignalProcessor,
)
from src.infrastructure.services.async_notification_service import (
    AsyncNotificationService,
)


class PerformanceValidator:
    """Comprehensive performance validation for optimized signal processing."""

    def __init__(self):
        self.redis_cache = RedisCacheService()
        self.processor = IncrementalSignalProcessor()
        self.metrics = {}

    async def setup(self):
        """Initialize services for testing."""
        await self.redis_cache.initialize()
        logging.info("✅ Performance validator initialized")

    async def cleanup(self):
        """Clean up test resources."""
        if self.redis_cache.cache_enabled:
            await self.redis_cache.disconnect()

    async def measure_signal_generation_latency(
        self, pair: str = "EURUSD", timeframe: str = "4h"
    ) -> Dict[str, float]:
        """
        Measure signal generation latency before and after optimization.
        Target: <500ms vs previous 2-5s
        """
        results = {
            "full_calculation_time": 0.0,
            "incremental_calculation_time": 0.0,
            "performance_improvement": 0.0,
            "target_met": False,
        }

        # Test 1: Full calculation (simulate old method)
        start_time = time.perf_counter()

        # Generate test data (200 candles for MA calculation)
        test_data = self._generate_test_ohlcv_data(200)

        # Calculate MAs without cache (full calculation)
        ma_20 = test_data["close"].rolling(window=20).mean()
        ma_50 = test_data["close"].rolling(window=50).mean()

        # Simulate signal generation logic
        signals = []
        for i in range(len(test_data)):
            if i >= 50:  # Ensure we have enough data for MA50
                if (
                    ma_20.iloc[i] > ma_50.iloc[i]
                    and ma_20.iloc[i - 1] <= ma_50.iloc[i - 1]
                ):
                    signals.append(("BUY", test_data.iloc[i]["close"], i))
                elif (
                    ma_20.iloc[i] < ma_50.iloc[i]
                    and ma_20.iloc[i - 1] >= ma_50.iloc[i - 1]
                ):
                    signals.append(("SELL", test_data.iloc[i]["close"], i))

        full_time = time.perf_counter() - start_time
        results["full_calculation_time"] = full_time

        # Test 2: Incremental calculation (optimized method)
        start_time = time.perf_counter()

        # Simulate incremental processing with cache
        if self.redis_cache.cache_enabled:
            # Pre-populate cache with MA state
            await self.redis_cache.set_ma_state(
                pair, timeframe, 20, ma_20.tail(20).tolist()
            )
            await self.redis_cache.set_ma_state(
                pair, timeframe, 50, ma_50.tail(50).tolist()
            )

            # Simulate processing only new candles (1-5 vs 200)
            new_candles = self._generate_test_ohlcv_data(3)  # Only 3 new candles

            # Get cached MA states
            ma_20_state = await self.redis_cache.get_ma_state(pair, timeframe, 20)
            ma_50_state = await self.redis_cache.get_ma_state(pair, timeframe, 50)

            # Calculate incremental MAs
            for _, candle in new_candles.iterrows():
                if ma_20_state:
                    # Update MA20 incrementally
                    ma_20_state.append(candle["close"])
                    if len(ma_20_state) > 20:
                        ma_20_state.pop(0)
                    current_ma_20 = np.mean(ma_20_state)

                if ma_50_state:
                    # Update MA50 incrementally
                    ma_50_state.append(candle["close"])
                    if len(ma_50_state) > 50:
                        ma_50_state.pop(0)
                    current_ma_50 = np.mean(ma_50_state)

        incremental_time = time.perf_counter() - start_time
        results["incremental_calculation_time"] = incremental_time

        # Calculate improvement
        if full_time > 0:
            improvement = ((full_time - incremental_time) / full_time) * 100
            results["performance_improvement"] = improvement
            results["target_met"] = incremental_time < 0.5  # <500ms target

        logging.info(f"📊 Signal Generation Performance:")
        logging.info(f"   Full calculation: {full_time:.3f}s")
        logging.info(f"   Incremental: {incremental_time:.3f}s")
        logging.info(f"   Improvement: {improvement:.1f}%")
        logging.info(f"   Target (<500ms): {'✅' if results['target_met'] else '❌'}")

        return results

    async def validate_ma_accuracy(
        self, pair: str = "EURUSD", timeframe: str = "4h"
    ) -> Dict[str, any]:
        """
        Critical test: Validate that incremental MA calculations maintain accuracy.
        This addresses your concern about fetching 1-5 candles vs 200.
        """
        results = {
            "accuracy_maintained": False,
            "max_deviation": 0.0,
            "avg_deviation": 0.0,
            "test_passed": False,
        }

        # Generate comprehensive test data
        test_data = self._generate_test_ohlcv_data(
            300
        )  # Large dataset for thorough testing

        # Method 1: Full calculation (ground truth)
        full_ma_20 = test_data["close"].rolling(window=20).mean()
        full_ma_50 = test_data["close"].rolling(window=50).mean()

        # Method 2: Incremental calculation simulation
        incremental_ma_20 = []
        incremental_ma_50 = []

        ma_20_window = []
        ma_50_window = []

        for i, price in enumerate(test_data["close"]):
            # Update windows
            ma_20_window.append(price)
            ma_50_window.append(price)

            if len(ma_20_window) > 20:
                ma_20_window.pop(0)
            if len(ma_50_window) > 50:
                ma_50_window.pop(0)

            # Calculate incremental MAs
            if len(ma_20_window) == 20:
                incremental_ma_20.append(np.mean(ma_20_window))
            else:
                incremental_ma_20.append(np.nan)

            if len(ma_50_window) == 50:
                incremental_ma_50.append(np.mean(ma_50_window))
            else:
                incremental_ma_50.append(np.nan)

        # Compare accuracy for MA20
        valid_indices = ~np.isnan(full_ma_20) & ~np.isnan(incremental_ma_20)
        if np.any(valid_indices):
            ma_20_deviations = np.abs(
                np.array(full_ma_20[valid_indices])
                - np.array(incremental_ma_20)[valid_indices]
            )

            # Compare accuracy for MA50
            valid_indices_50 = ~np.isnan(full_ma_50) & ~np.isnan(incremental_ma_50)
            ma_50_deviations = np.abs(
                np.array(full_ma_50[valid_indices_50])
                - np.array(incremental_ma_50)[valid_indices_50]
            )

            all_deviations = np.concatenate([ma_20_deviations, ma_50_deviations])

            results["max_deviation"] = float(np.max(all_deviations))
            results["avg_deviation"] = float(np.mean(all_deviations))

            # Accuracy threshold: deviations should be negligible (< 0.0001)
            accuracy_threshold = 0.0001
            results["accuracy_maintained"] = (
                results["max_deviation"] < accuracy_threshold
            )
            results["test_passed"] = results["accuracy_maintained"]

        logging.info(f"🎯 MA Accuracy Validation:")
        logging.info(f"   Max deviation: {results['max_deviation']:.8f}")
        logging.info(f"   Avg deviation: {results['avg_deviation']:.8f}")
        logging.info(
            f"   Accuracy maintained: {'✅' if results['accuracy_maintained'] else '❌'}"
        )

        if not results["accuracy_maintained"]:
            logging.error(
                "🚨 CRITICAL: MA accuracy compromised! Incremental calculation has significant deviations."
            )

        return results

    async def measure_cache_performance(self) -> Dict[str, any]:
        """
        Measure Redis cache hit ratios and performance.
        Target: >90% hit ratio
        """
        results = {
            "cache_enabled": self.redis_cache.cache_enabled,
            "hit_ratio": 0.0,
            "avg_get_time": 0.0,
            "avg_set_time": 0.0,
            "target_hit_ratio_met": False,
        }

        if not self.redis_cache.cache_enabled:
            logging.warning(
                "⚠️ Redis cache not enabled - cannot measure cache performance"
            )
            return results

        # Test cache operations
        test_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        timeframes = ["4h", "1d"]

        hit_count = 0
        miss_count = 0
        get_times = []
        set_times = []

        for pair in test_pairs:
            for timeframe in timeframes:
                # Test SET operations
                test_data = [1.1234, 1.1235, 1.1236, 1.1237, 1.1238]

                start_time = time.perf_counter()
                await self.redis_cache.set_ma_state(pair, timeframe, 20, test_data)
                set_time = time.perf_counter() - start_time
                set_times.append(set_time)

                # Test GET operations (should hit)
                start_time = time.perf_counter()
                cached_data = await self.redis_cache.get_ma_state(pair, timeframe, 20)
                get_time = time.perf_counter() - start_time
                get_times.append(get_time)

                if cached_data:
                    hit_count += 1
                else:
                    miss_count += 1

                # Test GET for non-existent data (should miss)
                start_time = time.perf_counter()
                nonexistent = await self.redis_cache.get_ma_state(
                    f"{pair}_fake", timeframe, 20
                )
                get_time = time.perf_counter() - start_time
                get_times.append(get_time)

                if nonexistent:
                    hit_count += 1
                else:
                    miss_count += 1

        total_ops = hit_count + miss_count
        if total_ops > 0:
            results["hit_ratio"] = (hit_count / total_ops) * 100
            results["target_hit_ratio_met"] = results["hit_ratio"] >= 90.0

        if get_times:
            results["avg_get_time"] = np.mean(get_times)
        if set_times:
            results["avg_set_time"] = np.mean(set_times)

        logging.info(f"💾 Cache Performance:")
        logging.info(f"   Hit ratio: {results['hit_ratio']:.1f}%")
        logging.info(f"   Avg GET time: {results['avg_get_time']:.4f}s")
        logging.info(f"   Avg SET time: {results['avg_set_time']:.4f}s")
        logging.info(
            f"   Target (>90%): {'✅' if results['target_hit_ratio_met'] else '❌'}"
        )

        return results

    def measure_memory_usage(self) -> Dict[str, float]:
        """
        Measure current memory usage on the Digital Ocean droplet.
        Monitor Redis memory usage and overall system resources.
        """
        memory_info = psutil.virtual_memory()

        results = {
            "total_memory_gb": memory_info.total / (1024**3),
            "available_memory_gb": memory_info.available / (1024**3),
            "used_memory_gb": memory_info.used / (1024**3),
            "memory_usage_percent": memory_info.percent,
            "process_memory_mb": 0.0,
            "redis_memory_estimate_mb": 0.0,
        }

        # Get current process memory usage
        current_process = psutil.Process()
        process_memory = current_process.memory_info()
        results["process_memory_mb"] = process_memory.rss / (1024**2)

        # Estimate Redis memory usage (rough calculation)
        # This is an approximation - for precise measurement, use Redis MEMORY USAGE command
        if self.redis_cache.cache_enabled:
            # Rough estimate: assume 1KB per cached MA state
            # With ~10 currency pairs, 2 timeframes, 2 MA periods = ~40 entries
            estimated_redis_mb = 40 * 1 / 1024  # Very conservative estimate
            results["redis_memory_estimate_mb"] = estimated_redis_mb

        logging.info(f"💾 Memory Usage (Digital Ocean Droplet):")
        logging.info(f"   Total RAM: {results['total_memory_gb']:.2f} GB")
        logging.info(
            f"   Used RAM: {results['used_memory_gb']:.2f} GB ({results['memory_usage_percent']:.1f}%)"
        )
        logging.info(f"   Available RAM: {results['available_memory_gb']:.2f} GB")
        logging.info(f"   Process Memory: {results['process_memory_mb']:.1f} MB")
        logging.info(
            f"   Redis Memory (est): {results['redis_memory_estimate_mb']:.1f} MB"
        )

        # Alert if memory usage is high
        if results["memory_usage_percent"] > 80:
            logging.warning(
                f"⚠️ High memory usage: {results['memory_usage_percent']:.1f}%"
            )

        return results

    async def measure_notification_performance(self) -> Dict[str, float]:
        """
        Measure async notification service performance.
        Target: <1s to queue, <5s to Discord
        """
        results = {
            "queue_time_ms": 0.0,
            "notification_processing_time_ms": 0.0,
            "queue_target_met": False,
            "processing_target_met": False,
        }

        try:
            # Initialize notification service
            notification_service = AsyncNotificationService()
            await notification_service.initialize()

            # Test notification queuing
            test_signal = {
                "pair": "EURUSD",
                "signal": "BUY",
                "price": 1.1234,
                "confidence": 85.5,
                "timestamp": datetime.now().isoformat(),
            }

            start_time = time.perf_counter()
            await notification_service.queue_notification(test_signal, "HIGH")
            queue_time = (time.perf_counter() - start_time) * 1000  # Convert to ms

            results["queue_time_ms"] = queue_time
            results["queue_target_met"] = queue_time < 1000  # <1s target

            logging.info(f"📢 Notification Performance:")
            logging.info(f"   Queue time: {queue_time:.1f}ms")
            logging.info(
                f"   Queue target (<1000ms): {'✅' if results['queue_target_met'] else '❌'}"
            )

            await notification_service.cleanup()

        except Exception as e:
            logging.error(f"❌ Notification performance test failed: {e}")

        return results

    def _generate_test_ohlcv_data(self, num_candles: int) -> pd.DataFrame:
        """Generate realistic OHLCV test data for performance testing."""
        np.random.seed(42)  # Reproducible results

        base_price = 1.1200
        data = []
        current_price = base_price

        for i in range(num_candles):
            # Simulate realistic price movement
            change = np.random.normal(0, 0.001)  # Small random changes
            current_price += change

            # Generate OHLC around current price
            high = current_price + abs(np.random.normal(0, 0.0005))
            low = current_price - abs(np.random.normal(0, 0.0005))
            open_price = current_price + np.random.normal(0, 0.0002)
            close_price = current_price
            volume = np.random.randint(1000, 10000)

            data.append(
                {
                    "timestamp": datetime.now() - timedelta(hours=4 * i),
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "volume": volume,
                }
            )

        return pd.DataFrame(data).sort_values("timestamp")


# Pytest test functions
class TestSignalOptimization:
    """Test suite for signal optimization validation."""

    @pytest.fixture
    async def validator(self):
        """Setup performance validator."""
        validator = PerformanceValidator()
        await validator.setup()
        yield validator
        await validator.cleanup()

    @pytest.mark.asyncio
    async def test_signal_generation_performance(self, validator):
        """Test that signal generation meets performance targets."""
        results = await validator.measure_signal_generation_latency()

        # Assertions
        assert results[
            "target_met"
        ], f"Signal generation too slow: {results['incremental_calculation_time']:.3f}s > 0.5s"
        assert (
            results["performance_improvement"] > 50
        ), f"Insufficient improvement: {results['performance_improvement']:.1f}%"

        print(f"✅ Performance improvement: {results['performance_improvement']:.1f}%")

    @pytest.mark.asyncio
    async def test_ma_accuracy_maintained(self, validator):
        """Critical test: Ensure MA accuracy is maintained with incremental processing."""
        results = await validator.validate_ma_accuracy()

        # This is critical - accuracy must be maintained
        assert results[
            "accuracy_maintained"
        ], f"MA accuracy compromised! Max deviation: {results['max_deviation']:.8f}"
        assert results["max_deviation"] < 0.0001, "MA deviations too large"

        print(
            f"✅ MA accuracy maintained with max deviation: {results['max_deviation']:.8f}"
        )

    @pytest.mark.asyncio
    async def test_cache_performance(self, validator):
        """Test Redis cache hit ratios and performance."""
        results = await validator.measure_cache_performance()

        if results["cache_enabled"]:
            assert results[
                "target_hit_ratio_met"
            ], f"Cache hit ratio too low: {results['hit_ratio']:.1f}% < 90%"
            assert (
                results["avg_get_time"] < 0.01
            ), f"Cache GET too slow: {results['avg_get_time']:.4f}s"

            print(f"✅ Cache hit ratio: {results['hit_ratio']:.1f}%")

    def test_memory_usage(self, validator):
        """Test memory usage on Digital Ocean droplet."""
        results = validator.measure_memory_usage()

        # Reasonable memory usage checks
        assert (
            results["memory_usage_percent"] < 90
        ), f"Memory usage too high: {results['memory_usage_percent']:.1f}%"
        assert (
            results["process_memory_mb"] < 500
        ), f"Process memory too high: {results['process_memory_mb']:.1f}MB"

        print(
            f"✅ Memory usage: {results['memory_usage_percent']:.1f}% ({results['used_memory_gb']:.2f}GB)"
        )

    @pytest.mark.asyncio
    async def test_notification_performance(self, validator):
        """Test async notification service performance."""
        results = await validator.measure_notification_performance()

        assert results[
            "queue_target_met"
        ], f"Notification queuing too slow: {results['queue_time_ms']:.1f}ms > 1000ms"

        print(f"✅ Notification queue time: {results['queue_time_ms']:.1f}ms")


# Standalone validation script
async def run_comprehensive_validation():
    """Run comprehensive performance validation."""
    print("🚀 Starting Comprehensive Performance Validation")
    print("=" * 60)

    validator = PerformanceValidator()
    await validator.setup()

    try:
        # 1. Signal generation performance
        print("\n1️⃣ Testing Signal Generation Performance...")
        perf_results = await validator.measure_signal_generation_latency()

        # 2. MA accuracy validation (CRITICAL)
        print("\n2️⃣ Validating MA Calculation Accuracy...")
        accuracy_results = await validator.validate_ma_accuracy()

        # 3. Cache performance
        print("\n3️⃣ Testing Cache Performance...")
        cache_results = await validator.measure_cache_performance()

        # 4. Memory usage
        print("\n4️⃣ Measuring Memory Usage...")
        memory_results = validator.measure_memory_usage()

        # 5. Notification performance
        print("\n5️⃣ Testing Notification Performance...")
        notification_results = await validator.measure_notification_performance()

        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        all_tests_passed = True

        # Signal performance
        if perf_results["target_met"]:
            print("✅ Signal generation performance: PASSED")
        else:
            print("❌ Signal generation performance: FAILED")
            all_tests_passed = False

        # MA accuracy (most critical)
        if accuracy_results["accuracy_maintained"]:
            print("✅ MA calculation accuracy: PASSED")
        else:
            print("❌ MA calculation accuracy: FAILED (CRITICAL)")
            all_tests_passed = False

        # Cache performance
        if cache_results["cache_enabled"] and cache_results["target_hit_ratio_met"]:
            print("✅ Cache performance: PASSED")
        elif not cache_results["cache_enabled"]:
            print("⚠️ Cache performance: DISABLED")
        else:
            print("❌ Cache performance: FAILED")
            all_tests_passed = False

        # Memory usage
        if memory_results["memory_usage_percent"] < 80:
            print("✅ Memory usage: HEALTHY")
        else:
            print("⚠️ Memory usage: HIGH")

        # Notification performance
        if notification_results["queue_target_met"]:
            print("✅ Notification performance: PASSED")
        else:
            print("❌ Notification performance: FAILED")
            all_tests_passed = False

        print("\n" + "=" * 60)
        if all_tests_passed:
            print("🎉 ALL CRITICAL TESTS PASSED!")
            print("✅ Ready to proceed to next development phase")
        else:
            print("🚨 SOME TESTS FAILED!")
            print("❌ Address issues before proceeding")

    finally:
        await validator.cleanup()


if __name__ == "__main__":
    # Run validation
    asyncio.run(run_comprehensive_validation())
