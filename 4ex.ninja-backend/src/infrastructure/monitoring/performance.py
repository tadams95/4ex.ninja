"""
Performance Monitoring

Tracks API response times, system performance metrics,
and trading signal processing performance.
"""

import asyncio
import logging
import time
import statistics
from collections import defaultdict, deque
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from enum import Enum
import threading


class MetricType(Enum):
    """Types of performance metrics."""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    TIMER = "timer"


@dataclass
class PerformanceMetric:
    """Performance metric data point."""

    name: str
    value: Union[int, float]
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class TimerResult:
    """Result of a timer measurement."""

    name: str
    duration_ms: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class PerformanceMonitor:
    """Advanced performance monitoring for the application."""

    def __init__(self, max_history: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history

        # Metrics storage
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))

        # Thread safety
        self._lock = threading.RLock()

        # Built-in metrics
        self._request_count = 0
        self._error_count = 0
        self._response_times = deque(maxlen=max_history)

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._build_key(name, tags)
            self._counters[key] += value

            metric = PerformanceMetric(
                name=name,
                value=self._counters[key],
                timestamp=time.time(),
                tags=tags or {},
                metric_type=MetricType.COUNTER,
            )
            self._metrics[key].append(metric)

    def set_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        with self._lock:
            key = self._build_key(name, tags)
            self._gauges[key] = value

            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type=MetricType.GAUGE,
            )
            self._metrics[key].append(metric)

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram value."""
        with self._lock:
            key = self._build_key(name, tags)

            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type=MetricType.HISTOGRAM,
            )
            self._metrics[key].append(metric)

    def record_timer(
        self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer measurement."""
        with self._lock:
            key = self._build_key(name, tags)

            timer_result = TimerResult(
                name=name,
                duration_ms=duration_ms,
                timestamp=time.time(),
                tags=tags or {},
            )
            self._timers[key].append(timer_result)

            # Also record as histogram for statistics
            self.record_histogram(f"{name}_duration", duration_ms, tags)

    @asynccontextmanager
    async def time_async(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing async operations."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.record_timer(name, duration_ms, tags)

    def time_sync(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing sync operations."""
        return TimingContext(self, name, tags)

    def get_metric_stats(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get statistics for a metric."""
        with self._lock:
            key = self._build_key(name, tags)

            if key not in self._metrics or not self._metrics[key]:
                return {"error": "No data available"}

            values = [m.value for m in self._metrics[key]]

            if not values:
                return {"error": "No values available"}

            return {
                "count": len(values),
                "latest": values[-1],
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            }

    def get_timer_stats(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get statistics for a timer."""
        with self._lock:
            key = self._build_key(name, tags)

            if key not in self._timers or not self._timers[key]:
                return {"error": "No timer data available"}

            durations = [t.duration_ms for t in self._timers[key]]

            if not durations:
                return {"error": "No timing values available"}

            return {
                "count": len(durations),
                "latest_ms": durations[-1],
                "min_ms": min(durations),
                "max_ms": max(durations),
                "mean_ms": statistics.mean(durations),
                "median_ms": statistics.median(durations),
                "p95_ms": self._percentile(durations, 0.95),
                "p99_ms": self._percentile(durations, 0.99),
                "stddev_ms": statistics.stdev(durations) if len(durations) > 1 else 0,
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "metrics_count": {
                    key: len(metrics) for key, metrics in self._metrics.items()
                },
                "timers_count": {
                    key: len(timers) for key, timers in self._timers.items()
                },
            }

    def reset_metrics(self, name: Optional[str] = None) -> None:
        """Reset metrics (all or specific metric)."""
        with self._lock:
            if name:
                # Reset specific metric
                keys_to_remove = [
                    key for key in self._metrics.keys() if key.startswith(name)
                ]
                for key in keys_to_remove:
                    del self._metrics[key]
                    if key in self._counters:
                        del self._counters[key]
                    if key in self._gauges:
                        del self._gauges[key]
                    if key in self._timers:
                        del self._timers[key]
            else:
                # Reset all metrics
                self._metrics.clear()
                self._counters.clear()
                self._gauges.clear()
                self._timers.clear()

    def _build_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Build a unique key for a metric with tags."""
        if not tags:
            return name

        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(percentile * (len(sorted_values) - 1))
        return sorted_values[index]


class TimingContext:
    """Context manager for timing sync operations."""

    def __init__(
        self,
        monitor: PerformanceMonitor,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.monitor = monitor
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.monitor.record_timer(self.name, duration_ms, self.tags)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Built-in performance tracking functions
def track_api_request(
    endpoint: str, method: str, status_code: int, duration_ms: float
) -> None:
    """Track API request performance."""
    tags = {"endpoint": endpoint, "method": method, "status_code": str(status_code)}

    performance_monitor.increment_counter("api_requests_total", tags=tags)
    performance_monitor.record_timer("api_request_duration", duration_ms, tags)

    if status_code >= 400:
        performance_monitor.increment_counter("api_errors_total", tags=tags)


def track_signal_processing(
    pair: str, timeframe: str, duration_ms: float, signal_count: int
) -> None:
    """Track trading signal processing performance."""
    tags = {"pair": pair, "timeframe": timeframe}

    performance_monitor.record_timer("signal_processing_duration", duration_ms, tags)
    performance_monitor.increment_counter("signals_processed", signal_count, tags)
    performance_monitor.set_gauge("last_signal_processing_time", time.time(), tags)


def track_database_operation(
    operation: str, collection: str, duration_ms: float, success: bool
) -> None:
    """Track database operation performance."""
    tags = {"operation": operation, "collection": collection, "success": str(success)}

    performance_monitor.record_timer("database_operation_duration", duration_ms, tags)
    performance_monitor.increment_counter("database_operations_total", tags=tags)

    if not success:
        performance_monitor.increment_counter("database_errors_total", tags=tags)


def track_external_api_call(
    service: str, endpoint: str, duration_ms: float, success: bool
) -> None:
    """Track external API call performance."""
    tags = {"service": service, "endpoint": endpoint, "success": str(success)}

    performance_monitor.record_timer("external_api_duration", duration_ms, tags)
    performance_monitor.increment_counter("external_api_calls_total", tags=tags)

    if not success:
        performance_monitor.increment_counter("external_api_errors_total", tags=tags)


# Performance summary functions
def get_performance_summary() -> Dict[str, Any]:
    """Get a comprehensive performance summary."""
    summary = {
        "timestamp": time.time(),
        "api_performance": {},
        "signal_processing": {},
        "database_performance": {},
        "external_apis": {},
        "system_metrics": performance_monitor.get_all_metrics(),
    }

    # API performance
    api_stats = performance_monitor.get_timer_stats("api_request_duration")
    if "error" not in api_stats:
        summary["api_performance"] = api_stats

    # Signal processing performance
    signal_stats = performance_monitor.get_timer_stats("signal_processing_duration")
    if "error" not in signal_stats:
        summary["signal_processing"] = signal_stats

    # Database performance
    db_stats = performance_monitor.get_timer_stats("database_operation_duration")
    if "error" not in db_stats:
        summary["database_performance"] = db_stats

    # External API performance
    ext_api_stats = performance_monitor.get_timer_stats("external_api_duration")
    if "error" not in ext_api_stats:
        summary["external_apis"] = ext_api_stats

    return summary


def get_slow_operations(threshold_ms: float = 1000) -> Dict[str, List[Dict[str, Any]]]:
    """Get operations that are slower than threshold."""
    slow_ops = {
        "api_requests": [],
        "signal_processing": [],
        "database_operations": [],
        "external_api_calls": [],
    }

    # Check for slow operations
    # This would be implemented based on specific monitoring needs

    return slow_ops
