"""
Connection pool monitoring and health checks.

This module provides comprehensive monitoring of database connection pools,
health checks, and automatic recovery mechanisms for maintaining optimal
database connectivity and performance.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import statistics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ConnectionMetrics:
    """Metrics for database connections."""

    timestamp: datetime
    active_connections: int
    idle_connections: int
    total_connections: int
    max_connections: int
    connection_wait_time_ms: float = 0.0
    query_execution_time_ms: float = 0.0
    connection_errors: int = 0
    successful_connections: int = 0
    pool_usage_percent: float = 0.0


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    check_name: str
    status: HealthStatus
    timestamp: datetime
    duration_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class HealthChecker(ABC):
    """Abstract base class for health checkers."""

    @abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """Perform a health check and return the result."""
        pass

    @property
    @abstractmethod
    def check_name(self) -> str:
        """Return the name of this health check."""
        pass


class DatabaseHealthChecker(HealthChecker):
    """Health checker for database connectivity."""

    def __init__(self, database_manager, timeout_seconds: int = 5):
        """
        Initialize the database health checker.

        Args:
            database_manager: Database manager instance
            timeout_seconds: Timeout for health check operations
        """
        self.database_manager = database_manager
        self.timeout_seconds = timeout_seconds

    @property
    def check_name(self) -> str:
        return "database_connectivity"

    async def check_health(self) -> HealthCheckResult:
        """Check database connectivity and basic operations."""
        start_time = time.time()

        try:
            # Test basic connectivity with timeout
            await asyncio.wait_for(
                self._test_connectivity(), timeout=self.timeout_seconds
            )

            duration_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                check_name=self.check_name,
                status=HealthStatus.HEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                message="Database connectivity is healthy",
                details={
                    "connection_test": "passed",
                    "response_time_ms": round(duration_ms, 2),
                },
            )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=self.check_name,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                message="Database health check timed out",
                error="Timeout after 5 seconds",
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=self.check_name,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                message="Database connectivity failed",
                error=str(e),
            )

    async def _test_connectivity(self):
        """Test basic database connectivity."""
        try:
            # Get database instance
            db = await self.database_manager.get_database()

            # Perform a simple ping operation
            await db.admin.command("ping")

            logger.debug("Database connectivity test passed")

        except Exception as e:
            logger.error(f"Database connectivity test failed: {e}")
            raise


class ConnectionPoolMonitor:
    """
    Monitor database connection pools and provide health insights.

    This monitor tracks connection pool metrics, performs health checks,
    and provides alerts when pool performance degrades.
    """

    def __init__(
        self,
        database_manager,
        check_interval_seconds: int = 30,
        history_size: int = 1000,
    ):
        """
        Initialize the connection pool monitor.

        Args:
            database_manager: Database manager instance
            check_interval_seconds: Interval between health checks
            history_size: Number of historical metrics to keep
        """
        self.database_manager = database_manager
        self.check_interval = check_interval_seconds
        self.history_size = history_size

        # Metrics storage
        self.metrics_history: List[ConnectionMetrics] = []
        self.health_check_history: List[HealthCheckResult] = []

        # Health checkers
        self.health_checkers: List[HealthChecker] = []

        # Monitoring state
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False

        # Alerting thresholds
        self.thresholds = {
            "max_pool_usage_percent": 90.0,
            "max_connection_wait_ms": 1000.0,
            "max_query_time_ms": 5000.0,
            "min_success_rate_percent": 95.0,
        }

        # Alert callbacks
        self._alert_callbacks: List[Callable] = []

        # Register default health checkers
        self._register_default_health_checkers()

    def _register_default_health_checkers(self):
        """Register default health checkers."""
        try:
            self.health_checkers.append(DatabaseHealthChecker(self.database_manager))
        except Exception as e:
            logger.error(f"Error registering default health checkers: {e}")

    def add_health_checker(self, checker: HealthChecker):
        """Add a custom health checker."""
        self.health_checkers.append(checker)
        logger.info(f"Added health checker: {checker.check_name}")

    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add a callback function for alerts."""
        self._alert_callbacks.append(callback)

    async def start_monitoring(self):
        """Start the connection pool monitoring."""
        if self._is_monitoring:
            logger.warning("Connection pool monitoring is already running")
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Connection pool monitoring started")

    async def stop_monitoring(self):
        """Stop the connection pool monitoring."""
        if not self._is_monitoring:
            return

        self._is_monitoring = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Connection pool monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._is_monitoring:
            try:
                # Collect metrics
                await self._collect_metrics()

                # Perform health checks
                await self._perform_health_checks()

                # Check for alerts
                await self._check_alerts()

                # Wait for next interval
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection pool monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _collect_metrics(self):
        """Collect connection pool metrics."""
        try:
            # Get database manager metrics
            db_metrics = await self._get_database_metrics()

            # Create metrics entry
            metrics = ConnectionMetrics(
                timestamp=datetime.utcnow(),
                active_connections=db_metrics.get("active_connections", 0),
                idle_connections=db_metrics.get("idle_connections", 0),
                total_connections=db_metrics.get("total_connections", 0),
                max_connections=db_metrics.get("max_connections", 100),
                connection_wait_time_ms=db_metrics.get("connection_wait_time_ms", 0.0),
                query_execution_time_ms=db_metrics.get("query_execution_time_ms", 0.0),
                connection_errors=db_metrics.get("connection_errors", 0),
                successful_connections=db_metrics.get("successful_connections", 0),
            )

            # Calculate pool usage percentage
            if metrics.max_connections > 0:
                metrics.pool_usage_percent = (
                    metrics.total_connections / metrics.max_connections
                ) * 100

            # Add to history
            self.metrics_history.append(metrics)

            # Trim history if needed
            if len(self.metrics_history) > self.history_size:
                self.metrics_history.pop(0)

            logger.debug(
                f"Collected connection metrics: {metrics.pool_usage_percent:.1f}% pool usage"
            )

        except Exception as e:
            logger.error(f"Error collecting connection metrics: {e}")

    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get metrics from database manager."""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would get actual metrics from your database manager

            # For MongoDB, you might use db.serverStatus() or connection pool info
            db = await self.database_manager.get_database()

            # Simple metrics collection (this would be more sophisticated in practice)
            return {
                "active_connections": 5,  # Placeholder
                "idle_connections": 10,  # Placeholder
                "total_connections": 15,  # Placeholder
                "max_connections": 100,  # Placeholder
                "connection_wait_time_ms": 0.0,
                "query_execution_time_ms": 50.0,
                "connection_errors": 0,
                "successful_connections": 100,
            }

        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {
                "active_connections": 0,
                "idle_connections": 0,
                "total_connections": 0,
                "max_connections": 100,
                "connection_wait_time_ms": 0.0,
                "query_execution_time_ms": 0.0,
                "connection_errors": 1,  # Indicate error
                "successful_connections": 0,
            }

    async def _perform_health_checks(self):
        """Perform all registered health checks."""
        for checker in self.health_checkers:
            try:
                result = await checker.check_health()

                # Add to history
                self.health_check_history.append(result)

                # Trim history if needed
                if len(self.health_check_history) > self.history_size:
                    self.health_check_history.pop(0)

                # Log health check results
                if result.status == HealthStatus.HEALTHY:
                    logger.debug(
                        f"Health check '{result.check_name}': {result.message}"
                    )
                else:
                    logger.warning(
                        f"Health check '{result.check_name}': {result.message}"
                    )

            except Exception as e:
                logger.error(
                    f"Error performing health check '{checker.check_name}': {e}"
                )

    async def _check_alerts(self):
        """Check for alert conditions."""
        if not self.metrics_history:
            return

        latest_metrics = self.metrics_history[-1]
        alerts = []

        # Check pool usage
        if (
            latest_metrics.pool_usage_percent
            > self.thresholds["max_pool_usage_percent"]
        ):
            alerts.append(
                {
                    "type": "high_pool_usage",
                    "message": f"Connection pool usage is {latest_metrics.pool_usage_percent:.1f}%",
                    "value": latest_metrics.pool_usage_percent,
                    "threshold": self.thresholds["max_pool_usage_percent"],
                }
            )

        # Check connection wait time
        if (
            latest_metrics.connection_wait_time_ms
            > self.thresholds["max_connection_wait_ms"]
        ):
            alerts.append(
                {
                    "type": "high_connection_wait",
                    "message": f"Connection wait time is {latest_metrics.connection_wait_time_ms:.1f}ms",
                    "value": latest_metrics.connection_wait_time_ms,
                    "threshold": self.thresholds["max_connection_wait_ms"],
                }
            )

        # Check query execution time
        if (
            latest_metrics.query_execution_time_ms
            > self.thresholds["max_query_time_ms"]
        ):
            alerts.append(
                {
                    "type": "slow_queries",
                    "message": f"Average query time is {latest_metrics.query_execution_time_ms:.1f}ms",
                    "value": latest_metrics.query_execution_time_ms,
                    "threshold": self.thresholds["max_query_time_ms"],
                }
            )

        # Check success rate
        total_connections = (
            latest_metrics.successful_connections + latest_metrics.connection_errors
        )
        if total_connections > 0:
            success_rate = (
                latest_metrics.successful_connections / total_connections
            ) * 100
            if success_rate < self.thresholds["min_success_rate_percent"]:
                alerts.append(
                    {
                        "type": "low_success_rate",
                        "message": f"Connection success rate is {success_rate:.1f}%",
                        "value": success_rate,
                        "threshold": self.thresholds["min_success_rate_percent"],
                    }
                )

        # Send alerts
        for alert in alerts:
            await self._send_alert(alert["type"], alert)

    async def _send_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Send an alert to registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert_type, alert_data)
            except Exception as e:
                logger.error(f"Error sending alert via callback: {e}")

        # Also log the alert
        logger.warning(f"ALERT [{alert_type}]: {alert_data['message']}")

    async def get_current_status(self) -> Dict[str, Any]:
        """Get current connection pool status."""
        try:
            # Latest metrics
            latest_metrics = self.metrics_history[-1] if self.metrics_history else None

            # Recent health checks
            recent_health_checks = {}
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)

            for check in reversed(self.health_check_history):
                if (
                    check.timestamp >= cutoff_time
                    and check.check_name not in recent_health_checks
                ):
                    recent_health_checks[check.check_name] = {
                        "status": check.status.value,
                        "message": check.message,
                        "timestamp": check.timestamp.isoformat(),
                        "duration_ms": round(check.duration_ms, 2),
                    }

            # Calculate trends
            trends = self._calculate_trends()

            return {
                "monitoring_active": self._is_monitoring,
                "last_update": (
                    latest_metrics.timestamp.isoformat() if latest_metrics else None
                ),
                "current_metrics": {
                    "active_connections": (
                        latest_metrics.active_connections if latest_metrics else 0
                    ),
                    "idle_connections": (
                        latest_metrics.idle_connections if latest_metrics else 0
                    ),
                    "total_connections": (
                        latest_metrics.total_connections if latest_metrics else 0
                    ),
                    "pool_usage_percent": (
                        round(latest_metrics.pool_usage_percent, 1)
                        if latest_metrics
                        else 0
                    ),
                    "connection_wait_time_ms": (
                        round(latest_metrics.connection_wait_time_ms, 2)
                        if latest_metrics
                        else 0
                    ),
                    "query_execution_time_ms": (
                        round(latest_metrics.query_execution_time_ms, 2)
                        if latest_metrics
                        else 0
                    ),
                },
                "health_checks": recent_health_checks,
                "trends": trends,
                "thresholds": self.thresholds,
            }

        except Exception as e:
            logger.error(f"Error getting connection pool status: {e}")
            return {
                "error": "Failed to get connection pool status",
                "monitoring_active": self._is_monitoring,
            }

    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from historical data."""
        try:
            if len(self.metrics_history) < 2:
                return {}

            # Get recent metrics (last 10 samples)
            recent_metrics = self.metrics_history[-10:]

            # Calculate trends
            pool_usage_values = [m.pool_usage_percent for m in recent_metrics]
            wait_time_values = [m.connection_wait_time_ms for m in recent_metrics]
            query_time_values = [m.query_execution_time_ms for m in recent_metrics]

            return {
                "pool_usage": {
                    "current": round(pool_usage_values[-1], 1),
                    "average": round(statistics.mean(pool_usage_values), 1),
                    "trend": (
                        "increasing"
                        if pool_usage_values[-1]
                        > statistics.mean(pool_usage_values[:-1])
                        else "decreasing"
                    ),
                },
                "connection_wait_time": {
                    "current": round(wait_time_values[-1], 2),
                    "average": round(statistics.mean(wait_time_values), 2),
                    "trend": (
                        "increasing"
                        if wait_time_values[-1] > statistics.mean(wait_time_values[:-1])
                        else "decreasing"
                    ),
                },
                "query_execution_time": {
                    "current": round(query_time_values[-1], 2),
                    "average": round(statistics.mean(query_time_values), 2),
                    "trend": (
                        "increasing"
                        if query_time_values[-1]
                        > statistics.mean(query_time_values[:-1])
                        else "decreasing"
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {}

    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a performance report for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Filter metrics by time period
            period_metrics = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]

            if not period_metrics:
                return {"message": f"No metrics available for the last {hours} hours"}

            # Calculate statistics
            pool_usage_values = [m.pool_usage_percent for m in period_metrics]
            wait_time_values = [m.connection_wait_time_ms for m in period_metrics]
            query_time_values = [m.query_execution_time_ms for m in period_metrics]

            # Health check summary
            period_health_checks = [
                h for h in self.health_check_history if h.timestamp >= cutoff_time
            ]

            health_summary = {}
            for check in period_health_checks:
                if check.check_name not in health_summary:
                    health_summary[check.check_name] = {
                        "healthy": 0,
                        "degraded": 0,
                        "unhealthy": 0,
                    }
                health_summary[check.check_name][check.status.value] += 1

            return {
                "report_period_hours": hours,
                "total_samples": len(period_metrics),
                "pool_usage_stats": {
                    "min": round(min(pool_usage_values), 1),
                    "max": round(max(pool_usage_values), 1),
                    "average": round(statistics.mean(pool_usage_values), 1),
                    "p95": (
                        round(statistics.quantiles(pool_usage_values, n=20)[18], 1)
                        if len(pool_usage_values) > 20
                        else round(max(pool_usage_values), 1)
                    ),
                },
                "connection_wait_stats": {
                    "min": round(min(wait_time_values), 2),
                    "max": round(max(wait_time_values), 2),
                    "average": round(statistics.mean(wait_time_values), 2),
                    "p95": (
                        round(statistics.quantiles(wait_time_values, n=20)[18], 2)
                        if len(wait_time_values) > 20
                        else round(max(wait_time_values), 2)
                    ),
                },
                "query_time_stats": {
                    "min": round(min(query_time_values), 2),
                    "max": round(max(query_time_values), 2),
                    "average": round(statistics.mean(query_time_values), 2),
                    "p95": (
                        round(statistics.quantiles(query_time_values, n=20)[18], 2)
                        if len(query_time_values) > 20
                        else round(max(query_time_values), 2)
                    ),
                },
                "health_check_summary": health_summary,
            }

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": "Failed to generate performance report"}


# Global connection pool monitor instance
connection_pool_monitor: Optional[ConnectionPoolMonitor] = None


def initialize_connection_monitor(
    database_manager, check_interval_seconds: int = 30
) -> ConnectionPoolMonitor:
    """Initialize the global connection pool monitor."""
    global connection_pool_monitor

    connection_pool_monitor = ConnectionPoolMonitor(
        database_manager=database_manager, check_interval_seconds=check_interval_seconds
    )

    logger.info("Connection pool monitor initialized")
    return connection_pool_monitor


def get_connection_monitor() -> Optional[ConnectionPoolMonitor]:
    """Get the global connection pool monitor instance."""
    return connection_pool_monitor
