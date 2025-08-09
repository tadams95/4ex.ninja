"""
Performance API endpoints.

This module provides comprehensive API endpoints for performance monitoring,
Web Vitals tracking, and trading-specific performance metrics.
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

from infrastructure.monitoring.performance import performance_monitor
from infrastructure.monitoring.health import health_monitor

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
