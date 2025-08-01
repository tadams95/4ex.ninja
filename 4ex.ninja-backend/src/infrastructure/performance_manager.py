"""
Performance monitoring and optimization integration.

This module integrates all performance monitoring and optimization components,
providing a unified interface for performance management across the repository layer.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from .monitoring.query_performance import (
    QueryPerformanceMonitor,
    query_performance_monitor,
    performance_monitor_decorator,
)
from .caching.cache_manager import (
    CacheManager,
    MemoryCache,
    initialize_cache_manager,
    get_cache_manager,
)
from .monitoring.connection_pool import (
    ConnectionPoolMonitor,
    initialize_connection_monitor,
    get_connection_monitor,
)
from .optimization.query_optimizer import (
    QueryPatternAnalyzer,
    RepositoryOptimizer,
    initialize_query_optimizer,
    get_query_optimizer,
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfiguration:
    """Configuration for performance monitoring and optimization."""

    # Query performance monitoring
    enable_query_monitoring: bool = True
    query_monitor_slow_threshold_ms: int = 1000

    # Caching
    enable_caching: bool = True
    cache_default_ttl_seconds: int = 3600
    cache_max_size: int = 10000

    # Connection monitoring
    enable_connection_monitoring: bool = True
    connection_check_interval_seconds: int = 30

    # Query optimization
    enable_query_optimization: bool = True
    optimization_analysis_window_hours: int = 24
    auto_apply_optimizations: bool = False


class PerformanceManager:
    """
    Unified performance manager for all repository performance features.

    This manager coordinates query monitoring, caching, connection monitoring,
    and query optimization to provide comprehensive performance management.
    """

    def __init__(
        self, database_manager, config: Optional[PerformanceConfiguration] = None
    ):
        """
        Initialize the performance manager.

        Args:
            database_manager: Database manager instance
            config: Performance configuration
        """
        self.database_manager = database_manager
        self.config = config or PerformanceConfiguration()

        # Component instances
        self.query_monitor: Optional[QueryPerformanceMonitor] = None
        self.cache_manager: Optional[CacheManager] = None
        self.connection_monitor: Optional[ConnectionPoolMonitor] = None
        self.query_analyzer: Optional[QueryPatternAnalyzer] = None
        self.repository_optimizer: Optional[RepositoryOptimizer] = None

        # State
        self.is_initialized = False
        self.is_monitoring = False

    async def initialize(self) -> bool:
        """
        Initialize all performance components.

        Returns:
            True if initialization was successful
        """
        try:
            logger.info("Initializing performance management components")

            # Initialize query performance monitoring
            if self.config.enable_query_monitoring:
                self.query_monitor = query_performance_monitor
                self.query_monitor.slow_query_threshold_ms = (
                    self.config.query_monitor_slow_threshold_ms
                )
                logger.info("Query performance monitoring initialized")

            # Initialize caching
            if self.config.enable_caching:
                cache_backend = MemoryCache(
                    max_size=self.config.cache_max_size,
                    default_ttl_seconds=self.config.cache_default_ttl_seconds,
                )
                self.cache_manager = initialize_cache_manager(
                    backend=cache_backend,
                    default_ttl_seconds=self.config.cache_default_ttl_seconds,
                )

                # Register cache warming functions
                await self._register_cache_warming_functions()
                logger.info("Caching layer initialized")

            # Initialize connection monitoring
            if self.config.enable_connection_monitoring:
                self.connection_monitor = initialize_connection_monitor(
                    database_manager=self.database_manager,
                    check_interval_seconds=self.config.connection_check_interval_seconds,
                )

                # Add alert callback
                self.connection_monitor.add_alert_callback(
                    self._handle_connection_alert
                )
                logger.info("Connection pool monitoring initialized")

            # Initialize query optimization
            if self.config.enable_query_optimization:
                self.query_analyzer, self.repository_optimizer = (
                    initialize_query_optimizer(self.database_manager)
                )
                logger.info("Query optimization initialized")

            self.is_initialized = True
            logger.info("Performance management initialization completed")
            return True

        except Exception as e:
            logger.error(f"Error initializing performance management: {e}")
            return False

    async def start_monitoring(self) -> bool:
        """
        Start all monitoring components.

        Returns:
            True if monitoring started successfully
        """
        if not self.is_initialized:
            logger.error("Performance manager not initialized")
            return False

        try:
            logger.info("Starting performance monitoring")

            # Start connection monitoring
            if self.connection_monitor:
                await self.connection_monitor.start_monitoring()

            # Cache doesn't need explicit monitoring start

            self.is_monitoring = True
            logger.info("Performance monitoring started")
            return True

        except Exception as e:
            logger.error(f"Error starting performance monitoring: {e}")
            return False

    async def stop_monitoring(self) -> bool:
        """
        Stop all monitoring components.

        Returns:
            True if monitoring stopped successfully
        """
        try:
            logger.info("Stopping performance monitoring")

            # Stop connection monitoring
            if self.connection_monitor:
                await self.connection_monitor.stop_monitoring()

            self.is_monitoring = False
            logger.info("Performance monitoring stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping performance monitoring: {e}")
            return False

    async def _register_cache_warming_functions(self):
        """Register cache warming functions for frequently accessed data."""
        if not self.cache_manager:
            return

        # Example cache warming functions
        async def warm_market_data_cache():
            """Warm cache with recent market data."""
            try:
                # This would typically pre-load frequently accessed market data
                logger.debug("Warming market data cache")
                # Implementation would depend on your specific data patterns
            except Exception as e:
                logger.error(f"Error warming market data cache: {e}")

        async def warm_signal_cache():
            """Warm cache with recent signals."""
            try:
                logger.debug("Warming signal cache")
                # Implementation would pre-load recent signals
            except Exception as e:
                logger.error(f"Error warming signal cache: {e}")

        # Register warming functions
        self.cache_manager.register_warm_cache_function(
            "market_data", warm_market_data_cache
        )
        self.cache_manager.register_warm_cache_function("signals", warm_signal_cache)

    def _handle_connection_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Handle connection pool alerts."""
        logger.warning(
            f"Connection pool alert [{alert_type}]: {alert_data.get('message', 'Unknown alert')}"
        )

        # You could implement additional alert handling here, such as:
        # - Sending notifications
        # - Triggering automated recovery actions
        # - Scaling connection pools

    def get_performance_decorator(self):
        """
        Get the performance monitoring decorator for repository methods.

        Returns:
            Decorator function for repository methods
        """
        if self.query_monitor:
            return performance_monitor_decorator(self.query_monitor)
        else:
            # Return a no-op decorator if monitoring is disabled
            def no_op_decorator(func):
                return func

            return no_op_decorator

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive performance status across all components.

        Returns:
            Complete performance status and metrics
        """
        try:
            status = {
                "performance_manager": {
                    "initialized": self.is_initialized,
                    "monitoring_active": self.is_monitoring,
                    "config": {
                        "query_monitoring": self.config.enable_query_monitoring,
                        "caching": self.config.enable_caching,
                        "connection_monitoring": self.config.enable_connection_monitoring,
                        "query_optimization": self.config.enable_query_optimization,
                    },
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Query performance status
            if self.query_monitor:
                status["query_performance"] = (
                    self.query_monitor.get_performance_summary()
                )

            # Cache status
            if self.cache_manager:
                status["cache_performance"] = (
                    await self.cache_manager.get_performance_stats()
                )

            # Connection status
            if self.connection_monitor:
                status["connection_status"] = (
                    await self.connection_monitor.get_current_status()
                )

            # Optimization status
            if self.query_analyzer:
                status["optimization_analysis"] = self.query_analyzer.analyze_patterns()
                if self.repository_optimizer:
                    status["optimization_history"] = (
                        self.repository_optimizer.get_optimization_history()
                    )

            return status

        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {
                "error": "Failed to get performance status",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def run_optimization_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive optimization analysis and return recommendations.

        Returns:
            Optimization analysis results and recommendations
        """
        if not self.repository_optimizer:
            return {"error": "Query optimization not enabled"}

        try:
            logger.info("Running comprehensive optimization analysis")

            # Run optimization analysis
            analysis_result = (
                await self.repository_optimizer.run_optimization_analysis()
            )

            # Add performance context
            analysis_result["performance_context"] = {
                "query_performance_summary": (
                    self.query_monitor.get_performance_summary()
                    if self.query_monitor
                    else None
                ),
                "cache_stats": (
                    await self.cache_manager.get_performance_stats()
                    if self.cache_manager
                    else None
                ),
                "connection_status": (
                    await self.connection_monitor.get_current_status()
                    if self.connection_monitor
                    else None
                ),
            }

            return analysis_result

        except Exception as e:
            logger.error(f"Error running optimization analysis: {e}")
            return {"error": "Failed to run optimization analysis"}

    async def warm_cache(self, function_names: Optional[List[str]] = None):
        """
        Warm the cache with frequently accessed data.

        Args:
            function_names: Specific warming functions to run, or None for all
        """
        if self.cache_manager:
            await self.cache_manager.warm_cache(function_names)
        else:
            logger.warning("Cache manager not available for warming")

    def record_query_for_optimization(
        self,
        collection: str,
        operation: str,
        query_filter: Dict[str, Any],
        execution_time_ms: float,
        result_count: int = 0,
    ):
        """
        Record a query execution for optimization analysis.

        Args:
            collection: Collection name
            operation: Operation type
            query_filter: Query filter used
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
        """
        if self.query_analyzer:
            self.query_analyzer.record_query_execution(
                collection=collection,
                operation=operation,
                query_filter=query_filter,
                execution_time_ms=execution_time_ms,
                result_count=result_count,
            )

    async def apply_optimization_recommendations(
        self, max_optimizations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Apply optimization recommendations automatically.

        Args:
            max_optimizations: Maximum number of optimizations to apply

        Returns:
            List of optimization results
        """
        if (
            not self.repository_optimizer
            or not self.query_analyzer
            or not self.config.auto_apply_optimizations
        ):
            return []

        try:
            # Get recommendations
            recommendations = self.query_analyzer.generate_index_recommendations()

            # Apply top recommendations
            results = []
            for i, recommendation in enumerate(recommendations[:max_optimizations]):
                result = await self.repository_optimizer.apply_optimization(
                    recommendation
                )
                results.append(
                    {
                        "recommendation_index": i,
                        "collection": result.collection,
                        "description": result.description,
                        "success": result.success,
                        "error": result.error,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error applying optimization recommendations: {e}")
            return []


# Global performance manager instance
global_performance_manager: Optional[PerformanceManager] = None


def initialize_performance_manager(
    database_manager, config: Optional[PerformanceConfiguration] = None
) -> PerformanceManager:
    """Initialize the global performance manager."""
    global global_performance_manager

    global_performance_manager = PerformanceManager(database_manager, config)

    logger.info("Global performance manager initialized")
    return global_performance_manager


def get_performance_manager() -> Optional[PerformanceManager]:
    """Get the global performance manager instance."""
    return global_performance_manager
