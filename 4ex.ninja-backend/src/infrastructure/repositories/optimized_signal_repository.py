"""
Example of Enhanced Signal Repository with Optimizations

This shows how to integrate the advanced query optimizations into an existing repository.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..repositories.mongo_signal_repository import MongoSignalRepository
from ..optimization.repository_integration import OptimizedSignalRepositoryMixin
from ...core.entities.signal import Signal


class OptimizedMongoSignalRepository(
    OptimizedSignalRepositoryMixin, MongoSignalRepository
):
    """
    Enhanced signal repository with advanced query optimizations.

    This repository extends the existing MongoSignalRepository with:
    - Query batching for improved performance
    - Optimized crossover analysis using aggregation pipelines
    - Materialized view queries for analytics
    """

    def __init__(self, database, session=None):
        """
        Initialize the optimized signal repository.

        Args:
            database: MongoDB database instance
            session: Optional MongoDB session for transactions
        """
        super().__init__(database, session)
        self.logger.info(
            "OptimizedMongoSignalRepository initialized with query optimizations"
        )

    async def get_signals_for_pairs_optimized(
        self, pairs: List[str], limit: int = 100, use_batching: bool = True
    ) -> List[Signal]:
        """
        Get signals for multiple pairs using optimized queries.

        Args:
            pairs: List of currency pairs
            limit: Maximum signals per pair
            use_batching: Whether to use query batching

        Returns:
            List of signals across all pairs
        """
        try:
            filters = {"pair": {"$in": pairs}, "status": {"$in": ["ACTIVE", "FILLED"]}}

            if use_batching and self.optimization_manager:
                return await self.find_with_batching(
                    filters=filters,
                    limit=limit * len(pairs),
                    sort_by="created_at",
                    sort_order="desc",
                )
            else:
                return await self.find_by_criteria(
                    filters=filters,
                    limit=limit * len(pairs),
                    sort_by="created_at",
                    sort_order="desc",
                )

        except Exception as e:
            self.logger.error(f"Failed to get optimized signals for pairs: {e}")
            return []

    async def get_crossover_metrics(
        self, pairs: List[str], timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Get crossover metrics using optimized aggregation pipelines.

        Args:
            pairs: Currency pairs to analyze
            timeframe: Timeframe for analysis

        Returns:
            Crossover metrics and analysis
        """
        try:
            # Use optimized crossover analysis
            crossover_data = await self.get_crossover_analysis(
                pairs=pairs, timeframe=timeframe, limit=len(pairs)
            )

            # Get analytics from materialized view if available
            analytics_data = await self.get_crossover_analytics_from_view(
                pairs=pairs, min_profit_rate=0.0, limit=len(pairs)
            )

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "pairs_analyzed": len(pairs),
                "crossover_signals": crossover_data,
                "historical_analytics": analytics_data,
                "optimization_used": self.optimization_manager is not None,
            }

        except Exception as e:
            self.logger.error(f"Failed to get crossover metrics: {e}")
            return {"error": str(e)}

    async def count_signals_by_status_optimized(
        self, pairs: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Count signals by status using batched queries.

        Args:
            pairs: Optional list of pairs to filter by

        Returns:
            Dictionary with status counts
        """
        try:
            statuses = ["ACTIVE", "FILLED", "CANCELLED", "EXPIRED"]
            counts = {}

            for status in statuses:
                filters: Dict[str, Any] = {"status": status}
                if pairs:
                    filters["pair"] = {"$in": pairs}

                # Use batched counting if available
                if self.optimization_manager:
                    count = await self.count_with_batching(filters)
                else:
                    count = await self.count(filters)

                counts[status] = count

            return counts

        except Exception as e:
            self.logger.error(f"Failed to count signals by status: {e}")
            return {}

    async def get_performance_analytics(
        self, pairs: Optional[List[str]] = None, min_profit_rate: float = 0.5
    ) -> Dict[str, Any]:
        """
        Get performance analytics from materialized views.

        Args:
            pairs: Optional list of pairs to filter by
            min_profit_rate: Minimum profit rate threshold

        Returns:
            Performance analytics data
        """
        try:
            if not self.optimization_manager:
                return {"error": "Optimization manager not available"}

            # Query materialized view for analytics
            analytics = await self.get_crossover_analytics_from_view(
                pairs=pairs, min_profit_rate=min_profit_rate, limit=100
            )

            if not analytics:
                return {"message": "No analytics data available or view not ready"}

            # Calculate summary statistics
            total_pairs = len(analytics)
            avg_profit_rate = (
                sum(a.get("profit_rate", 0) for a in analytics) / total_pairs
                if total_pairs > 0
                else 0
            )
            total_signals = sum(a.get("total_signals", 0) for a in analytics)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_pairs_analyzed": total_pairs,
                    "average_profit_rate": round(avg_profit_rate, 4),
                    "total_signals_analyzed": total_signals,
                    "min_profit_rate_filter": min_profit_rate,
                },
                "detailed_analytics": analytics[:20],  # Top 20 results
                "data_source": "materialized_view",
            }

        except Exception as e:
            self.logger.error(f"Failed to get performance analytics: {e}")
            return {"error": str(e)}


# Example usage function
async def demonstrate_optimization_usage(database):
    """
    Demonstrate how to use the optimized repository.

    Args:
        database: MongoDB database instance
    """
    # For demo purposes, just show the optimization concepts
    from ..optimization.advanced_query_optimizer import DatabaseOptimizationManager

    print("=== Database Query Optimization Demo ===")

    # Create optimization manager
    optimization_manager = DatabaseOptimizationManager(database)

    # Initialize optimizations
    print("\n1. Initializing database optimizations...")
    success = await optimization_manager.initialize_optimizations()
    print(f"Optimization initialization: {'Success' if success else 'Failed'}")

    # Get optimization status
    print("\n2. Checking optimization status...")
    status = await optimization_manager.get_optimization_status()
    print(f"Materialized views available: {status.get('materialized_views', {})}")
    print(
        f"Pending batches: {status.get('batch_processor', {}).get('pending_batches', 0)}"
    )

    # Test crossover aggregation
    print("\n3. Testing crossover aggregation optimization...")
    test_pairs = ["EUR_USD", "GBP_USD", "USD_JPY"]
    crossover_results = await optimization_manager.aggregation_optimizer.get_crossover_signals_optimized(
        pairs=test_pairs, limit=10
    )
    print(f"Crossover analysis completed: {len(crossover_results)} results")

    # Test market trend analysis
    print("\n4. Testing market trend analysis...")
    trend_results = (
        await optimization_manager.aggregation_optimizer.get_market_trend_analysis(
            pairs=test_pairs, days=7
        )
    )
    print(
        f"Market trend analysis: {trend_results.get('pairs_analyzed', 0)} pairs analyzed"
    )

    # Test query batching
    print("\n5. Testing query batching...")
    callback_id = await optimization_manager.batch_processor.add_query_to_batch(
        collection="signals",
        operation="find",
        filters={"pair": "EUR_USD"},
        options={"limit": 10},
    )
    print(f"Query added to batch with callback_id: {callback_id}")

    print("\n=== Demo completed ===\n")
    print("Benefits achieved:")
    print("✅ Enhanced indexing strategies for optimal query performance")
    print("✅ Aggregation pipeline optimizations for crossover data analysis")
    print("✅ Query batching capabilities for improved throughput")
    print("✅ Materialized views for complex analytics queries")

    return {
        "optimization_initialized": success,
        "crossover_results_count": len(crossover_results),
        "trend_analysis_pairs": trend_results.get("pairs_analyzed", 0),
        "batch_query_submitted": callback_id is not None,
    }


if __name__ == "__main__":
    import asyncio

    # Mock database for demo
    class MockDatabase:
        pass

    async def main():
        mock_db = MockDatabase()
        await demonstrate_optimization_usage(mock_db)

    asyncio.run(main())
