"""
Database Health Monitoring - Enhanced health checking and monitoring utilities

This module provides comprehensive health monitoring capabilities for MongoDB
connections with metrics collection and alerting support.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthMetrics:
    """Database health metrics data."""

    status: HealthStatus
    response_time_ms: float
    active_connections: int
    available_connections: int
    connection_pool_size: int
    last_error: Optional[str] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class DatabaseHealthMonitor:
    """
    Advanced health monitoring for database connections.

    Provides comprehensive health checking with metrics collection,
    alerting capabilities, and performance monitoring.
    """

    def __init__(self, db_manager):
        """
        Initialize health monitor.

        Args:
            db_manager: DatabaseManager instance to monitor
        """
        self.db_manager = db_manager
        self.metrics_history: List[HealthMetrics] = []
        self.max_history_size = 100
        self.alert_thresholds = {
            "response_time_ms": 1000,  # Alert if response time > 1 second
            "connection_usage_percent": 80,  # Alert if connection usage > 80%
        }

    async def perform_health_check(self) -> HealthMetrics:
        """
        Perform comprehensive health check of database connection.

        Returns:
            HealthMetrics: Current health status and metrics
        """
        start_time = time.time()

        try:
            if not self.db_manager.is_connected:
                return HealthMetrics(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    active_connections=0,
                    available_connections=0,
                    connection_pool_size=0,
                    last_error="Database not connected",
                )

            # Perform ping test
            client = self.db_manager.client
            await client.admin.command("ping", maxTimeMS=5000)

            response_time = (time.time() - start_time) * 1000

            # Get connection pool statistics
            pool_stats = self._get_connection_pool_stats()

            # Determine health status
            status = self._determine_health_status(response_time, pool_stats)

            metrics = HealthMetrics(
                status=status,
                response_time_ms=response_time,
                active_connections=pool_stats.get("active_connections", 0),
                available_connections=pool_stats.get("available_connections", 0),
                connection_pool_size=pool_stats.get("pool_size", 0),
            )

            # Store metrics in history
            self._store_metrics(metrics)

            return metrics

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)

            metrics = HealthMetrics(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                active_connections=0,
                available_connections=0,
                connection_pool_size=0,
                last_error=error_msg,
            )

            self._store_metrics(metrics)
            return metrics

    def _get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics from MongoDB client."""
        try:
            # Get connection info from database manager
            conn_info = self.db_manager.get_connection_info()

            # In a real implementation, you would extract actual pool stats
            # from the MongoDB client. For now, we'll use configuration values.
            return {
                "pool_size": conn_info.get("max_pool_size", 0),
                "active_connections": 0,  # Would be extracted from client
                "available_connections": conn_info.get("max_pool_size", 0),
            }

        except Exception as e:
            logger.warning(f"Failed to get connection pool stats: {str(e)}")
            return {
                "pool_size": 0,
                "active_connections": 0,
                "available_connections": 0,
            }

    def _determine_health_status(
        self, response_time: float, pool_stats: Dict[str, Any]
    ) -> HealthStatus:
        """Determine health status based on metrics."""
        # Check response time
        if response_time > self.alert_thresholds["response_time_ms"]:
            return HealthStatus.DEGRADED

        # Check connection pool usage
        pool_size = pool_stats.get("pool_size", 1)
        active_connections = pool_stats.get("active_connections", 0)
        usage_percent = (active_connections / pool_size) * 100 if pool_size > 0 else 0

        if usage_percent > self.alert_thresholds["connection_usage_percent"]:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def _store_metrics(self, metrics: HealthMetrics) -> None:
        """Store metrics in history with size limit."""
        self.metrics_history.append(metrics)

        # Trim history if it exceeds max size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

    def get_recent_metrics(self, count: int = 10) -> List[HealthMetrics]:
        """
        Get recent health metrics.

        Args:
            count: Number of recent metrics to return

        Returns:
            List of recent HealthMetrics
        """
        return self.metrics_history[-count:] if self.metrics_history else []

    def get_average_response_time(self, minutes: int = 5) -> float:
        """
        Get average response time over specified time period.

        Args:
            minutes: Time period in minutes

        Returns:
            Average response time in milliseconds
        """
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m
            for m in self.metrics_history
            if m.timestamp is not None
            and m.timestamp >= cutoff_time
            and m.status != HealthStatus.UNHEALTHY
        ]

        if not recent_metrics:
            return 0.0

        return sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive health summary.

        Returns:
            Dictionary with health summary information
        """
        if not self.metrics_history:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "message": "No health data available",
            }

        latest = self.metrics_history[-1]
        avg_response_time = self.get_average_response_time()

        # Count status distribution in last 10 checks
        recent_statuses = [m.status for m in self.get_recent_metrics(10)]
        status_counts = {
            status.value: recent_statuses.count(status) for status in HealthStatus
        }

        return {
            "current_status": latest.status.value,
            "last_check_time": latest.timestamp,
            "response_time_ms": latest.response_time_ms,
            "average_response_time_5min": avg_response_time,
            "connection_pool": {
                "active": latest.active_connections,
                "available": latest.available_connections,
                "total": latest.connection_pool_size,
            },
            "recent_status_distribution": status_counts,
            "last_error": latest.last_error,
        }


class DatabaseMonitoringService:
    """
    Service for continuous database monitoring with background health checks.
    """

    def __init__(self, db_manager, check_interval: float = 30.0):
        """
        Initialize monitoring service.

        Args:
            db_manager: DatabaseManager instance
            check_interval: Health check interval in seconds
        """
        self.db_manager = db_manager
        self.health_monitor = DatabaseHealthMonitor(db_manager)
        self.check_interval = check_interval
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._is_running:
            logger.warning("Monitoring service is already running")
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Database monitoring started with {self.check_interval}s interval")

    async def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        self._is_running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        logger.info("Database monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._is_running:
            try:
                metrics = await self.health_monitor.perform_health_check()

                # Log health status changes
                if metrics.status != HealthStatus.HEALTHY:
                    logger.warning(
                        f"Database health: {metrics.status.value} "
                        f"(response_time: {metrics.response_time_ms:.2f}ms)"
                    )

                # Check for alerts
                await self._check_alerts(metrics)

                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.check_interval)

    async def _check_alerts(self, metrics: HealthMetrics) -> None:
        """Check if alerts should be triggered based on metrics."""
        # This would integrate with your alerting system
        # For now, just log critical issues

        if metrics.status == HealthStatus.UNHEALTHY:
            logger.error(f"DATABASE ALERT: Unhealthy - {metrics.last_error}")
        elif metrics.response_time_ms > 2000:  # 2 seconds
            logger.warning(
                f"DATABASE ALERT: Slow response time - {metrics.response_time_ms:.2f}ms"
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_monitor.get_health_summary()
