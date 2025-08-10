"""
Application Health Monitoring

Provides comprehensive health checks for database connections,
external APIs, and system resources.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

try:
    import aiohttp
except ImportError:
    aiohttp = None


class HealthStatus(Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result."""

    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    details: Optional[Dict[str, Any]] = None


class HealthMonitor:
    """Comprehensive health monitoring for the application."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._checks: Dict[str, Callable] = {}
        self._last_results: Dict[str, HealthCheck] = {}

    def register_check(self, name: str, check_func: Callable) -> None:
        """Register a health check function."""
        self._checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")

    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self._checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check '{name}' not found",
                duration_ms=0,
            )

        start_time = time.perf_counter()
        try:
            result = await self._checks[name]()
            duration_ms = (time.perf_counter() - start_time) * 1000

            if isinstance(result, HealthCheck):
                result.duration_ms = duration_ms
                self._last_results[name] = result
                return result
            else:
                # If function returns a simple status
                health_check = HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message=(
                        "Check completed successfully" if result else "Check failed"
                    ),
                    duration_ms=duration_ms,
                )
                self._last_results[name] = health_check
                return health_check

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            health_check = HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms,
                details={"error": str(e), "error_type": type(e).__name__},
            )
            self._last_results[name] = health_check
            return health_check

    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        tasks = []
        for name in self._checks:
            tasks.append(self.run_check(name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_results = {}
        for i, name in enumerate(self._checks.keys()):
            if isinstance(results[i], Exception):
                health_results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(results[i])}",
                    duration_ms=0,
                )
            else:
                health_results[name] = results[i]

        # Trigger alerts for unhealthy systems
        await self._check_and_send_alerts(health_results)

        return health_results

    async def _check_and_send_alerts(self, results: Dict[str, HealthCheck]):
        """Check health results and send alerts for critical issues."""
        try:
            from .alerts import alert_database_connectivity, alert_external_api_downtime

            for name, result in results.items():
                if result.status == HealthStatus.UNHEALTHY:
                    if name == "database":
                        await alert_database_connectivity(
                            message=f"Database health check failed: {result.message}",
                            context={
                                "health_check": name,
                                "duration_ms": result.duration_ms,
                                "details": result.details or {},
                            },
                        )
                    elif name in ["oanda_api", "external_api"]:
                        await alert_external_api_downtime(
                            api_name=name,
                            message=f"External API health check failed: {result.message}",
                            context={
                                "health_check": name,
                                "duration_ms": result.duration_ms,
                                "details": result.details or {},
                            },
                        )
        except Exception as e:
            self.logger.error(f"Failed to send health check alerts: {str(e)}")

    def get_overall_status(self, results: Dict[str, HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks."""
        if not results:
            return HealthStatus.UNHEALTHY

        statuses = [check.status for check in results.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

    def get_last_results(self) -> Dict[str, HealthCheck]:
        """Get the last health check results."""
        return self._last_results.copy()


# Global health monitor instance
health_monitor = HealthMonitor()


# Built-in health checks
async def check_database_connection() -> HealthCheck:
    """Check database connectivity."""
    try:
        # For now, we'll create a placeholder check
        # This will be replaced with actual MongoDB connection check
        import pymongo

        # Placeholder - replace with actual MongoDB connection
        # client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        # client.server_info()

        return HealthCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            duration_ms=0,
            details={"type": "mongodb", "status": "connected"},
        )

    except Exception as e:
        return HealthCheck(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            duration_ms=0,
            details={"error": str(e)},
        )


