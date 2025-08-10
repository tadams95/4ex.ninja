"""
Business Metrics Monitor

Tracks business-specific performance metrics for trading signals,
user activities, and system performance indicators.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class SignalStatus(Enum):
    """Signal processing status."""
    GENERATED = "generated"
    VALIDATED = "validated"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class BusinessMetric:
    """Business metric data point."""
    
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalMetrics:
    """Signal processing metrics."""
    
    total_generated: int = 0
    total_validated: int = 0
    total_sent: int = 0
    total_failed: int = 0
    avg_processing_time_ms: float = 0.0
    avg_confidence: float = 0.0
    pairs_processed: set = field(default_factory=set)
    last_signal_time: Optional[float] = None


class BusinessMetricsMonitor:
    """Monitors business-specific performance metrics."""
    
    def __init__(self, max_history: int = 10000):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        
        # Metrics storage
        self._metrics_history = deque(maxlen=max_history)
        self._signal_metrics = SignalMetrics()
        self._user_activity = defaultdict(int)
        self._api_metrics = defaultdict(lambda: {"count": 0, "total_time": 0.0, "errors": 0})
        self._cache_metrics = {"hits": 0, "misses": 0, "evictions": 0}
        
        # Processing times for different operations
        self._processing_times = defaultdict(lambda: deque(maxlen=1000))
        
    def record_signal_generated(
        self, 
        pair: str, 
        confidence: float, 
        processing_time_ms: float,
        signal_type: str = "crossover"
    ):
        """Record a signal generation event."""
        self._signal_metrics.total_generated += 1
        self._signal_metrics.pairs_processed.add(pair)
        self._signal_metrics.last_signal_time = time.time()
        
        # Update average confidence
        current_avg = self._signal_metrics.avg_confidence
        total_signals = self._signal_metrics.total_generated
        self._signal_metrics.avg_confidence = (
            (current_avg * (total_signals - 1) + confidence) / total_signals
        )
        
        # Update average processing time
        current_avg_time = self._signal_metrics.avg_processing_time_ms
        self._signal_metrics.avg_processing_time_ms = (
            (current_avg_time * (total_signals - 1) + processing_time_ms) / total_signals
        )
        
        # Record detailed metric
        metric = BusinessMetric(
            name="signal_generated",
            value=1,
            timestamp=time.time(),
            tags={
                "pair": pair,
                "signal_type": signal_type
            },
            metadata={
                "confidence": confidence,
                "processing_time_ms": processing_time_ms
            }
        )
        self._metrics_history.append(metric)
        
        self.logger.debug(
            f"Signal generated: {pair} confidence={confidence:.3f} "
            f"processing_time={processing_time_ms:.1f}ms"
        )
        
    def record_signal_status_change(
        self,
        signal_id: str,
        old_status: SignalStatus,
        new_status: SignalStatus,
        processing_time_ms: Optional[float] = None
    ):
        """Record a signal status change."""
        if new_status == SignalStatus.VALIDATED:
            self._signal_metrics.total_validated += 1
        elif new_status == SignalStatus.SENT:
            self._signal_metrics.total_sent += 1
        elif new_status == SignalStatus.FAILED:
            self._signal_metrics.total_failed += 1
            
        metric = BusinessMetric(
            name="signal_status_change",
            value=1,
            timestamp=time.time(),
            tags={
                "signal_id": signal_id,
                "old_status": old_status.value,
                "new_status": new_status.value
            },
            metadata={
                "processing_time_ms": processing_time_ms
            }
        )
        self._metrics_history.append(metric)
        
    def record_user_activity(
        self,
        user_id: str,
        activity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record user activity."""
        self._user_activity[activity_type] += 1
        
        metric = BusinessMetric(
            name="user_activity",
            value=1,
            timestamp=time.time(),
            tags={
                "user_id": user_id,
                "activity_type": activity_type
            },
            metadata=metadata or {}
        )
        self._metrics_history.append(metric)
        
    def record_api_call(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        user_id: Optional[str] = None
    ):
        """Record API call metrics."""
        key = f"{method}:{endpoint}"
        api_stats = self._api_metrics[key]
        
        api_stats["count"] += 1
        api_stats["total_time"] += response_time_ms
        
        if status_code >= 400:
            api_stats["errors"] += 1
            
        metric = BusinessMetric(
            name="api_call",
            value=response_time_ms,
            timestamp=time.time(),
            tags={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
                "user_id": user_id or "anonymous"
            }
        )
        self._metrics_history.append(metric)
        
    def record_cache_operation(
        self,
        operation: str,  # "hit", "miss", "eviction", "set"
        cache_type: str,
        key: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ):
        """Record cache operation metrics."""
        if operation in self._cache_metrics:
            self._cache_metrics[operation] += 1
            
        metric = BusinessMetric(
            name="cache_operation",
            value=1,
            timestamp=time.time(),
            tags={
                "operation": operation,
                "cache_type": cache_type
            },
            metadata={
                "key": key,
                "processing_time_ms": processing_time_ms
            }
        )
        self._metrics_history.append(metric)
        
    def record_database_operation(
        self,
        operation: str,  # "find", "insert", "update", "delete", "aggregate"
        collection: str,
        duration_ms: float,
        record_count: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Record database operation metrics."""
        self._processing_times[f"db_{operation}"].append(duration_ms)
        
        metric = BusinessMetric(
            name="database_operation",
            value=duration_ms,
            timestamp=time.time(),
            tags={
                "operation": operation,
                "collection": collection,
                "success": "false" if error else "true"
            },
            metadata={
                "record_count": record_count,
                "error": error
            }
        )
        self._metrics_history.append(metric)
        
    def get_signal_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive signal metrics summary."""
        total_processed = (
            self._signal_metrics.total_validated + 
            self._signal_metrics.total_failed
        )
        
        success_rate = (
            (self._signal_metrics.total_validated / total_processed * 100)
            if total_processed > 0 else 0
        )
        
        delivery_rate = (
            (self._signal_metrics.total_sent / self._signal_metrics.total_validated * 100)
            if self._signal_metrics.total_validated > 0 else 0
        )
        
        return {
            "signal_generation": {
                "total_generated": self._signal_metrics.total_generated,
                "total_validated": self._signal_metrics.total_validated,
                "total_sent": self._signal_metrics.total_sent,
                "total_failed": self._signal_metrics.total_failed,
                "success_rate_percent": round(success_rate, 2),
                "delivery_rate_percent": round(delivery_rate, 2),
                "avg_confidence": round(self._signal_metrics.avg_confidence, 3),
                "avg_processing_time_ms": round(self._signal_metrics.avg_processing_time_ms, 2),
                "pairs_processed_count": len(self._signal_metrics.pairs_processed),
                "pairs_processed": sorted(list(self._signal_metrics.pairs_processed)),
                "last_signal_time": self._signal_metrics.last_signal_time
            }
        }
        
    def get_api_metrics_summary(self) -> Dict[str, Any]:
        """Get API performance metrics summary."""
        summary = {}
        
        for endpoint, stats in self._api_metrics.items():
            if stats["count"] > 0:
                avg_response_time = stats["total_time"] / stats["count"]
                error_rate = (stats["errors"] / stats["count"]) * 100
                
                summary[endpoint] = {
                    "total_calls": stats["count"],
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "total_errors": stats["errors"],
                    "error_rate_percent": round(error_rate, 2)
                }
                
        return summary
        
    def get_cache_metrics_summary(self) -> Dict[str, Any]:
        """Get cache performance metrics summary."""
        total_operations = self._cache_metrics["hits"] + self._cache_metrics["misses"]
        hit_rate = (
            (self._cache_metrics["hits"] / total_operations * 100)
            if total_operations > 0 else 0
        )
        
        return {
            "cache_hits": self._cache_metrics["hits"],
            "cache_misses": self._cache_metrics["misses"],
            "cache_evictions": self._cache_metrics["evictions"],
            "hit_rate_percent": round(hit_rate, 2),
            "total_operations": total_operations
        }
        
    def get_user_activity_summary(self) -> Dict[str, Any]:
        """Get user activity metrics summary."""
        return dict(self._user_activity)
        
    def get_database_performance_summary(self) -> Dict[str, Any]:
        """Get database performance metrics summary."""
        summary = {}
        
        for operation, times in self._processing_times.items():
            if times:
                times_list = list(times)
                summary[operation] = {
                    "count": len(times_list),
                    "avg_ms": round(sum(times_list) / len(times_list), 2),
                    "min_ms": round(min(times_list), 2),
                    "max_ms": round(max(times_list), 2),
                    "p95_ms": round(self._percentile(times_list, 0.95), 2),
                    "p99_ms": round(self._percentile(times_list, 0.99), 2)
                }
                
        return summary
        
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get comprehensive business metrics summary."""
        return {
            "timestamp": time.time(),
            "signals": self.get_signal_metrics_summary(),
            "api_performance": self.get_api_metrics_summary(),
            "cache_performance": self.get_cache_metrics_summary(),
            "user_activity": self.get_user_activity_summary(),
            "database_performance": self.get_database_performance_summary(),
            "metrics_history_count": len(self._metrics_history)
        }
        
    def get_recent_metrics(self, minutes: int = 60) -> List[BusinessMetric]:
        """Get metrics from the last N minutes."""
        cutoff_time = time.time() - (minutes * 60)
        return [
            metric for metric in self._metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        self._signal_metrics = SignalMetrics()
        self._user_activity.clear()
        self._api_metrics.clear()
        self._cache_metrics = {"hits": 0, "misses": 0, "evictions": 0}
        self._processing_times.clear()
        self._metrics_history.clear()
        
        self.logger.info("Business metrics reset")
        
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global instance
business_metrics_monitor = BusinessMetricsMonitor()
