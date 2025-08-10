"""
Performance API endpoints.

This module provides comprehensive API endpoints for performance monitoring,
Web Vitals tracking, trading-specific performance metrics, system metrics,
and business metrics.
"""

import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from infrastructure.monitoring.performance import performance_monitor
    from infrastructure.monitoring.health import health_monitor
    from infrastructure.monitoring.system_metrics import system_metrics_monitor
    from infrastructure.monitoring.business_metrics import business_metrics_monitor
except ImportError:
    # Fallback for development/testing
    performance_monitor = None
    health_monitor = None
    system_metrics_monitor = None
    business_metrics_monitor = None

router = APIRouter(prefix="/performance", tags=["performance"])
logger = logging.getLogger(__name__)


class WebVitalMetric(BaseModel):
    """Web Vital metric from frontend."""

    type: str
    name: str
    value: float
    rating: str
    session_id: str
    url: str
    user_agent: str
    timestamp: Optional[float] = None


class CustomMetric(BaseModel):
    """Custom performance metric."""

    name: str
    value: float
    tags: Optional[Dict[str, str]] = None
    timestamp: Optional[float] = None


@router.post("/web-vitals")
async def record_web_vital(metric: WebVitalMetric) -> Dict[str, Any]:
    """
    Record Web Vital metrics from frontend.
    """
    try:
        if not performance_monitor:
            return {"status": "success", "message": "Performance monitoring not available"}
            
        # Convert and store the metric
        performance_monitor.record_metric(
            name=f"web_vital_{metric.name.lower()}",
            value=metric.value,
            tags={
                "rating": metric.rating,
                "session_id": metric.session_id,
                "url": metric.url,
                "user_agent": metric.user_agent[:100],  # Truncate user agent
            },
        )

        logger.info(
            f"Recorded Web Vital: {metric.name} = {metric.value} ({metric.rating})"
        )

        return {"status": "success", "message": "Web Vital recorded"}

    except Exception as e:
        logger.error(f"Error recording Web Vital: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record Web Vital")


@router.post("/metrics")
async def record_custom_metric(metric: CustomMetric) -> Dict[str, Any]:
    """
    Record custom performance metrics.
    """
    try:
        if not performance_monitor:
            return {"status": "success", "message": "Performance monitoring not available"}
            
        performance_monitor.record_metric(
            name=metric.name, value=metric.value, tags=metric.tags or {}
        )

        logger.debug(f"Recorded custom metric: {metric.name} = {metric.value}")

        return {"status": "success", "message": "Metric recorded"}

    except Exception as e:
        logger.error(f"Error recording custom metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record metric")