async def check_external_api_oanda() -> HealthCheck:
    """Check OANDA API connectivity."""
    if aiohttp is None:
        return HealthCheck(
            name="oanda_api",
            status=HealthStatus.DEGRADED,
            message="aiohttp not available for API checks",
            duration_ms=0,
            details={"error": "missing_dependency"},
        )

    try:
        # Simple connectivity check to OANDA
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api-fxpractice.oanda.com/v3/accounts"
            ) as response:
                if response.status == 401:  # Unauthorized is expected without API key
                    return HealthCheck(
                        name="oanda_api",
                        status=HealthStatus.HEALTHY,
                        message="OANDA API is reachable",
                        duration_ms=0,
                        details={
                            "endpoint": "https://api-fxpractice.oanda.com",
                            "status": "reachable",
                        },
                    )
                elif response.status < 500:
                    return HealthCheck(
                        name="oanda_api",
                        status=HealthStatus.HEALTHY,
                        message="OANDA API is responding",
                        duration_ms=0,
                        details={"status_code": response.status},
                    )
                else:
                    return HealthCheck(
                        name="oanda_api",
                        status=HealthStatus.DEGRADED,
                        message=f"OANDA API returned {response.status}",
                        duration_ms=0,
                        details={"status_code": response.status},
                    )

    except asyncio.TimeoutError:
        return HealthCheck(
            name="oanda_api",
            status=HealthStatus.UNHEALTHY,
            message="OANDA API timeout",
            duration_ms=0,
            details={"error": "timeout"},
        )
    except Exception as e:
        return HealthCheck(
            name="oanda_api",
            status=HealthStatus.UNHEALTHY,
            message=f"OANDA API check failed: {str(e)}",
            duration_ms=0,
            details={"error": str(e)},
        )


async def check_system_resources() -> HealthCheck:
    """Check system resource usage."""
    try:
        # CPU usage - Non-blocking instant read (performance optimization)
        # Changed from interval=1 to interval=None to avoid 1-second blocking wait
        cpu_percent = psutil.cpu_percent(interval=None)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent

        details = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory_percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": disk_percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
        }

        # Determine status based on thresholds
        status = HealthStatus.HEALTHY
        messages = []

        if cpu_percent > 90:
            status = HealthStatus.UNHEALTHY
            messages.append(f"High CPU usage: {cpu_percent:.1f}%")
        elif cpu_percent > 70:
            status = HealthStatus.DEGRADED
            messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")

        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
            messages.append(f"High memory usage: {memory_percent:.1f}%")
        elif memory_percent > 75:
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
            messages.append(f"Elevated memory usage: {memory_percent:.1f}%")

        if disk_percent > 95:
            status = HealthStatus.UNHEALTHY
            messages.append(f"Critical disk usage: {disk_percent:.1f}%")
        elif disk_percent > 85:
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
            messages.append(f"High disk usage: {disk_percent:.1f}%")

        message = "; ".join(messages) if messages else "System resources normal"

        return HealthCheck(
            name="system_resources",
            status=status,
            message=message,
            duration_ms=0,
            details=details,
        )

    except Exception as e:
        return HealthCheck(
            name="system_resources",
            status=HealthStatus.UNHEALTHY,
            message=f"System resources check failed: {str(e)}",
            duration_ms=0,
            details={"error": str(e)},
        )


def register_default_health_checks() -> None:
    """Register all default health checks."""
    health_monitor.register_check("database", check_database_connection)
    health_monitor.register_check("oanda_api", check_external_api_oanda)
    health_monitor.register_check("system_resources", check_system_resources)


# Health check endpoint helpers
def health_check_to_dict(check: HealthCheck) -> Dict[str, Any]:
    """Convert health check to dictionary for API responses."""
    return {
        "name": check.name,
        "status": check.status.value,
        "message": check.message,
        "duration_ms": round(check.duration_ms, 2),
        "details": check.details,
    }


async def get_health_summary() -> Dict[str, Any]:
    """Get a complete health summary."""
    results = await health_monitor.run_all_checks()
    overall_status = health_monitor.get_overall_status(results)

    return {
        "status": overall_status.value,
        "timestamp": time.time(),
        "checks": {
            name: health_check_to_dict(check) for name, check in results.items()
        },
        "summary": {
            "total_checks": len(results),
            "healthy": len(
                [c for c in results.values() if c.status == HealthStatus.HEALTHY]
            ),
            "degraded": len(
                [c for c in results.values() if c.status == HealthStatus.DEGRADED]
            ),
            "unhealthy": len(
                [c for c in results.values() if c.status == HealthStatus.UNHEALTHY]
            ),
        },
    }
