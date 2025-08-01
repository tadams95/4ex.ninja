"""
Performance monitoring API endpoints.

This module provides API endpoints for accessing performance monitoring data,
optimization recommendations, and system health information.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

from ...infrastructure.performance_manager import get_performance_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["Performance Monitoring"])


@router.get("/status", response_model=Dict[str, Any])
async def get_performance_status() -> Dict[str, Any]:
    """
    Get comprehensive performance status across all monitoring components.

    Returns:
        Performance status and metrics
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager:
            raise HTTPException(
                status_code=503, detail="Performance monitoring not available"
            )

        status = await performance_manager.get_comprehensive_status()
        return status

    except Exception as e:
        logger.error(f"Error getting performance status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve performance status"
        )


@router.get("/query-performance", response_model=Dict[str, Any])
async def get_query_performance() -> Dict[str, Any]:
    """
    Get query performance metrics and analysis.

    Returns:
        Query performance summary and recommendations
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.query_monitor:
            raise HTTPException(
                status_code=503, detail="Query performance monitoring not available"
            )

        # Get performance summary
        summary = performance_manager.query_monitor.get_performance_summary()

        # Get optimization recommendations
        recommendations = (
            performance_manager.query_monitor.get_optimization_recommendations()
        )

        return {
            "performance_summary": summary,
            "optimization_recommendations": recommendations,
        }

    except Exception as e:
        logger.error(f"Error getting query performance: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve query performance metrics"
        )


@router.get("/cache-stats", response_model=Dict[str, Any])
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache performance statistics.

    Returns:
        Cache performance metrics
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.cache_manager:
            raise HTTPException(
                status_code=503, detail="Cache monitoring not available"
            )

        stats = await performance_manager.cache_manager.get_performance_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve cache statistics"
        )


@router.get("/connection-status", response_model=Dict[str, Any])
async def get_connection_status() -> Dict[str, Any]:
    """
    Get database connection pool status and health.

    Returns:
        Connection pool status and metrics
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.connection_monitor:
            raise HTTPException(
                status_code=503, detail="Connection monitoring not available"
            )

        status = await performance_manager.connection_monitor.get_current_status()
        return status

    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve connection status"
        )


@router.get("/optimization-analysis", response_model=Dict[str, Any])
async def get_optimization_analysis() -> Dict[str, Any]:
    """
    Get comprehensive optimization analysis and recommendations.

    Returns:
        Optimization analysis results and recommendations
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager:
            raise HTTPException(
                status_code=503, detail="Performance monitoring not available"
            )

        analysis = await performance_manager.run_optimization_analysis()
        return analysis

    except Exception as e:
        logger.error(f"Error getting optimization analysis: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve optimization analysis"
        )


@router.post("/warm-cache", response_model=Dict[str, Any])
async def warm_cache(function_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Manually trigger cache warming for specified functions.

    Args:
        function_names: Specific warming functions to run, or None for all

    Returns:
        Cache warming result
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.cache_manager:
            raise HTTPException(
                status_code=503, detail="Cache management not available"
            )

        await performance_manager.warm_cache(function_names)

        return {
            "message": "Cache warming completed successfully",
            "functions_warmed": function_names or "all",
        }

    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to warm cache")


@router.get("/connection-report", response_model=Dict[str, Any])
async def get_connection_performance_report(
    hours: int = Query(default=24, ge=1, le=168)  # 1 hour to 1 week
) -> Dict[str, Any]:
    """
    Get connection pool performance report for specified time period.

    Args:
        hours: Number of hours to include in the report (1-168)

    Returns:
        Connection performance report
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.connection_monitor:
            raise HTTPException(
                status_code=503, detail="Connection monitoring not available"
            )

        report = await performance_manager.connection_monitor.get_performance_report(
            hours
        )
        return report

    except Exception as e:
        logger.error(f"Error getting connection report: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve connection performance report"
        )


@router.get("/query-patterns", response_model=Dict[str, Any])
async def get_query_patterns() -> Dict[str, Any]:
    """
    Get query pattern analysis for optimization insights.

    Returns:
        Query pattern analysis results
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.query_analyzer:
            raise HTTPException(
                status_code=503, detail="Query optimization not available"
            )

        patterns = performance_manager.query_analyzer.analyze_patterns()
        return patterns

    except Exception as e:
        logger.error(f"Error getting query patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve query patterns")


@router.get("/index-recommendations", response_model=List[Dict[str, Any]])
async def get_index_recommendations() -> List[Dict[str, Any]]:
    """
    Get database index recommendations based on query patterns.

    Returns:
        List of index recommendations
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager or not performance_manager.query_analyzer:
            raise HTTPException(
                status_code=503, detail="Query optimization not available"
            )

        recommendations = (
            performance_manager.query_analyzer.generate_index_recommendations()
        )

        # Convert to dict format for API response
        return [
            {
                "collection": rec.collection,
                "fields": rec.fields,
                "index_type": rec.index_type,
                "reason": rec.reason,
                "potential_improvement": rec.potential_improvement,
                "priority": rec.priority,
                "frequency": rec.frequency,
                "avg_execution_time_ms": rec.avg_execution_time_ms,
            }
            for rec in recommendations
        ]

    except Exception as e:
        logger.error(f"Error getting index recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve index recommendations"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_health_status() -> Dict[str, Any]:
    """
    Get basic health status of performance monitoring components.

    Returns:
        Health status (no authentication required)
    """
    try:
        performance_manager = get_performance_manager()

        if not performance_manager:
            return {
                "status": "unavailable",
                "message": "Performance monitoring not initialized",
            }

        health_status = {
            "status": "healthy",
            "components": {
                "performance_manager": performance_manager.is_initialized,
                "query_monitoring": performance_manager.query_monitor is not None,
                "caching": performance_manager.cache_manager is not None,
                "connection_monitoring": performance_manager.connection_monitor
                is not None,
                "query_optimization": performance_manager.query_analyzer is not None,
            },
            "monitoring_active": performance_manager.is_monitoring,
        }

        # Check if any critical components are missing
        if not any(health_status["components"].values()):
            health_status["status"] = "degraded"
            health_status["message"] = "No performance components are available"

        return health_status

    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {
            "status": "error",
            "message": "Failed to check health status",
            "error": str(e),
        }
