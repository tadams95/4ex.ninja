"""
Enhanced Repository Integration with Advanced Query Optimization

This module provides integration between the existing repository pattern
and the new advanced query optimization features.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from .advanced_query_optimizer import (
    DatabaseOptimizationManager,
    get_optimization_manager,
)

if TYPE_CHECKING:
    from ..repositories.mongo_base_repository import MongoBaseRepository

logger = logging.getLogger(__name__)


class OptimizedRepositoryMixin:
    """
    Mixin class to add optimization capabilities to existing repositories.

    This mixin can be added to any repository to enable:
    - Query batching
    - Optimized aggregations
    - Materialized view querying

    Note: This mixin expects to be used with MongoBaseRepository or compatible repositories.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._optimization_manager: Optional[DatabaseOptimizationManager] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def optimization_manager(self) -> Optional[DatabaseOptimizationManager]:
        """Get the optimization manager, creating it if needed."""
        if self._optimization_manager is None and hasattr(self, "_database"):
            try:
                database = getattr(self, "_database")
                self._optimization_manager = get_optimization_manager(database)
            except Exception as e:
                self.logger.warning(f"Failed to initialize optimization manager: {e}")
        return self._optimization_manager

    async def find_with_batching(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Any]:
        """
        Find entities using query batching for improved performance.

        Args:
            filters: Query filters
            limit: Maximum number of results
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            List of entities
        """
        if not self.optimization_manager or not hasattr(self, "find_by_criteria"):
            # Fallback to regular find
            return await getattr(self, "find_by_criteria")(
                filters, limit, None, sort_by, sort_order
            )

        try:
            # Prepare query options
            options = {}
            if limit:
                options["limit"] = limit
            if sort_by:
                options["sort"] = {sort_by: 1 if sort_order == "asc" else -1}

            # Add to batch
            collection_name = getattr(self, "_collection_name", "unknown")
            callback_id = (
                await self.optimization_manager.batch_processor.add_query_to_batch(
                    collection=collection_name,
                    operation="find",
                    filters=filters,
                    options=options,
                )
            )

            # Get batched result
            result = await self.optimization_manager.batch_processor.get_batch_result(
                callback_id, timeout=5.0
            )

            if result is None:
                # Fallback to regular query
                self.logger.warning(
                    f"Batch query timeout, falling back to regular query"
                )
                return await getattr(self, "find_by_criteria")(
                    filters, limit, None, sort_by, sort_order
                )

            if isinstance(result, dict) and "error" in result:
                self.logger.error(f"Batch query error: {result['error']}")
                return await getattr(self, "find_by_criteria")(
                    filters, limit, None, sort_by, sort_order
                )

            # Convert documents to entities
            entities = []
            if hasattr(self, "_dict_to_entity") and isinstance(result, list):
                dict_to_entity = getattr(self, "_dict_to_entity")
                for doc in result:
                    entity = dict_to_entity(doc)
                    if entity:
                        entities.append(entity)
            elif isinstance(result, list):
                entities = result
            else:
                entities = []

            return entities

        except Exception as e:
            self.logger.error(f"Batched find failed: {e}")
            # Fallback to regular find
            return await getattr(self, "find_by_criteria")(
                filters, limit, None, sort_by, sort_order
            )

    async def count_with_batching(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count entities using query batching.

        Args:
            filters: Query filters

        Returns:
            Count of matching entities
        """
        if not self.optimization_manager or not hasattr(self, "count"):
            return await getattr(self, "count")(filters)

        try:
            collection_name = getattr(self, "_collection_name", "unknown")
            callback_id = (
                await self.optimization_manager.batch_processor.add_query_to_batch(
                    collection=collection_name,
                    operation="count",
                    filters=filters or {},
                    options={},
                )
            )

            result = await self.optimization_manager.batch_processor.get_batch_result(
                callback_id, timeout=5.0
            )

            if result is None or isinstance(result, dict):
                return await getattr(self, "count")(filters)

            return int(result)

        except Exception as e:
            self.logger.error(f"Batched count failed: {e}")
            return await getattr(self, "count")(filters)


class OptimizedSignalRepositoryMixin(OptimizedRepositoryMixin):
    """Signal repository optimization mixin with crossover-specific features."""

    async def get_crossover_analysis(
        self, pairs: List[str], timeframe: str = "1h", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get optimized crossover analysis using aggregation pipelines.

        Args:
            pairs: Currency pairs to analyze
            timeframe: Timeframe for analysis
            limit: Maximum results

        Returns:
            Crossover analysis results
        """
        if not self.optimization_manager:
            self.logger.warning("Optimization manager not available, using basic query")
            return await self._basic_crossover_analysis(pairs, limit)

        try:
            return await self.optimization_manager.aggregation_optimizer.get_crossover_signals_optimized(
                pairs=pairs, timeframe=timeframe, limit=limit
            )
        except Exception as e:
            self.logger.error(f"Optimized crossover analysis failed: {e}")
            return await self._basic_crossover_analysis(pairs, limit)

    async def _basic_crossover_analysis(
        self, pairs: List[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback basic crossover analysis."""
        try:
            # Simple aggregation without optimization
            results = []
            if not hasattr(self, "find_by_criteria"):
                return results

            find_by_criteria = getattr(self, "find_by_criteria")
            for pair in pairs[:limit]:
                signals = await find_by_criteria(
                    {"pair": pair, "status": {"$in": ["ACTIVE", "FILLED"]}}, limit=20
                )

                buy_count = len(
                    [
                        s
                        for s in signals
                        if hasattr(s, "signal_type") and s.signal_type.value == "BUY"
                    ]
                )
                sell_count = len(
                    [
                        s
                        for s in signals
                        if hasattr(s, "signal_type") and s.signal_type.value == "SELL"
                    ]
                )

                results.append(
                    {
                        "_id": pair,
                        "buy_signals": buy_count,
                        "sell_signals": sell_count,
                        "total_signals": len(signals),
                        "signal_bias": (
                            "BULLISH"
                            if buy_count > sell_count
                            else "BEARISH" if sell_count > buy_count else "NEUTRAL"
                        ),
                    }
                )

            return results
        except Exception as e:
            self.logger.error(f"Basic crossover analysis failed: {e}")
            return []

    async def get_crossover_analytics_from_view(
        self,
        pairs: Optional[List[str]] = None,
        min_profit_rate: float = 0.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query crossover analytics from materialized view.

        Args:
            pairs: Filter by currency pairs
            min_profit_rate: Minimum profit rate filter
            limit: Maximum results

        Returns:
            Analytics from materialized view
        """
        if not self.optimization_manager:
            return []

        try:
            return (
                await self.optimization_manager.view_manager.query_crossover_analytics(
                    pairs=pairs, min_profit_rate=min_profit_rate, limit=limit
                )
            )
        except Exception as e:
            self.logger.error(f"Failed to query crossover analytics view: {e}")
            return []


class OptimizedMarketDataRepositoryMixin(OptimizedRepositoryMixin):
    """Market data repository optimization mixin."""

    async def get_market_trend_analysis(
        self, pairs: List[str], days: int = 7
    ) -> Dict[str, Any]:
        """
        Get optimized market trend analysis.

        Args:
            pairs: Currency pairs to analyze
            days: Number of days to analyze

        Returns:
            Market trend analysis
        """
        if not self.optimization_manager:
            return {"error": "Optimization manager not available"}

        try:
            return await self.optimization_manager.aggregation_optimizer.get_market_trend_analysis(
                pairs=pairs, days=days
            )
        except Exception as e:
            self.logger.error(f"Market trend analysis failed: {e}")
            return {"error": str(e)}

    async def get_market_performance_from_view(
        self,
        pairs: Optional[List[str]] = None,
        min_volatility: float = 0.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query market performance from materialized view.

        Args:
            pairs: Filter by currency pairs
            min_volatility: Minimum volatility filter
            limit: Maximum results

        Returns:
            Performance data from materialized view
        """
        if not self.optimization_manager:
            return []

        try:
            return (
                await self.optimization_manager.view_manager.query_market_performance(
                    pairs=pairs, min_volatility=min_volatility, limit=limit
                )
            )
        except Exception as e:
            self.logger.error(f"Failed to query market performance view: {e}")
            return []


class OptimizedQueryBuilder:
    """Builder for creating optimized database queries."""

    def __init__(self, optimization_manager: DatabaseOptimizationManager):
        self.optimization_manager = optimization_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def build_crossover_query(
        self,
        pairs: List[str],
        date_range: Optional[tuple] = None,
        signal_types: Optional[List[str]] = None,
        status_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build an optimized query for crossover analysis.

        Args:
            pairs: Currency pairs
            date_range: Tuple of (start_date, end_date)
            signal_types: List of signal types to include
            status_filter: List of statuses to include

        Returns:
            Optimized query dictionary
        """
        query = {"pair": {"$in": pairs}}

        if date_range:
            start_date, end_date = date_range
            query["created_at"] = {"$gte": start_date, "$lte": end_date}

        if signal_types:
            query["signal_type"] = {"$in": signal_types}

        if status_filter:
            query["status"] = {"$in": status_filter}
        else:
            # Default to active statuses for performance
            query["status"] = {"$in": ["ACTIVE", "FILLED"]}

        return query

    def build_market_data_query(
        self,
        pairs: List[str],
        timeframes: Optional[List[str]] = None,
        date_range: Optional[tuple] = None,
        volume_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Build an optimized query for market data.

        Args:
            pairs: Currency pairs
            timeframes: List of timeframes
            date_range: Tuple of (start_date, end_date)
            volume_threshold: Minimum volume threshold

        Returns:
            Optimized query dictionary
        """
        query: Dict[str, Any] = {"pair": {"$in": pairs}}

        if timeframes:
            query["timeframe"] = {"$in": timeframes}

        if date_range:
            start_date, end_date = date_range
            query["timestamp"] = {"$gte": start_date, "$lte": end_date}

        if volume_threshold:
            query["volume"] = {"$gte": volume_threshold}

        return query


def create_optimization_middleware():
    """
    Create middleware for automatic query optimization.

    Returns:
        Middleware function for FastAPI
    """

    async def optimization_middleware(request, call_next):
        """Middleware to enable query optimization for requests."""
        try:
            # Add optimization context to request
            if hasattr(request.state, "database"):
                request.state.optimization_manager = get_optimization_manager(
                    request.state.database
                )

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Optimization middleware error: {e}")
            # Don't fail the request due to optimization issues
            response = await call_next(request)
            return response

    return optimization_middleware


# Utility functions for integration
async def initialize_repository_optimizations(database) -> bool:
    """
    Initialize optimizations for repository layer.

    Args:
        database: MongoDB database instance

    Returns:
        bool: True if successful
    """
    try:
        optimization_manager = get_optimization_manager(database)
        return await optimization_manager.initialize_optimizations()
    except Exception as e:
        logger.error(f"Failed to initialize repository optimizations: {e}")
        return False


async def get_optimization_health_status(database) -> Dict[str, Any]:
    """
    Get health status of all optimizations.

    Args:
        database: MongoDB database instance

    Returns:
        Health status dictionary
    """
    try:
        optimization_manager = get_optimization_manager(database)
        status = await optimization_manager.get_optimization_status()

        # Add health indicators
        health = {
            "overall_health": "healthy",
            "optimizations_active": True,
            "materialized_views_count": sum(
                1 for v in status.get("materialized_views", {}).values() if v
            ),
            "pending_batches": status.get("batch_processor", {}).get(
                "pending_batches", 0
            ),
            "details": status,
        }

        # Determine overall health
        if health["materialized_views_count"] == 0:
            health["overall_health"] = "degraded"
            health["optimizations_active"] = False
        elif health["pending_batches"] > 100:
            health["overall_health"] = "warning"

        return health

    except Exception as e:
        logger.error(f"Failed to get optimization health status: {e}")
        return {
            "overall_health": "unhealthy",
            "optimizations_active": False,
            "error": str(e),
        }


# Export commonly used optimization utilities
__all__ = [
    "OptimizedRepositoryMixin",
    "OptimizedSignalRepositoryMixin",
    "OptimizedMarketDataRepositoryMixin",
    "OptimizedQueryBuilder",
    "create_optimization_middleware",
    "initialize_repository_optimizations",
    "get_optimization_health_status",
]