@router.get("/", response_model=Dict[str, Any])
async def get_performance_overview() -> Dict[str, Any]:
    """
    Get comprehensive performance overview.
    """
    try:
        logger.info("Fetching performance overview")

        # Check if monitoring is available
        if not performance_monitor or not health_monitor:
            return {
                "status": "operational",
                "timestamp": time.time(),
                "message": "Performance monitoring not fully available",
                "performance_summary": {},
                "uptime_metrics": {},
                "system_info": {
                    "total_requests": 0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0,
                },
                "web_vitals": {
                    "lcp_p95": 0.0,
                    "cls_avg": 0.0,
                    "inp_p95": 0.0,
                },
            }

        # Get current performance summary
        summary = performance_monitor.get_performance_summary()

        # Get health status
        health_results = await health_monitor.run_all_checks()
        overall_health = health_monitor.get_overall_status(health_results)

        # Calculate uptime and availability
        uptime_metrics = performance_monitor.get_uptime_metrics()

        return {
            "status": overall_health.value,
            "timestamp": time.time(),
            "performance_summary": summary,
            "uptime_metrics": uptime_metrics,
            "system_info": {
                "total_requests": performance_monitor.get_counter_value(
                    "http_requests_total"
                ),
                "error_rate": performance_monitor.get_gauge_value("error_rate"),
                "avg_response_time": performance_monitor.get_gauge_value(
                    "avg_response_time"
                ),
            },
            "web_vitals": {
                "lcp_p95": performance_monitor.get_percentile("web_vital_lcp", 95),
                "cls_avg": performance_monitor.get_average("web_vital_cls"),
                "inp_p95": performance_monitor.get_percentile("web_vital_inp", 95),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching performance overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance data")


@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get detailed performance metrics with filtering.
    """
    try:
        logger.info("Fetching detailed performance metrics")

        # Check if monitoring is available
        if not performance_monitor:
            return {
                "timestamp": time.time(),
                "message": "Performance monitoring not available",
                "metrics_by_type": {},
                "statistics": {},
                "system_metrics": {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "disk_usage": 0.0,
                },
                "api_metrics": {
                    "requests_per_minute": 0,
                    "average_response_time": 0.0,
                    "error_rate": 0.0,
                    "slow_queries": 0,
                },
            }

        # Get all performance metrics
        recent_metrics = performance_monitor.get_recent_metrics(minutes=60)

        # Group metrics by type
        metrics_by_type = {}
        for metric in recent_metrics:
            metric_type = metric.get("type", "unknown")
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric)

        # Calculate statistics
        stats = {}
        for metric_type, type_metrics in metrics_by_type.items():
            if type_metrics:
                values = [m.get("value", 0) for m in type_metrics]
                stats[metric_type] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "recent_count": len(
                        [
                            m
                            for m in type_metrics
                            if m.get("timestamp", 0) > time.time() - 300
                        ]
                    ),
                }

        return {
            "timestamp": time.time(),
            "metrics_by_type": metrics_by_type,
            "statistics": stats,
            "system_metrics": {
                "cpu_usage": performance_monitor.get_gauge_value("cpu_usage"),
                "memory_usage": performance_monitor.get_gauge_value("memory_usage"),
                "disk_usage": performance_monitor.get_gauge_value("disk_usage"),
            },
            "api_metrics": {
                "requests_per_minute": performance_monitor.get_counter_value(
                    "requests_per_minute"
                ),
                "average_response_time": performance_monitor.get_gauge_value(
                    "avg_response_time"
                ),
                "error_rate": performance_monitor.get_gauge_value("error_rate"),
                "slow_queries": performance_monitor.get_counter_value("slow_queries"),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")


@router.get("/budgets", response_model=Dict[str, Any])
async def get_performance_budgets() -> Dict[str, Any]:
    """
    Get performance budget status and alerts.
    """
    try:
        # Define performance budgets
        budgets = {
            "web_vital_lcp": {
                "threshold": 2500,
                "unit": "ms",
                "name": "Largest Contentful Paint",
            },
            "web_vital_cls": {
                "threshold": 0.1,
                "unit": "score",
                "name": "Cumulative Layout Shift",
            },
            "web_vital_inp": {
                "threshold": 200,
                "unit": "ms",
                "name": "Interaction to Next Paint",
            },
            "api_response_time": {
                "threshold": 1000,
                "unit": "ms",
                "name": "API Response Time",
            },
            "signal_processing_time": {
                "threshold": 2000,
                "unit": "ms",
                "name": "Signal Processing",
            },
        }

        budget_status = {}
        alerts = []

        # Check if monitoring is available
        if not performance_monitor:
            return {
                "timestamp": time.time(),
                "message": "Performance monitoring not available",
                "budgets": budgets,
                "status": "unknown",
                "alerts": [],
                "overall_score": 0
            }

        for budget_name, budget_config in budgets.items():
            current_value = None
            status = "unknown"

            if budget_name.startswith("web_vital_"):
                current_value = performance_monitor.get_percentile(budget_name, 95)
            else:
                current_value = performance_monitor.get_average(budget_name)

            if current_value is not None:
                if current_value <= budget_config["threshold"]:
                    status = "good"
                elif current_value <= budget_config["threshold"] * 1.5:
                    status = "warning"
                else:
                    status = "critical"
                    alerts.append(
                        {
                            "metric": budget_name,
                            "name": budget_config["name"],
                            "current": current_value,
                            "threshold": budget_config["threshold"],
                            "severity": "critical",
                        }
                    )

            budget_status[budget_name] = {
                "name": budget_config["name"],
                "threshold": budget_config["threshold"],
                "unit": budget_config["unit"],
                "current": current_value,
                "status": status,
            }

        return {
            "timestamp": time.time(),
            "budgets": budget_status,
            "alerts": alerts,
            "overall_status": "critical" if alerts else "good",
        }

    except Exception as e:
        logger.error(f"Error fetching performance budgets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch budgets")


@router.get("/trends/{metric_name}")
async def get_metric_trends(metric_name: str, hours: int = 24) -> Dict[str, Any]:
    """
    Get performance trends for a specific metric over time.
    """
    try:
        # Check if monitoring is available
        if not performance_monitor:
            return {
                "metric_name": metric_name,
                "time_range_hours": hours,
                "message": "Performance monitoring not available",
                "data_points": [],
                "trend": "unknown",
                "change_percent": 0,
                "summary": {
                    "min": None,
                    "max": None,
                    "avg": None,
                },
            }

        # Get historical data for the metric
        end_time = time.time()
        start_time = end_time - (hours * 3600)

        historical_data = performance_monitor.get_metric_history(
            metric_name, start_time, end_time
        )

        # Calculate trend analysis
        if len(historical_data) > 1:
            values = [point["value"] for point in historical_data]
            trend = "improving" if values[-1] < values[0] else "degrading"
            change_percent = (
                ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            )
        else:
            trend = "insufficient_data"
            change_percent = 0

        return {
            "metric_name": metric_name,
            "time_range_hours": hours,
            "data_points": historical_data,
            "trend": trend,
            "change_percent": round(change_percent, 2),
            "summary": {
                "min": (
                    min(historical_data, key=lambda x: x["value"])["value"]
                    if historical_data
                    else None
                ),
                "max": (
                    max(historical_data, key=lambda x: x["value"])["value"]
                    if historical_data
                    else None
                ),
                "avg": (
                    sum(point["value"] for point in historical_data)
                    / len(historical_data)
                    if historical_data
                    else None
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching metric trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trends")


# Enhanced Metrics Endpoints

@router.get("/system", response_model=Dict[str, Any])
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get comprehensive system resource metrics.
    """
    try:
        if not system_metrics_monitor:
            return {"error": "System metrics monitoring not available"}
            
        current_metrics = system_metrics_monitor.get_current_metrics()
        if not current_metrics:
            return {"error": "No current system metrics available"}
            
        summary = system_metrics_monitor.get_metrics_summary(minutes=60)
        health_status = system_metrics_monitor.get_health_status()
        
        return {
            "timestamp": time.time(),
            "current": {
                "cpu_percent": current_metrics.cpu_percent,
                "memory_percent": current_metrics.memory_percent,
                "memory_used_mb": current_metrics.memory_used_mb,
                "memory_available_mb": current_metrics.memory_available_mb,
                "disk_usage_percent": current_metrics.disk_usage_percent,
                "disk_free_gb": current_metrics.disk_free_gb,
                "process_count": current_metrics.process_count,
                "open_file_descriptors": current_metrics.open_file_descriptors
            },
            "summary_60min": summary,
            "health_status": health_status
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/business", response_model=Dict[str, Any])
async def get_business_metrics() -> Dict[str, Any]:
    """
    Get comprehensive business performance metrics.
    """
    try:
        if not business_metrics_monitor:
            return {"error": "Business metrics monitoring not available"}
            
        comprehensive_summary = business_metrics_monitor.get_comprehensive_summary()
        return comprehensive_summary
        
    except Exception as e:
        logger.error(f"Error getting business metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get business metrics")


@router.get("/signals", response_model=Dict[str, Any])
async def get_signal_metrics() -> Dict[str, Any]:
    """
    Get signal processing performance metrics.
    """
    try:
        if not business_metrics_monitor:
            return {"error": "Business metrics monitoring not available"}
            
        signal_summary = business_metrics_monitor.get_signal_metrics_summary()
        return signal_summary
        
    except Exception as e:
        logger.error(f"Error getting signal metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get signal metrics")


@router.get("/api-performance", response_model=Dict[str, Any])
async def get_api_performance_metrics() -> Dict[str, Any]:
    """
    Get API endpoint performance metrics.
    """
    try:
        if not business_metrics_monitor:
            return {"error": "Business metrics monitoring not available"}
            
        api_summary = business_metrics_monitor.get_api_metrics_summary()
        return {
            "timestamp": time.time(),
            "api_endpoints": api_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting API performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API performance metrics")


@router.get("/cache-metrics", response_model=Dict[str, Any])
async def get_cache_metrics() -> Dict[str, Any]:
    """
    Get cache performance metrics.
    """
    try:
        if not business_metrics_monitor:
            return {"error": "Business metrics monitoring not available"}
            
        cache_summary = business_metrics_monitor.get_cache_metrics_summary()
        return {
            "timestamp": time.time(),
            "cache_performance": cache_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting cache metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cache metrics")


@router.get("/database-performance", response_model=Dict[str, Any])
async def get_database_performance_metrics() -> Dict[str, Any]:
    """
    Get database performance metrics.
    """
    try:
        if not business_metrics_monitor:
            return {"error": "Business metrics monitoring not available"}
            
        db_summary = business_metrics_monitor.get_database_performance_summary()
        return {
            "timestamp": time.time(),
            "database_performance": db_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting database performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get database performance metrics")


@router.post("/system/start-monitoring")
async def start_system_monitoring(interval_seconds: int = 30) -> Dict[str, Any]:
    """
    Start system metrics monitoring.
    """
    try:
        if not system_metrics_monitor:
            raise HTTPException(status_code=503, detail="System metrics monitoring not available")
            
        await system_metrics_monitor.start_monitoring(interval_seconds)
        return {
            "status": "success",
            "message": f"System monitoring started with {interval_seconds}s interval"
        }
        
    except Exception as e:
        logger.error(f"Error starting system monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start system monitoring")


@router.post("/system/stop-monitoring")
async def stop_system_monitoring() -> Dict[str, Any]:
    """
    Stop system metrics monitoring.
    """
    try:
        if not system_metrics_monitor:
            raise HTTPException(status_code=503, detail="System metrics monitoring not available")
            
        await system_metrics_monitor.stop_monitoring()
        return {
            "status": "success",
            "message": "System monitoring stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping system monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop system monitoring")


@router.post("/reset")
async def reset_metrics() -> Dict[str, Any]:
    """
    Reset all metrics (useful for testing and maintenance).
    """
    try:
        reset_count = 0
        
        if business_metrics_monitor:
            business_metrics_monitor.reset_metrics()
            reset_count += 1
            
        if performance_monitor and hasattr(performance_monitor, 'reset_metrics'):
            performance_monitor.reset_metrics()
            reset_count += 1
            
        return {
            "status": "success",
            "message": f"Reset {reset_count} metric monitors",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset metrics")
