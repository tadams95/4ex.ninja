"""
Health and Performance API Endpoints

FastAPI endpoints for health checks and performance monitoring.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import time
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from infrastructure.monitoring.health import (
    health_monitor,
    get_health_summary,
    register_default_health_checks,
    HealthStatus,
)
from infrastructure.monitoring.performance import (
    performance_monitor,
    get_performance_summary,
    get_slow_operations,
)
from infrastructure.monitoring.error_tracking import SentryErrorTracker


# Initialize router
router = APIRouter(prefix="/health", tags=["health"])

# Initialize health checks
register_default_health_checks()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Quick health check endpoint.
    Returns basic system status.
    """
    try:
        # Quick checks only
        results = await health_monitor.run_all_checks()
        overall_status = health_monitor.get_overall_status(results)

        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "message": "System health check completed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check with detailed information.
    """
    try:
        return await get_health_summary()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Detailed health check failed: {str(e)}"
        )


@router.get("/check/{check_name}")
async def individual_health_check(check_name: str) -> Dict[str, Any]:
    """
    Run a specific health check.
    """
    try:
        result = await health_monitor.run_check(check_name)
        return {
            "status": result.status.value,
            "name": result.name,
            "message": result.message,
            "duration_ms": result.duration_ms,
            "details": result.details,
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Health check '{check_name}' failed: {str(e)}"
        )


@router.get("/performance")
async def performance_metrics() -> Dict[str, Any]:
    """
    Get current performance metrics.
    """
    try:
        return get_performance_summary()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Performance metrics failed: {str(e)}"
        )


@router.get("/performance/timers/{timer_name}")
async def timer_stats(timer_name: str, tags: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics for a specific timer.

    Args:
        timer_name: Name of the timer
        tags: Optional tags in format "key1=value1,key2=value2"
    """
    try:
        tag_dict = None
        if tags:
            tag_dict = {}
            for tag_pair in tags.split(","):
                if "=" in tag_pair:
                    key, value = tag_pair.split("=", 1)
                    tag_dict[key.strip()] = value.strip()

        stats = performance_monitor.get_timer_stats(timer_name, tag_dict)
        return {
            "timer_name": timer_name,
            "tags": tag_dict,
            "statistics": stats,
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timer stats failed: {str(e)}")


@router.get("/performance/metrics/{metric_name}")
async def metric_stats(metric_name: str, tags: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics for a specific metric.

    Args:
        metric_name: Name of the metric
        tags: Optional tags in format "key1=value1,key2=value2"
    """
    try:
        tag_dict = None
        if tags:
            tag_dict = {}
            for tag_pair in tags.split(","):
                if "=" in tag_pair:
                    key, value = tag_pair.split("=", 1)
                    tag_dict[key.strip()] = value.strip()

        stats = performance_monitor.get_metric_stats(metric_name, tag_dict)
        return {
            "metric_name": metric_name,
            "tags": tag_dict,
            "statistics": stats,
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metric stats failed: {str(e)}")


@router.get("/performance/slow")
async def slow_operations(threshold_ms: float = 1000) -> Dict[str, Any]:
    """
    Get operations that are slower than the threshold.

    Args:
        threshold_ms: Threshold in milliseconds (default: 1000ms)
    """
    try:
        slow_ops = get_slow_operations(threshold_ms)
        return {
            "threshold_ms": threshold_ms,
            "slow_operations": slow_ops,
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Slow operations check failed: {str(e)}"
        )


@router.post("/performance/reset")
async def reset_performance_metrics(
    metric_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Reset performance metrics.

    Args:
        metric_name: Optional specific metric to reset, otherwise reset all
    """
    try:
        performance_monitor.reset_metrics(metric_name)
        return {
            "message": f"Performance metrics reset: {metric_name or 'all'}",
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset metrics failed: {str(e)}")


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """
    Get overall system status including health and performance.
    """
    try:
        # Get health status
        health_results = await health_monitor.run_all_checks()
        health_status = health_monitor.get_overall_status(health_results)

        # Get performance summary
        performance_summary = get_performance_summary()

        # Get system metrics
        system_metrics = performance_monitor.get_all_metrics()

        return {
            "overall_status": health_status.value,
            "health": {
                "status": health_status.value,
                "checks": len(health_results),
                "healthy": len(
                    [
                        c
                        for c in health_results.values()
                        if c.status == HealthStatus.HEALTHY
                    ]
                ),
                "degraded": len(
                    [
                        c
                        for c in health_results.values()
                        if c.status == HealthStatus.DEGRADED
                    ]
                ),
                "unhealthy": len(
                    [
                        c
                        for c in health_results.values()
                        if c.status == HealthStatus.UNHEALTHY
                    ]
                ),
            },
            "performance": {
                "api_metrics": performance_summary.get("api_performance", {}),
                "signal_processing": performance_summary.get("signal_processing", {}),
                "database": performance_summary.get("database_performance", {}),
                "external_apis": performance_summary.get("external_apis", {}),
            },
            "system": system_metrics,
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System status failed: {str(e)}")


# Error tracking endpoint (if Sentry is configured)
@router.get("/errors")
async def error_summary() -> Dict[str, Any]:
    """
    Get error tracking summary (requires Sentry configuration).
    """
    try:
        # This would return error statistics from Sentry
        # For now, return a placeholder
        return {
            "message": "Error tracking available (configure Sentry DSN for detailed stats)",
            "timestamp": time.time(),
            "status": "ready",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summary failed: {str(e)}")


# Health check dependency for other endpoints
async def check_system_health():
    """Dependency to check if system is healthy enough to serve requests."""
    results = await health_monitor.run_all_checks()
    overall_status = health_monitor.get_overall_status(results)

    if overall_status == HealthStatus.UNHEALTHY:
        raise HTTPException(
            status_code=503, detail="System is unhealthy and cannot serve requests"
        )

    return overall_status
