"""
Performance Testing and Load Validation for Day 7 Task 1.5.28

This module provides comprehensive performance testing and load validation
for repository operations, entity processing, and system scalability.
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import statistics
import concurrent.futures
from dataclasses import dataclass, asdict

from ...core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from ...core.entities.market_data import MarketData, Candle, Granularity

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""

    operation_name: str
    total_operations: int
    duration_seconds: float
    operations_per_second: float
    min_operation_time: float
    max_operation_time: float
    avg_operation_time: float
    median_operation_time: float
    p95_operation_time: float
    memory_usage_mb: Optional[float] = None
    errors_count: int = 0
    success_rate: float = 100.0


class PerformanceBenchmark:
    """
    Performance benchmarking utilities for entity operations.

    Provides comprehensive performance testing capabilities including
    load testing, stress testing, and scalability validation.
    """

    def __init__(self):
        """Initialize performance benchmark."""
        self.results = []

    async def benchmark_operation(
        self, operation: Callable, operation_name: str, iterations: int = 1000, **kwargs
    ) -> PerformanceMetrics:
        """
        Benchmark a specific operation.

        Args:
            operation: Async function to benchmark
            operation_name: Name of the operation for reporting
            iterations: Number of iterations to run
            **kwargs: Arguments to pass to the operation

        Returns:
            Performance metrics for the operation
        """
        operation_times = []
        errors = 0

        start_time = time.time()

        for i in range(iterations):
            try:
                op_start = time.time()

                if asyncio.iscoroutinefunction(operation):
                    await operation(**kwargs)
                else:
                    operation(**kwargs)

                op_end = time.time()
                operation_times.append(op_end - op_start)

            except Exception as e:
                errors += 1
                logger.warning(
                    f"Operation {operation_name} failed on iteration {i}: {e}"
                )

        end_time = time.time()
        total_duration = end_time - start_time

        if operation_times:
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                total_operations=iterations,
                duration_seconds=total_duration,
                operations_per_second=len(operation_times) / total_duration,
                min_operation_time=min(operation_times),
                max_operation_time=max(operation_times),
                avg_operation_time=statistics.mean(operation_times),
                median_operation_time=statistics.median(operation_times),
                p95_operation_time=self._calculate_percentile(operation_times, 95),
                errors_count=errors,
                success_rate=((iterations - errors) / iterations) * 100,
            )
        else:
            # All operations failed
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                total_operations=iterations,
                duration_seconds=total_duration,
                operations_per_second=0,
                min_operation_time=0,
                max_operation_time=0,
                avg_operation_time=0,
                median_operation_time=0,
                p95_operation_time=0,
                errors_count=errors,
                success_rate=0.0,
            )

        self.results.append(metrics)
        return metrics

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100.0))
        return sorted_values[min(index, len(sorted_values) - 1)]

    async def stress_test_operation(
        self,
        operation: Callable,
        operation_name: str,
        max_concurrent: int = 100,
        duration_seconds: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Stress test an operation with increasing concurrent load.

        Args:
            operation: Operation to stress test
            operation_name: Name for reporting
            max_concurrent: Maximum concurrent operations
            duration_seconds: Duration to run the test
            **kwargs: Arguments for the operation

        Returns:
            Stress test results
        """
        results = {
            "operation_name": operation_name,
            "test_duration": duration_seconds,
            "max_concurrent": max_concurrent,
            "load_levels": [],
            "peak_performance": 0,
            "degradation_point": None,
        }

        # Test with increasing concurrency levels
        for concurrent_level in [1, 5, 10, 25, 50, max_concurrent]:
            if concurrent_level > max_concurrent:
                break

            logger.info(
                f"Testing {operation_name} with {concurrent_level} concurrent operations"
            )

            # Run stress test at this concurrency level
            level_result = await self._run_concurrent_operations(
                operation, concurrent_level, duration_seconds, **kwargs
            )

            level_result["concurrent_level"] = concurrent_level
            results["load_levels"].append(level_result)

            # Track peak performance
            if level_result["operations_per_second"] > results["peak_performance"]:
                results["peak_performance"] = level_result["operations_per_second"]

            # Detect performance degradation
            if (
                results["peak_performance"] > 0
                and level_result["operations_per_second"]
                < results["peak_performance"] * 0.8
            ):
                if results["degradation_point"] is None:
                    results["degradation_point"] = concurrent_level

        return results

    async def _run_concurrent_operations(
        self,
        operation: Callable,
        concurrent_count: int,
        duration_seconds: int,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run concurrent operations for specified duration."""
        start_time = time.time()
        end_time = start_time + duration_seconds

        completed_operations = 0
        failed_operations = 0
        operation_times = []

        async def worker():
            nonlocal completed_operations, failed_operations

            while time.time() < end_time:
                try:
                    op_start = time.time()

                    if asyncio.iscoroutinefunction(operation):
                        await operation(**kwargs)
                    else:
                        operation(**kwargs)

                    op_end = time.time()
                    operation_times.append(op_end - op_start)
                    completed_operations += 1

                except Exception as e:
                    failed_operations += 1

        # Start concurrent workers
        tasks = [worker() for _ in range(concurrent_count)]
        await asyncio.gather(*tasks, return_exceptions=True)

        actual_duration = time.time() - start_time

        return {
            "duration": actual_duration,
            "completed_operations": completed_operations,
            "failed_operations": failed_operations,
            "operations_per_second": (
                completed_operations / actual_duration if actual_duration > 0 else 0
            ),
            "avg_operation_time": (
                statistics.mean(operation_times) if operation_times else 0
            ),
            "error_rate": (
                (failed_operations / (completed_operations + failed_operations)) * 100
                if (completed_operations + failed_operations) > 0
                else 0
            ),
        }


class EntityPerformanceTests:
    """Performance tests for entity operations."""

    def __init__(self):
        """Initialize entity performance tests."""
        self.benchmark = PerformanceBenchmark()

    async def test_signal_creation_performance(self) -> PerformanceMetrics:
        """Test performance of signal creation."""

        def create_test_signal():
            return Signal(
                signal_id=f"perf_signal_{time.time()}_{id(object())}",
                pair="EUR/USD",
                timeframe="H1",
                signal_type=SignalType.BUY,
                crossover_type=CrossoverType.BULLISH,
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1000"),
                fast_ma=10,
                slow_ma=20,
                timestamp=datetime.utcnow(),
            )

        return await self.benchmark.benchmark_operation(
            operation=create_test_signal,
            operation_name="signal_creation",
            iterations=10000,
        )

    async def test_signal_calculation_performance(self) -> PerformanceMetrics:
        """Test performance of signal calculations."""

        # Create test signal
        test_signal = Signal(
            signal_id="calc_test_signal",
            pair="EUR/USD",
            timeframe="H1",
            signal_type=SignalType.BUY,
            crossover_type=CrossoverType.BULLISH,
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1050"),
            fast_ma=10,
            slow_ma=20,
            timestamp=datetime.utcnow(),
            stop_loss=Decimal("1.0950"),
            take_profit=Decimal("1.1100"),
        )

        def perform_calculations():
            # Test various calculations
            test_signal.calculate_risk_reward_ratio()
            test_signal.is_profitable()
            test_signal.get_pnl()
            test_signal.should_stop_loss()
            test_signal.should_take_profit()

            # Update price and recalculate
            new_price = Decimal("1.1025")
            test_signal.update_current_price(new_price)

            return test_signal

        return await self.benchmark.benchmark_operation(
            operation=perform_calculations,
            operation_name="signal_calculations",
            iterations=50000,
        )

    async def test_candle_processing_performance(self) -> PerformanceMetrics:
        """Test performance of candle processing."""

        def create_and_process_candle():
            candle = Candle(
                time=datetime.utcnow(),
                open=Decimal("1.1000"),
                high=Decimal("1.1010"),
                low=Decimal("1.0990"),
                close=Decimal("1.1005"),
                volume=50000,
            )

            # Perform various calculations
            candle.is_bullish()
            candle.is_bearish()
            candle.body_size()
            candle.upper_shadow()
            candle.lower_shadow()
            candle.total_range()
            candle.typical_price()
            candle.weighted_close()

            return candle

        return await self.benchmark.benchmark_operation(
            operation=create_and_process_candle,
            operation_name="candle_processing",
            iterations=100000,
        )

    async def test_market_data_processing_performance(self) -> PerformanceMetrics:
        """Test performance of market data processing with large datasets."""

        def create_and_process_market_data():
            # Create large candle dataset
            candles = []
            base_time = datetime.utcnow()

            for i in range(1000):  # 1000 candles
                candle = Candle(
                    time=base_time + timedelta(minutes=i),
                    open=Decimal("1.1000") + Decimal(str((i % 100) * 0.0001)),
                    high=Decimal("1.1010") + Decimal(str((i % 100) * 0.0001)),
                    low=Decimal("1.0990") + Decimal(str((i % 100) * 0.0001)),
                    close=Decimal("1.1005") + Decimal(str((i % 100) * 0.0001)),
                    volume=50000 + (i * 10),
                )
                candles.append(candle)

            # Create market data
            market_data = MarketData(
                instrument="EUR/USD", granularity=Granularity.H1, candles=candles
            )

            # Perform various operations
            market_data.get_latest_candle()
            market_data.get_recent_candles(100)
            market_data.get_closes(50)
            market_data.get_highs(50)
            market_data.get_lows(50)
            market_data.get_volumes(50)
            market_data.calculate_sma(20)

            return market_data

        return await self.benchmark.benchmark_operation(
            operation=create_and_process_market_data,
            operation_name="market_data_processing",
            iterations=100,
        )

    async def test_bulk_operations_performance(self) -> PerformanceMetrics:
        """Test performance of bulk operations."""

        def create_bulk_signals():
            signals = []

            for i in range(100):
                signal = Signal(
                    signal_id=f"bulk_signal_{i}",
                    pair=["EUR/USD", "GBP/USD", "USD/JPY"][i % 3],
                    timeframe="H1",
                    signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                    crossover_type=(
                        CrossoverType.BULLISH if i % 2 == 0 else CrossoverType.BEARISH
                    ),
                    entry_price=Decimal("1.1000") + Decimal(str(i * 0.0001)),
                    current_price=Decimal("1.1000") + Decimal(str(i * 0.0001)),
                    fast_ma=10,
                    slow_ma=20,
                    timestamp=datetime.utcnow(),
                )
                signals.append(signal)

            # Process all signals
            for signal in signals:
                signal.calculate_risk_reward_ratio()
                signal.is_profitable()
                signal.get_pnl()

            return signals

        return await self.benchmark.benchmark_operation(
            operation=create_bulk_signals,
            operation_name="bulk_operations",
            iterations=1000,
        )


class LoadTestingScenarios:
    """Load testing scenarios for system validation."""

    def __init__(self):
        """Initialize load testing scenarios."""
        self.benchmark = PerformanceBenchmark()

    async def test_concurrent_signal_processing(self) -> Dict[str, Any]:
        """Test concurrent signal processing under load."""

        def process_signal():
            signal = Signal(
                signal_id=f"load_test_{time.time()}_{id(object())}",
                pair="EUR/USD",
                timeframe="H1",
                signal_type=SignalType.BUY,
                crossover_type=CrossoverType.BULLISH,
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1050"),
                fast_ma=10,
                slow_ma=20,
                timestamp=datetime.utcnow(),
                stop_loss=Decimal("1.0950"),
                take_profit=Decimal("1.1100"),
            )

            # Perform calculations
            signal.calculate_risk_reward_ratio()
            signal.is_profitable()
            signal.get_pnl()

            return signal

        return await self.benchmark.stress_test_operation(
            operation=process_signal,
            operation_name="concurrent_signal_processing",
            max_concurrent=50,
            duration_seconds=30,
        )

    async def test_memory_intensive_operations(self) -> Dict[str, Any]:
        """Test memory-intensive operations."""

        def memory_intensive_operation():
            # Create large dataset in memory
            large_signals = []

            for i in range(10000):  # 10k signals
                signal = Signal(
                    signal_id=f"memory_test_{i}",
                    pair="EUR/USD",
                    timeframe="H1",
                    signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                    crossover_type=(
                        CrossoverType.BULLISH if i % 2 == 0 else CrossoverType.BEARISH
                    ),
                    entry_price=Decimal("1.1000") + Decimal(str(i * 0.0001)),
                    current_price=Decimal("1.1000") + Decimal(str(i * 0.0001)),
                    fast_ma=10,
                    slow_ma=20,
                    timestamp=datetime.utcnow(),
                )
                large_signals.append(signal)

            # Process all signals
            for signal in large_signals:
                signal.calculate_risk_reward_ratio()

            return len(large_signals)

        return await self.benchmark.stress_test_operation(
            operation=memory_intensive_operation,
            operation_name="memory_intensive_operations",
            max_concurrent=10,
            duration_seconds=20,
        )

    async def test_sustained_load(self) -> Dict[str, Any]:
        """Test sustained load over extended period."""

        def sustained_operation():
            # Simulate realistic trading operation
            signal = Signal(
                signal_id=f"sustained_{time.time()}",
                pair="EUR/USD",
                timeframe="H1",
                signal_type=SignalType.BUY,
                crossover_type=CrossoverType.BULLISH,
                entry_price=Decimal("1.1000"),
                current_price=Decimal("1.1025"),
                fast_ma=10,
                slow_ma=20,
                timestamp=datetime.utcnow(),
            )

            # Multiple operations
            signal.calculate_risk_reward_ratio()
            signal.is_profitable()
            signal.get_pnl()

            # Update price multiple times
            for i in range(10):
                new_price = signal.current_price + Decimal("0.0001")
                signal.update_current_price(new_price)
                signal.is_profitable()

            return signal

        return await self.benchmark.stress_test_operation(
            operation=sustained_operation,
            operation_name="sustained_load",
            max_concurrent=25,
            duration_seconds=60,  # 1 minute sustained test
        )


class PerformanceTestSuite:
    """Comprehensive performance test suite."""

    def __init__(self):
        """Initialize performance test suite."""
        self.entity_tests = EntityPerformanceTests()
        self.load_tests = LoadTestingScenarios()

    async def run_all_performance_tests(self) -> Dict[str, Any]:
        """
        Run all performance and load tests.

        Returns:
            Comprehensive performance test results
        """
        results = {
            "test_suite": "Performance Testing and Load Validation",
            "test_run_timestamp": datetime.utcnow().isoformat(),
            "performance_benchmarks": [],
            "load_test_results": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "performance_issues": [],
            },
        }

        # Run performance benchmarks
        benchmark_tests = [
            self.entity_tests.test_signal_creation_performance,
            self.entity_tests.test_signal_calculation_performance,
            self.entity_tests.test_candle_processing_performance,
            self.entity_tests.test_market_data_processing_performance,
            self.entity_tests.test_bulk_operations_performance,
        ]

        for test_method in benchmark_tests:
            try:
                benchmark_result = await test_method()
                results["performance_benchmarks"].append(asdict(benchmark_result))
                results["summary"]["total_tests"] += 1

                # Check performance thresholds
                if self._meets_performance_criteria(benchmark_result):
                    results["summary"]["passed_tests"] += 1
                else:
                    results["summary"]["failed_tests"] += 1
                    results["summary"]["performance_issues"].append(
                        f"{benchmark_result.operation_name}: {benchmark_result.operations_per_second:.1f} ops/sec"
                    )

            except Exception as e:
                results["summary"]["total_tests"] += 1
                results["summary"]["failed_tests"] += 1
                results["summary"]["performance_issues"].append(
                    f"{test_method.__name__}: {str(e)}"
                )

        # Run load tests
        load_test_methods = [
            self.load_tests.test_concurrent_signal_processing,
            self.load_tests.test_memory_intensive_operations,
            self.load_tests.test_sustained_load,
        ]

        for test_method in load_test_methods:
            try:
                load_result = await test_method()
                results["load_test_results"].append(load_result)
                results["summary"]["total_tests"] += 1

                # Check load test success
                if self._meets_load_test_criteria(load_result):
                    results["summary"]["passed_tests"] += 1
                else:
                    results["summary"]["failed_tests"] += 1
                    results["summary"]["performance_issues"].append(
                        f"{load_result['operation_name']}: Peak {load_result['peak_performance']:.1f} ops/sec"
                    )

            except Exception as e:
                results["summary"]["total_tests"] += 1
                results["summary"]["failed_tests"] += 1
                results["summary"]["performance_issues"].append(
                    f"{test_method.__name__}: {str(e)}"
                )

        return results

    def _meets_performance_criteria(self, metrics: PerformanceMetrics) -> bool:
        """Check if performance metrics meet criteria."""
        # Define minimum performance thresholds
        thresholds = {
            "signal_creation": 5000,  # 5k signals/sec
            "signal_calculations": 10000,  # 10k calculations/sec
            "candle_processing": 20000,  # 20k candles/sec
            "market_data_processing": 50,  # 50 large datasets/sec
            "bulk_operations": 100,  # 100 bulk ops/sec
        }

        threshold = thresholds.get(metrics.operation_name, 100)
        return (
            metrics.operations_per_second >= threshold
            and metrics.success_rate >= 95.0
            and metrics.avg_operation_time < 1.0
        )  # Less than 1 second average

    def _meets_load_test_criteria(self, load_result: Dict[str, Any]) -> bool:
        """Check if load test results meet criteria."""
        # Basic criteria for load tests
        return load_result["peak_performance"] > 10 and any(  # At least 10 ops/sec peak
            level["error_rate"] < 5.0 for level in load_result["load_levels"]
        )  # Less than 5% error rate at some level


# Pytest integration
@pytest.mark.performance
@pytest.mark.asyncio
class TestPerformancePytest:
    """Pytest-compatible performance tests."""

    async def test_signal_performance(self):
        """Test signal operation performance."""
        entity_tests = EntityPerformanceTests()

        # Test signal creation
        result = await entity_tests.test_signal_creation_performance()
        assert (
            result.operations_per_second > 1000
        ), f"Signal creation too slow: {result.operations_per_second} ops/sec"
        assert (
            result.success_rate >= 95.0
        ), f"Signal creation error rate too high: {100 - result.success_rate}%"

        # Test signal calculations
        result = await entity_tests.test_signal_calculation_performance()
        assert (
            result.operations_per_second > 5000
        ), f"Signal calculations too slow: {result.operations_per_second} ops/sec"

    async def test_market_data_performance(self):
        """Test market data performance."""
        entity_tests = EntityPerformanceTests()

        # Test candle processing
        result = await entity_tests.test_candle_processing_performance()
        assert (
            result.operations_per_second > 10000
        ), f"Candle processing too slow: {result.operations_per_second} ops/sec"

        # Test market data processing
        result = await entity_tests.test_market_data_processing_performance()
        assert (
            result.operations_per_second > 10
        ), f"Market data processing too slow: {result.operations_per_second} ops/sec"

    async def test_load_performance(self):
        """Test load performance."""
        load_tests = LoadTestingScenarios()

        # Test concurrent processing
        result = await load_tests.test_concurrent_signal_processing()
        assert (
            result["peak_performance"] > 50
        ), f"Concurrent processing too slow: {result['peak_performance']} ops/sec"

        # Check error rates are acceptable
        for level in result["load_levels"]:
            if (
                level["concurrent_level"] <= 10
            ):  # Low concurrency should have low error rate
                assert (
                    level["error_rate"] < 1.0
                ), f"High error rate at low concurrency: {level['error_rate']}%"


if __name__ == "__main__":
    # Can be run directly for performance testing
    async def main():
        suite = PerformanceTestSuite()
        results = await suite.run_all_performance_tests()

        print("\n=== Performance Test Results ===")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed_tests']}")
        print(f"Failed: {results['summary']['failed_tests']}")

        print("\n--- Performance Benchmarks ---")
        for benchmark in results["performance_benchmarks"]:
            print(
                f"✅ {benchmark['operation_name']}: {benchmark['operations_per_second']:.1f} ops/sec"
            )
            print(
                f"   Avg: {benchmark['avg_operation_time']*1000:.1f}ms, P95: {benchmark['p95_operation_time']*1000:.1f}ms"
            )

        print("\n--- Load Test Results ---")
        for load_test in results["load_test_results"]:
            print(
                f"✅ {load_test['operation_name']}: Peak {load_test['peak_performance']:.1f} ops/sec"
            )
            if load_test.get("degradation_point"):
                print(
                    f"   Degradation at {load_test['degradation_point']} concurrent operations"
                )

        if results["summary"]["performance_issues"]:
            print("\n--- Performance Issues ---")
            for issue in results["summary"]["performance_issues"]:
                print(f"⚠️  {issue}")

    asyncio.run(main())
