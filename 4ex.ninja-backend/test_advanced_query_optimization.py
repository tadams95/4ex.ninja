"""
Tests for Advanced Database Query Optimization

Tests the advanced query optimization features including:
- Advanced indexing strategies
- Aggregation pipeline optimizations
- Query batching
- Materialized views
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.infrastructure.optimization.advanced_query_optimizer import (
    AdvancedIndexManager,
    CrossoverAggregationOptimizer,
    QueryBatchProcessor,
    MaterializedViewManager,
    DatabaseOptimizationManager,
    get_optimization_manager,
)


class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self.collections = {}
        self.collection_names = []

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

    async def list_collection_names(self):
        return self.collection_names

    async def create_collection(self, name, **kwargs):
        self.collection_names.append(name)
        return self[name]


class MockCollection:
    """Mock collection for testing."""

    def __init__(self, name):
        self.name = name
        self.indexes = []
        self.documents = []

    async def create_index(self, index_spec, **kwargs):
        self.indexes.append({"spec": index_spec, "options": kwargs})
        return "mock_index_name"

    def aggregate(self, pipeline, **kwargs):
        return MockCursor([])

    def find(self, query, **kwargs):
        return MockCursor([])

    async def drop(self):
        pass


class MockCursor:
    """Mock cursor for testing."""

    def __init__(self, data):
        self.data = data

    async def to_list(self, length=None):
        return self.data

    def sort(self, *args, **kwargs):
        return self

    def limit(self, limit):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.data:
            return self.data.pop(0)
        raise StopAsyncIteration


@pytest.fixture
async def mock_database():
    """Provide a mock database for testing."""
    return MockDatabase()


@pytest.fixture
async def optimization_manager(mock_database):
    """Provide an optimization manager with mock database."""
    return DatabaseOptimizationManager(mock_database)


class TestAdvancedIndexManager:
    """Test advanced index management."""

    async def test_create_advanced_indexes(self, mock_database):
        """Test creating advanced indexes."""
        manager = AdvancedIndexManager(mock_database)

        result = await manager.create_advanced_indexes()

        assert result is True
        assert len(mock_database["signals"].indexes) > 0
        assert len(mock_database["market_data"].indexes) > 0
        assert len(mock_database["strategies"].indexes) > 0

    async def test_signal_indexes_creation(self, mock_database):
        """Test signal-specific index creation."""
        manager = AdvancedIndexManager(mock_database)

        await manager._create_signal_indexes()

        signals_collection = mock_database["signals"]
        index_specs = [idx["spec"] for idx in signals_collection.indexes]

        # Check for specific index types
        text_indexes = [
            idx
            for idx in index_specs
            if any(
                isinstance(field, tuple) and field[1] == "text"
                for field in (idx if isinstance(idx, list) else [idx])
            )
        ]
        assert len(text_indexes) > 0

    async def test_market_data_indexes_creation(self, mock_database):
        """Test market data index creation."""
        manager = AdvancedIndexManager(mock_database)

        await manager._create_market_data_indexes()

        market_data_collection = mock_database["market_data"]
        assert len(market_data_collection.indexes) > 0

        # Check for time-series optimized indexes
        index_options = [idx["options"] for idx in market_data_collection.indexes]
        partial_indexes = [
            opt for opt in index_options if "partialFilterExpression" in opt
        ]
        assert len(partial_indexes) > 0


class TestCrossoverAggregationOptimizer:
    """Test crossover aggregation optimizations."""

    async def test_crossover_signals_optimized(self, mock_database):
        """Test optimized crossover signal aggregation."""
        optimizer = CrossoverAggregationOptimizer(mock_database)

        # Mock some data
        mock_data = [
            {
                "_id": "EUR_USD",
                "signals": [],
                "buy_signals": 5,
                "sell_signals": 3,
                "crossover_strength": 0.25,
                "signal_bias": "BULLISH",
            }
        ]
        mock_database["signals"].aggregate = lambda pipeline, **kwargs: MockCursor(
            mock_data
        )

        result = await optimizer.get_crossover_signals_optimized(
            pairs=["EUR_USD", "GBP_USD"], limit=10
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["_id"] == "EUR_USD"
        assert result[0]["signal_bias"] == "BULLISH"

    async def test_market_trend_analysis(self, mock_database):
        """Test market trend analysis aggregation."""
        optimizer = CrossoverAggregationOptimizer(mock_database)

        # Mock trend data
        mock_data = [
            {
                "_id": "EUR_USD",
                "trend_direction": "STRONG_BULLISH",
                "trend_strength": 0.8,
                "overall_change_pct": 2.5,
            }
        ]
        mock_database["market_data"].aggregate = lambda pipeline, **kwargs: MockCursor(
            mock_data
        )

        result = await optimizer.get_market_trend_analysis(pairs=["EUR_USD"], days=7)

        assert isinstance(result, dict)
        assert "results" in result
        assert "bullish_pairs" in result
        assert result["pairs_analyzed"] == 1


class TestQueryBatchProcessor:
    """Test query batching functionality."""

    async def test_add_query_to_batch(self, mock_database):
        """Test adding queries to batch."""
        processor = QueryBatchProcessor(mock_database, batch_size=3, batch_timeout=0.1)

        callback_id = await processor.add_query_to_batch(
            collection="signals",
            operation="find",
            filters={"pair": "EUR_USD"},
            options={"limit": 10},
        )

        assert callback_id is not None
        assert len(processor.pending_batches["signals_find"]) == 1

    async def test_batch_processing_on_size_limit(self, mock_database):
        """Test automatic batch processing when size limit is reached."""
        processor = QueryBatchProcessor(mock_database, batch_size=2, batch_timeout=1.0)

        # Add first query
        callback_id1 = await processor.add_query_to_batch(
            collection="signals", operation="find", filters={"pair": "EUR_USD"}
        )

        # Add second query (should trigger batch processing)
        callback_id2 = await processor.add_query_to_batch(
            collection="signals", operation="find", filters={"pair": "GBP_USD"}
        )

        # Batch should be processed and cleared
        await asyncio.sleep(0.01)  # Give time for processing
        assert len(processor.pending_batches["signals_find"]) == 0

    async def test_batch_timeout_processing(self, mock_database):
        """Test batch processing on timeout."""
        processor = QueryBatchProcessor(
            mock_database, batch_size=10, batch_timeout=0.05
        )

        callback_id = await processor.add_query_to_batch(
            collection="signals", operation="find", filters={"pair": "EUR_USD"}
        )

        # Wait for timeout to trigger
        await asyncio.sleep(0.1)

        # Batch should be processed and cleared
        assert len(processor.pending_batches["signals_find"]) == 0

    async def test_get_batch_result(self, mock_database):
        """Test retrieving batch results."""
        processor = QueryBatchProcessor(mock_database, batch_size=1, batch_timeout=0.1)

        # Mock the batch processing to set a result
        processor.batch_results["test_callback"] = [{"test": "result"}]

        result = await processor.get_batch_result("test_callback", timeout=1.0)

        assert result == [{"test": "result"}]

    async def test_get_batch_result_timeout(self, mock_database):
        """Test batch result timeout."""
        processor = QueryBatchProcessor(mock_database, batch_size=1, batch_timeout=0.1)

        result = await processor.get_batch_result("nonexistent_callback", timeout=0.05)

        assert result is None


class TestMaterializedViewManager:
    """Test materialized view management."""

    async def test_create_crossover_analytics_view(self, mock_database):
        """Test creating crossover analytics materialized view."""
        manager = MaterializedViewManager(mock_database)

        result = await manager.create_crossover_analytics_view()

        assert result is True
        assert "crossover_analytics_view" in manager.views
        assert len(mock_database["crossover_analytics_view"].indexes) > 0

    async def test_create_market_performance_view(self, mock_database):
        """Test creating market performance materialized view."""
        manager = MaterializedViewManager(mock_database)

        result = await manager.create_market_performance_view()

        assert result is True
        assert "market_performance_view" in manager.views
        assert len(mock_database["market_performance_view"].indexes) > 0

    async def test_query_crossover_analytics(self, mock_database):
        """Test querying crossover analytics view."""
        manager = MaterializedViewManager(mock_database)

        # Mock data
        mock_data = [{"pair": "EUR_USD", "profit_rate": 0.75, "total_signals": 20}]
        mock_database["crossover_analytics_view"].find = lambda query: MockCursor(
            mock_data
        )

        result = await manager.query_crossover_analytics(
            pairs=["EUR_USD"], min_profit_rate=0.5, limit=10
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["pair"] == "EUR_USD"

    async def test_query_market_performance(self, mock_database):
        """Test querying market performance view."""
        manager = MaterializedViewManager(mock_database)

        # Mock data
        mock_data = [
            {"pair": "GBP_USD", "daily_return_pct": 1.5, "avg_volatility": 0.02}
        ]
        mock_database["market_performance_view"].find = lambda query: MockCursor(
            mock_data
        )

        result = await manager.query_market_performance(
            pairs=["GBP_USD"], min_volatility=0.01, limit=10
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["pair"] == "GBP_USD"

    async def test_refresh_views(self, mock_database):
        """Test refreshing materialized views."""
        manager = MaterializedViewManager(mock_database)

        # Create a view with old timestamp
        old_time = datetime.utcnow() - timedelta(hours=10)
        manager.views["crossover_analytics_view"] = {
            "created": old_time,
            "refresh_interval_hours": 6,
        }

        results = await manager.refresh_views()

        assert "crossover_analytics_view" in results
        assert results["crossover_analytics_view"] is True


class TestDatabaseOptimizationManager:
    """Test the main optimization manager."""

    async def test_initialize_optimizations(self, optimization_manager):
        """Test initialization of all optimizations."""
        result = await optimization_manager.initialize_optimizations()

        assert result is True
        assert isinstance(optimization_manager.index_manager, AdvancedIndexManager)
        assert isinstance(
            optimization_manager.aggregation_optimizer, CrossoverAggregationOptimizer
        )
        assert isinstance(optimization_manager.batch_processor, QueryBatchProcessor)
        assert isinstance(optimization_manager.view_manager, MaterializedViewManager)

    async def test_get_optimization_status(self, optimization_manager):
        """Test getting optimization status."""
        status = await optimization_manager.get_optimization_status()

        assert isinstance(status, dict)
        assert "timestamp" in status
        assert "indexes" in status
        assert "materialized_views" in status
        assert "batch_processor" in status
        assert "views_info" in status

    async def test_global_optimization_manager(self, mock_database):
        """Test global optimization manager singleton."""
        manager1 = get_optimization_manager(mock_database)
        manager2 = get_optimization_manager(mock_database)

        assert manager1 is manager2  # Should be the same instance


class TestIntegrationScenarios:
    """Test complete optimization scenarios."""

    async def test_full_optimization_workflow(self, mock_database):
        """Test complete optimization workflow."""
        manager = DatabaseOptimizationManager(mock_database)

        # Initialize optimizations
        init_result = await manager.initialize_optimizations()
        assert init_result is True

        # Check that views were created
        status = await manager.get_optimization_status()
        assert status["materialized_views"]["crossover_analytics"] is True
        assert status["materialized_views"]["market_performance"] is True

        # Test batch processing
        callback_id = await manager.batch_processor.add_query_to_batch(
            collection="signals", operation="find", filters={"pair": "EUR_USD"}
        )
        assert callback_id is not None

        # Test aggregation optimization
        crossover_result = (
            await manager.aggregation_optimizer.get_crossover_signals_optimized(
                pairs=["EUR_USD", "GBP_USD"]
            )
        )
        assert isinstance(crossover_result, list)

    async def test_optimization_error_handling(self, mock_database):
        """Test error handling in optimization components."""
        manager = DatabaseOptimizationManager(mock_database)

        # Test with database that raises exceptions
        def raise_exception(*args, **kwargs):
            raise Exception("Database error")

        mock_database["signals"].aggregate = raise_exception

        # Should handle errors gracefully
        result = await manager.aggregation_optimizer.get_crossover_signals_optimized(
            pairs=["EUR_USD"]
        )
        assert result == []

    async def test_performance_measurement(self, mock_database):
        """Test that optimizations include performance measurement."""
        manager = DatabaseOptimizationManager(mock_database)

        start_time = datetime.utcnow()

        # Run optimization operations
        await manager.initialize_optimizations()

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Should complete reasonably quickly (within 5 seconds for mock operations)
        assert execution_time < 5.0


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Test performance characteristics of optimizations."""

    async def test_batch_processing_performance(self, mock_database):
        """Test batch processing performance."""
        processor = QueryBatchProcessor(mock_database, batch_size=50, batch_timeout=0.1)

        start_time = datetime.utcnow()

        # Add multiple queries
        callback_ids = []
        for i in range(100):
            callback_id = await processor.add_query_to_batch(
                collection="signals", operation="find", filters={"pair": f"PAIR_{i}"}
            )
            callback_ids.append(callback_id)

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Should be able to queue 100 queries quickly
        assert execution_time < 1.0
        assert len(callback_ids) == 100

    async def test_aggregation_pipeline_efficiency(self, mock_database):
        """Test aggregation pipeline efficiency."""
        optimizer = CrossoverAggregationOptimizer(mock_database)

        # Mock large dataset response
        large_dataset = [{"_id": f"PAIR_{i}", "signals": []} for i in range(1000)]
        mock_database["signals"].aggregate = lambda pipeline, **kwargs: MockCursor(
            large_dataset
        )

        start_time = datetime.utcnow()

        result = await optimizer.get_crossover_signals_optimized(
            pairs=[f"PAIR_{i}" for i in range(100)], limit=50
        )

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Should handle large datasets efficiently
        assert execution_time < 2.0
        assert len(result) == 1000  # Mock returns all data


if __name__ == "__main__":
    # Run basic functionality test
    async def main():
        mock_db = MockDatabase()
        manager = DatabaseOptimizationManager(mock_db)

        print("Testing database optimization initialization...")
        result = await manager.initialize_optimizations()
        print(f"Initialization result: {result}")

        print("Testing optimization status...")
        status = await manager.get_optimization_status()
        print(f"Status: {status}")

        print("All tests completed successfully!")

    asyncio.run(main())
