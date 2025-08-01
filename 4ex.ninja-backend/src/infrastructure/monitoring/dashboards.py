"""
Monitoring Dashboards and Metrics Collection Module

This module provides comprehensive metrics collection for system performance,
business metrics, and error rate monitoring with dashboard visualization capabilities.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import json
from collections import defaultdict, deque
import threading
from abc import ABC, abstractmethod

# Set up logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"  # Monotonically increasing values
    GAUGE = "gauge"  # Point-in-time values
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements
    RATE = "rate"  # Events per time unit


class MetricCategory(Enum):
    """Categories of metrics for organization."""

    SYSTEM = "system"  # System performance metrics
    BUSINESS = "business"  # Business-related metrics
    APPLICATION = "application"  # Application-specific metrics
    INFRASTRUCTURE = "infrastructure"  # Infrastructure metrics
    SECURITY = "security"  # Security-related metrics


@dataclass
class MetricPoint:
    """Represents a single metric data point."""

    timestamp: datetime
    value: Union[int, float]
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "tags": self.tags,
        }


@dataclass
class Metric:
    """Represents a metric with its metadata and data points."""

    name: str
    metric_type: MetricType
    category: MetricCategory
    description: str
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    data_points: List[MetricPoint] = field(default_factory=list)
    retention_seconds: int = 86400  # 24 hours default

    def add_point(
        self, value: Union[int, float], tags: Optional[Dict[str, str]] = None
    ):
        """Add a data point to the metric."""
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc), value=value, tags=tags or {}
        )
        self.data_points.append(point)

        # Clean old data points
        self._cleanup_old_points()

    def _cleanup_old_points(self):
        """Remove data points older than retention period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            seconds=self.retention_seconds
        )
        self.data_points = [
            point for point in self.data_points if point.timestamp > cutoff_time
        ]

    def get_current_value(self) -> Optional[Union[int, float]]:
        """Get the most recent value."""
        if self.data_points:
            return self.data_points[-1].value
        return None

    def get_average(self, window_seconds: Optional[int] = None) -> Optional[float]:
        """Get average value over time window."""
        points = self._get_points_in_window(window_seconds)
        if not points:
            return None

        return sum(point.value for point in points) / len(points)

    def get_rate(self, window_seconds: int = 60) -> Optional[float]:
        """Get rate of change over time window."""
        points = self._get_points_in_window(window_seconds)
        if len(points) < 2:
            return None

        time_diff = (points[-1].timestamp - points[0].timestamp).total_seconds()
        if time_diff <= 0:
            return None

        value_diff = points[-1].value - points[0].value
        return value_diff / time_diff

    def _get_points_in_window(self, window_seconds: Optional[int]) -> List[MetricPoint]:
        """Get data points within time window."""
        if window_seconds is None:
            return self.data_points

        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        return [point for point in self.data_points if point.timestamp > cutoff_time]


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.lock = threading.RLock()
        self._setup_system_metrics()

    def _setup_system_metrics(self):
        """Setup default system metrics."""
        # System performance metrics
        self.register_metric(
            "cpu_usage_percent",
            MetricType.GAUGE,
            MetricCategory.SYSTEM,
            "CPU usage percentage",
            "%",
        )

        self.register_metric(
            "memory_usage_bytes",
            MetricType.GAUGE,
            MetricCategory.SYSTEM,
            "Memory usage in bytes",
            "bytes",
        )

        self.register_metric(
            "disk_usage_percent",
            MetricType.GAUGE,
            MetricCategory.SYSTEM,
            "Disk usage percentage",
            "%",
        )

        # Application metrics
        self.register_metric(
            "request_count",
            MetricType.COUNTER,
            MetricCategory.APPLICATION,
            "Total number of requests processed",
        )

        self.register_metric(
            "request_duration_ms",
            MetricType.HISTOGRAM,
            MetricCategory.APPLICATION,
            "Request duration in milliseconds",
            "ms",
        )

        self.register_metric(
            "error_count",
            MetricType.COUNTER,
            MetricCategory.APPLICATION,
            "Total number of errors",
        )

        self.register_metric(
            "error_rate",
            MetricType.RATE,
            MetricCategory.APPLICATION,
            "Error rate per second",
            "errors/sec",
        )

        # Business metrics
        self.register_metric(
            "signals_generated",
            MetricType.COUNTER,
            MetricCategory.BUSINESS,
            "Total number of trading signals generated",
        )

        self.register_metric(
            "active_users",
            MetricType.GAUGE,
            MetricCategory.BUSINESS,
            "Number of active users",
        )

        self.register_metric(
            "subscription_conversions",
            MetricType.COUNTER,
            MetricCategory.BUSINESS,
            "Number of subscription conversions",
        )

        # Infrastructure metrics
        self.register_metric(
            "database_connections",
            MetricType.GAUGE,
            MetricCategory.INFRASTRUCTURE,
            "Number of active database connections",
        )

        self.register_metric(
            "api_response_time_ms",
            MetricType.HISTOGRAM,
            MetricCategory.INFRASTRUCTURE,
            "External API response time in milliseconds",
            "ms",
        )

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        category: MetricCategory,
        description: str,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
        retention_seconds: int = 86400,
    ) -> Metric:
        """Register a new metric."""
        with self.lock:
            metric = Metric(
                name=name,
                metric_type=metric_type,
                category=category,
                description=description,
                unit=unit,
                tags=tags or {},
                retention_seconds=retention_seconds,
            )
            self.metrics[name] = metric
            logger.debug(f"Registered metric: {name}")
            return metric

    def increment_counter(
        self,
        name: str,
        value: Union[int, float] = 1,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Increment a counter metric."""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                current_value = metric.get_current_value() or 0
                metric.add_point(current_value + value, tags)
            else:
                logger.warning(f"Counter metric not found: {name}")

    def set_gauge(
        self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric value."""
        with self.lock:
            if name in self.metrics:
                self.metrics[name].add_point(value, tags)
            else:
                logger.warning(f"Gauge metric not found: {name}")

    def record_histogram(
        self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None
    ):
        """Record a value in a histogram metric."""
        with self.lock:
            if name in self.metrics:
                self.metrics[name].add_point(value, tags)
            else:
                logger.warning(f"Histogram metric not found: {name}")

    def time_function(self, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """Decorator to time function execution."""

        def decorator(func):
            if asyncio.iscoroutinefunction(func):

                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000
                        self.record_histogram(metric_name, duration_ms, tags)
                        return result
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        error_tags = (tags or {}).copy()
                        error_tags["error"] = "true"
                        self.record_histogram(metric_name, duration_ms, error_tags)
                        raise

                return async_wrapper
            else:

                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000
                        self.record_histogram(metric_name, duration_ms, tags)
                        return result
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        error_tags = (tags or {}).copy()
                        error_tags["error"] = "true"
                        self.record_histogram(metric_name, duration_ms, error_tags)
                        raise

                return sync_wrapper

        return decorator

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        with self.lock:
            return self.metrics.get(name)

    def get_metrics_by_category(self, category: MetricCategory) -> List[Metric]:
        """Get all metrics in a category."""
        with self.lock:
            return [
                metric
                for metric in self.metrics.values()
                if metric.category == category
            ]

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics."""
        with self.lock:
            return self.metrics.copy()

    def collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("cpu_usage_percent", cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("memory_usage_bytes", memory.used)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self.set_gauge("disk_usage_percent", disk_percent)

        except ImportError:
            logger.debug("psutil not available for system metrics collection")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")


class Dashboard:
    """Provides dashboard functionality for metrics visualization."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health metrics."""
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy",
            "metrics": {},
        }

        # System metrics
        system_metrics = self.metrics_collector.get_metrics_by_category(
            MetricCategory.SYSTEM
        )
        for metric in system_metrics:
            current_value = metric.get_current_value()
            if current_value is not None:
                summary["metrics"][metric.name] = {
                    "value": current_value,
                    "unit": metric.unit,
                    "description": metric.description,
                }

        # Determine overall status
        cpu_usage = summary["metrics"].get("cpu_usage_percent", {}).get("value", 0)
        memory_usage = summary["metrics"].get("memory_usage_bytes", {}).get("value", 0)

        if cpu_usage > 90 or memory_usage > 8 * 1024 * 1024 * 1024:  # 8GB
            summary["status"] = "critical"
        elif cpu_usage > 70 or memory_usage > 6 * 1024 * 1024 * 1024:  # 6GB
            summary["status"] = "warning"

        return summary

    def get_business_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of business metrics."""
        summary = {"timestamp": datetime.now(timezone.utc).isoformat(), "metrics": {}}

        business_metrics = self.metrics_collector.get_metrics_by_category(
            MetricCategory.BUSINESS
        )
        for metric in business_metrics:
            current_value = metric.get_current_value()
            if current_value is not None:
                summary["metrics"][metric.name] = {
                    "current": current_value,
                    "hourly_average": metric.get_average(3600),
                    "daily_average": metric.get_average(86400),
                    "unit": metric.unit,
                    "description": metric.description,
                }

        return summary

    def get_error_rate_summary(self) -> Dict[str, Any]:
        """Get error rate and recovery metrics."""
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_metrics": {},
        }

        error_count_metric = self.metrics_collector.get_metric("error_count")
        request_count_metric = self.metrics_collector.get_metric("request_count")

        if error_count_metric and request_count_metric:
            # Calculate error rate
            errors_last_hour = len(
                [
                    point
                    for point in error_count_metric.data_points
                    if point.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)
                ]
            )

            requests_last_hour = len(
                [
                    point
                    for point in request_count_metric.data_points
                    if point.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)
                ]
            )

            if requests_last_hour > 0:
                error_rate = (errors_last_hour / requests_last_hour) * 100
            else:
                error_rate = 0

            summary["error_metrics"] = {
                "error_rate_percent": error_rate,
                "errors_last_hour": errors_last_hour,
                "requests_last_hour": requests_last_hour,
                "status": (
                    "healthy"
                    if error_rate < 1
                    else "warning" if error_rate < 5 else "critical"
                ),
            }

        return summary

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance": {},
        }

        # Request duration metrics
        duration_metric = self.metrics_collector.get_metric("request_duration_ms")
        if duration_metric:
            recent_points = duration_metric._get_points_in_window(3600)  # Last hour
            if recent_points:
                values = [point.value for point in recent_points]
                values.sort()

                summary["performance"]["request_duration"] = {
                    "average_ms": sum(values) / len(values),
                    "p50_ms": values[len(values) // 2] if values else 0,
                    "p95_ms": values[int(len(values) * 0.95)] if values else 0,
                    "p99_ms": values[int(len(values) * 0.99)] if values else 0,
                }

        # API response time metrics
        api_metric = self.metrics_collector.get_metric("api_response_time_ms")
        if api_metric:
            recent_points = api_metric._get_points_in_window(3600)  # Last hour
            if recent_points:
                values = [point.value for point in recent_points]
                summary["performance"]["api_response_time"] = {
                    "average_ms": sum(values) / len(values),
                    "max_ms": max(values),
                    "min_ms": min(values),
                }

        return summary

    def export_metrics_json(self, time_window_seconds: Optional[int] = 3600) -> str:
        """Export metrics as JSON for external dashboards."""
        export_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "time_window_seconds": time_window_seconds,
            "metrics": {},
        }

        for name, metric in self.metrics_collector.get_all_metrics().items():
            points = metric._get_points_in_window(time_window_seconds)
            export_data["metrics"][name] = {
                "type": metric.metric_type.value,
                "category": metric.category.value,
                "description": metric.description,
                "unit": metric.unit,
                "tags": metric.tags,
                "data_points": [point.to_dict() for point in points],
            }

        return json.dumps(export_data, indent=2)


class MetricsScheduler:
    """Schedules periodic metrics collection."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.running = False
        self.tasks: List[asyncio.Task] = []

    async def start(self):
        """Start periodic metrics collection."""
        if self.running:
            return

        self.running = True
        logger.info("Starting metrics collection scheduler")

        # Schedule system metrics collection every 30 seconds
        self.tasks.append(asyncio.create_task(self._periodic_system_metrics()))

        # Schedule metrics cleanup every hour
        self.tasks.append(asyncio.create_task(self._periodic_cleanup()))

    async def stop(self):
        """Stop metrics collection."""
        self.running = False

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        logger.info("Metrics collection scheduler stopped")

    async def _periodic_system_metrics(self):
        """Periodically collect system metrics."""
        while self.running:
            try:
                self.metrics_collector.collect_system_metrics()
                await asyncio.sleep(30)  # Every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic system metrics collection: {str(e)}")
                await asyncio.sleep(30)

    async def _periodic_cleanup(self):
        """Periodically clean up old metrics data."""
        while self.running:
            try:
                # Clean up old data points from all metrics
                for metric in self.metrics_collector.get_all_metrics().values():
                    metric._cleanup_old_points()

                await asyncio.sleep(3600)  # Every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic metrics cleanup: {str(e)}")
                await asyncio.sleep(3600)


# Global metrics collector and dashboard instances
metrics_collector = MetricsCollector()
dashboard = Dashboard(metrics_collector)
scheduler = MetricsScheduler(metrics_collector)


# Convenience decorators and functions


def track_requests(func):
    """Decorator to track request count and duration."""

    @metrics_collector.time_function("request_duration_ms")
    def wrapper(*args, **kwargs):
        metrics_collector.increment_counter("request_count")
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            metrics_collector.increment_counter("error_count")
            raise

    return wrapper


def track_business_event(event_name: str, value: Union[int, float] = 1):
    """Track a business event."""
    metrics_collector.increment_counter(f"business_event_{event_name}", value)


def record_signal_generated(pair: str, confidence: float):
    """Record a trading signal generation."""
    metrics_collector.increment_counter("signals_generated")
    metrics_collector.record_histogram("signal_confidence", confidence, {"pair": pair})


def record_user_activity(user_id: str, activity_type: str):
    """Record user activity."""
    metrics_collector.increment_counter(
        "user_activity", tags={"activity_type": activity_type}
    )

    # Update active users gauge (this is simplified - in production you'd track unique users)
    active_users_metric = metrics_collector.get_metric("active_users")
    if active_users_metric:
        current_value = active_users_metric.get_current_value() or 0
        metrics_collector.set_gauge("active_users", current_value + 1)
