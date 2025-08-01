"""
Query performance monitoring and logging infrastructure.

This module provides comprehensive query performance monitoring, logging,
and optimization insights for repository operations.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
import asyncio
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""

    query_type: str
    collection: str
    duration_ms: float
    timestamp: datetime
    success: bool
    result_count: int
    query_filter: Dict[str, Any]
    error: Optional[str] = None
    memory_usage: Optional[float] = None


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for query performance analysis."""

    query_type: str
    collection: str
    total_executions: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class QueryPerformanceMonitor:
    """
    Monitor and analyze query performance across all repository operations.

    This class provides real-time monitoring, historical analysis, and
    optimization recommendations for database queries.
    """

    def __init__(
        self, max_history_size: int = 10000, aggregation_window_minutes: int = 60
    ):
        """
        Initialize the performance monitor.

        Args:
            max_history_size: Maximum number of query metrics to keep in memory
            aggregation_window_minutes: Window size for aggregated metrics
        """
        self.max_history_size = max_history_size
        self.aggregation_window = timedelta(minutes=aggregation_window_minutes)

        # Store recent query metrics
        self.query_history: deque = deque(maxlen=max_history_size)

        # Aggregated metrics by query type and collection
        self.aggregated_metrics: Dict[str, AggregatedMetrics] = {}

        # Slow query tracking
        self.slow_query_threshold_ms = 1000  # 1 second
        self.slow_queries: deque = deque(maxlen=1000)

        # Real-time performance tracking
        self.recent_durations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Query pattern analysis
        self.query_patterns: Dict[str, int] = defaultdict(int)

    def record_query(
        self,
        query_type: str,
        collection: str,
        duration_ms: float,
        success: bool,
        result_count: int = 0,
        query_filter: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record a query execution for performance monitoring.

        Args:
            query_type: Type of query (find, insert, update, delete, aggregate)
            collection: Collection name
            duration_ms: Query execution duration in milliseconds
            success: Whether the query succeeded
            result_count: Number of results returned
            query_filter: Query filter used (for pattern analysis)
            error: Error message if query failed
        """
        try:
            # Create query metrics
            metrics = QueryMetrics(
                query_type=query_type,
                collection=collection,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                success=success,
                result_count=result_count,
                query_filter=query_filter or {},
                error=error,
            )

            # Add to history
            self.query_history.append(metrics)

            # Update aggregated metrics
            self._update_aggregated_metrics(metrics)

            # Track slow queries
            if duration_ms > self.slow_query_threshold_ms:
                self.slow_queries.append(metrics)
                logger.warning(
                    f"Slow query detected: {query_type} on {collection} "
                    f"took {duration_ms:.2f}ms"
                )

            # Update real-time tracking
            key = f"{collection}.{query_type}"
            self.recent_durations[key].append(duration_ms)

            # Analyze query patterns
            if query_filter:
                pattern = self._extract_query_pattern(query_filter)
                self.query_patterns[f"{collection}.{pattern}"] += 1

            # Log performance metrics
            if duration_ms > 100:  # Log queries taking more than 100ms
                logger.info(
                    f"Query performance: {query_type} on {collection} "
                    f"took {duration_ms:.2f}ms, returned {result_count} results"
                )

        except Exception as e:
            logger.error(f"Error recording query metrics: {e}")

    def _update_aggregated_metrics(self, metrics: QueryMetrics) -> None:
        """Update aggregated metrics for a query type and collection."""
        key = f"{metrics.collection}.{metrics.query_type}"

        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = AggregatedMetrics(
                query_type=metrics.query_type, collection=metrics.collection
            )

        agg = self.aggregated_metrics[key]
        agg.total_executions += 1
        agg.total_duration_ms += metrics.duration_ms
        agg.avg_duration_ms = agg.total_duration_ms / agg.total_executions
        agg.min_duration_ms = min(agg.min_duration_ms, metrics.duration_ms)
        agg.max_duration_ms = max(agg.max_duration_ms, metrics.duration_ms)

        if not metrics.success:
            agg.error_count += 1

        agg.success_rate = (
            agg.total_executions - agg.error_count
        ) / agg.total_executions
        agg.last_updated = datetime.utcnow()

        # Update percentiles from recent data
        key_recent = f"{metrics.collection}.{metrics.query_type}"
        if key_recent in self.recent_durations:
            durations = list(self.recent_durations[key_recent])
            if durations:
                agg.p50_duration_ms = statistics.median(durations)
                agg.p95_duration_ms = (
                    statistics.quantiles(durations, n=20)[18]
                    if len(durations) > 20
                    else max(durations)
                )
                agg.p99_duration_ms = (
                    statistics.quantiles(durations, n=100)[98]
                    if len(durations) > 100
                    else max(durations)
                )

    def _extract_query_pattern(self, query_filter: Dict[str, Any]) -> str:
        """Extract a pattern from query filter for analysis."""
        try:
            # Create a pattern based on keys and operator types
            pattern_parts = []
            for key, value in query_filter.items():
                if isinstance(value, dict):
                    # Extract MongoDB operators
                    operators = [op for op in value.keys() if op.startswith("$")]
                    if operators:
                        pattern_parts.append(f"{key}[{','.join(operators)}]")
                    else:
                        pattern_parts.append(key)
                else:
                    pattern_parts.append(key)

            return "+".join(sorted(pattern_parts))
        except Exception:
            return "unknown_pattern"

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary."""
        try:
            current_time = datetime.utcnow()

            # Recent queries (last hour)
            recent_queries = [
                q
                for q in self.query_history
                if current_time - q.timestamp <= timedelta(hours=1)
            ]

            # Calculate overall metrics
            total_queries = len(recent_queries)
            if total_queries == 0:
                return {"message": "No recent queries to analyze"}

            successful_queries = [q for q in recent_queries if q.success]
            success_rate = len(successful_queries) / total_queries

            durations = [q.duration_ms for q in successful_queries]
            avg_duration = statistics.mean(durations) if durations else 0

            # Top slow queries
            slow_queries_recent = [
                q
                for q in recent_queries
                if q.duration_ms > self.slow_query_threshold_ms
            ]

            # Most frequent query patterns
            pattern_counts = dict(self.query_patterns)
            top_patterns = sorted(
                pattern_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]

            return {
                "summary": {
                    "total_queries_last_hour": total_queries,
                    "success_rate": round(success_rate * 100, 2),
                    "average_duration_ms": round(avg_duration, 2),
                    "slow_queries_count": len(slow_queries_recent),
                    "p95_duration_ms": (
                        round(statistics.quantiles(durations, n=20)[18], 2)
                        if len(durations) > 20
                        else 0
                    ),
                },
                "aggregated_metrics": {
                    key: {
                        "avg_duration_ms": round(metrics.avg_duration_ms, 2),
                        "p95_duration_ms": round(metrics.p95_duration_ms, 2),
                        "success_rate": round(metrics.success_rate * 100, 2),
                        "total_executions": metrics.total_executions,
                    }
                    for key, metrics in self.aggregated_metrics.items()
                },
                "slow_queries": [
                    {
                        "query_type": q.query_type,
                        "collection": q.collection,
                        "duration_ms": round(q.duration_ms, 2),
                        "timestamp": q.timestamp.isoformat(),
                        "filter": str(q.query_filter),
                    }
                    for q in list(self.slow_queries)[-10:]  # Last 10 slow queries
                ],
                "top_query_patterns": top_patterns[:10],
            }

        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": "Failed to generate performance summary"}

    def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []

        try:
            # Analyze aggregated metrics for optimization opportunities
            for key, metrics in self.aggregated_metrics.items():
                # Slow average queries
                if metrics.avg_duration_ms > 500:
                    recommendations.append(
                        f"Consider adding indexes for {metrics.collection} "
                        f"{metrics.query_type} operations (avg: {metrics.avg_duration_ms:.1f}ms)"
                    )

                # High P95 latency
                if metrics.p95_duration_ms > 1000:
                    recommendations.append(
                        f"Optimize {metrics.collection} {metrics.query_type} queries "
                        f"- P95 latency is {metrics.p95_duration_ms:.1f}ms"
                    )

                # Low success rate
                if metrics.success_rate < 0.95:
                    recommendations.append(
                        f"Investigate failures in {metrics.collection} {metrics.query_type} "
                        f"operations (success rate: {metrics.success_rate:.1%})"
                    )

            # Analyze query patterns for indexing opportunities
            for pattern, count in self.query_patterns.items():
                if count > 100:  # Frequently used patterns
                    collection, pattern_detail = pattern.split(".", 1)
                    if "+" in pattern_detail:  # Multiple field queries
                        recommendations.append(
                            f"Consider compound index for {collection} "
                            f"on fields: {pattern_detail.replace('+', ', ')}"
                        )

            # General recommendations based on slow queries
            slow_collections = set(q.collection for q in self.slow_queries)
            for collection in slow_collections:
                recommendations.append(
                    f"Review query patterns and indexing strategy for {collection} collection"
                )

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            recommendations.append("Error generating recommendations - check logs")

        return recommendations[:10]  # Limit to top 10 recommendations


def performance_monitor_decorator(monitor: QueryPerformanceMonitor):
    """
    Decorator to automatically monitor repository method performance.

    Args:
        monitor: QueryPerformanceMonitor instance

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result_count = 0
            error = None

            try:
                result = await func(*args, **kwargs)

                # Try to determine result count
                if hasattr(result, "__len__"):
                    result_count = len(result)
                elif result is not None:
                    result_count = 1

                return result

            except Exception as e:
                success = False
                error = str(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Extract collection and query type from method name
                method_name = func.__name__
                collection = (
                    getattr(args[0], "_collection_name", "unknown")
                    if args
                    else "unknown"
                )

                # Map method names to query types
                query_type_mapping = {
                    "create": "insert",
                    "get_by_id": "find",
                    "get_all": "find",
                    "find_by_criteria": "find",
                    "update": "update",
                    "delete": "delete",
                    "find_one": "find",
                    "upsert": "upsert",
                    "aggregate": "aggregate",
                }

                query_type = query_type_mapping.get(method_name, method_name)

                monitor.record_query(
                    query_type=query_type,
                    collection=collection,
                    duration_ms=duration_ms,
                    success=success,
                    result_count=result_count,
                    error=error,
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result_count = 0
            error = None

            try:
                result = func(*args, **kwargs)

                # Try to determine result count
                if hasattr(result, "__len__"):
                    result_count = len(result)
                elif result is not None:
                    result_count = 1

                return result

            except Exception as e:
                success = False
                error = str(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Extract collection and query type from method name
                method_name = func.__name__
                collection = (
                    getattr(args[0], "_collection_name", "unknown")
                    if args
                    else "unknown"
                )

                # Map method names to query types
                query_type_mapping = {
                    "create": "insert",
                    "get_by_id": "find",
                    "get_all": "find",
                    "find_by_criteria": "find",
                    "update": "update",
                    "delete": "delete",
                    "find_one": "find",
                    "upsert": "upsert",
                    "aggregate": "aggregate",
                }

                query_type = query_type_mapping.get(method_name, method_name)

                monitor.record_query(
                    query_type=query_type,
                    collection=collection,
                    duration_ms=duration_ms,
                    success=success,
                    result_count=result_count,
                    error=error,
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Global performance monitor instance
query_performance_monitor = QueryPerformanceMonitor()
