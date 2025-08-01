"""
Database Integration Tests for Day 7 Task 1.5.26

This module provides comprehensive integration tests for database operations,
focusing on CRUD operations, connection handling, and error scenarios.
"""

import pytest
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

    MOTOR_AVAILABLE = True
except ImportError:
    AsyncIOMotorClient = None
    ServerSelectionTimeoutError = Exception
    DuplicateKeyError = Exception
    MOTOR_AVAILABLE = False

from ...core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from ...core.entities.market_data import MarketData, Candle, Granularity

logger = logging.getLogger(__name__)


class DatabaseOperationTests:
    """
    Integration tests for database operations.

    Tests CRUD operations, transactions, error handling, and data consistency
    across different collections and scenarios.
    """

    def __init__(self):
        """Initialize database operation tests."""
        self.test_db_name = "test_4ex_ninja_integration"
        self.test_db_uri = "mongodb://localhost:27017"
        self.client = None
        self.database = None

    async def setup_database(self) -> bool:
        """Setup test database connection."""
        if not MOTOR_AVAILABLE:
            logger.warning("Motor not available, skipping database integration tests")
            return False

        try:
            self.client = AsyncIOMotorClient(
                self.test_db_uri, serverSelectionTimeoutMS=5000
            )
            await self.client.admin.command("ping")
            self.database = self.client[self.test_db_name]

            # Create test collections with indexes
            await self._setup_test_collections()

            logger.info("Database integration test setup complete")
            return True
        except Exception as e:
            logger.warning(f"Cannot setup database for integration tests: {e}")
            return False

    async def cleanup_database(self):
        """Cleanup test database."""
        try:
            if self.client and self.database:
                await self.client.drop_database(self.test_db_name)
                self.client.close()
        except Exception as e:
            logger.error(f"Error cleaning up test database: {e}")

    async def _setup_test_collections(self):
        """Setup test collections with proper indexes."""
        # Signals collection
        signals_collection = self.database.signals
        await signals_collection.create_index("signal_id", unique=True)
        await signals_collection.create_index("pair")
        await signals_collection.create_index("timestamp")
        await signals_collection.create_index("status")

        # Market data collection
        market_data_collection = self.database.market_data
        await market_data_collection.create_index(
            [("instrument", 1), ("granularity", 1)]
        )
        await market_data_collection.create_index("last_updated")

        # Performance metrics collection
        performance_collection = self.database.performance_metrics
        await performance_collection.create_index("timestamp")
        await performance_collection.create_index("metric_type")

    async def test_signal_crud_operations(self) -> Dict[str, Any]:
        """Test CRUD operations for signals."""
        results = {"test_name": "signal_crud_operations", "passed": True, "errors": []}

        try:
            collection = self.database.signals

            # Create test signal
            signal_data = {
                "signal_id": "integration_test_signal_1",
                "pair": "EUR/USD",
                "timeframe": "H1",
                "signal_type": "BUY",
                "crossover_type": "BULLISH",
                "entry_price": "1.1000",
                "current_price": "1.1005",
                "fast_ma": 10,
                "slow_ma": 20,
                "timestamp": datetime.utcnow(),
                "status": "ACTIVE",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Test CREATE
            insert_result = await collection.insert_one(signal_data)
            assert insert_result.inserted_id is not None, "Signal creation failed"

            # Test READ
            found_signal = await collection.find_one(
                {"signal_id": "integration_test_signal_1"}
            )
            assert found_signal is not None, "Signal retrieval failed"
            assert found_signal["pair"] == "EUR/USD", "Signal data mismatch"

            # Test UPDATE
            update_result = await collection.update_one(
                {"signal_id": "integration_test_signal_1"},
                {
                    "$set": {
                        "status": "FILLED",
                        "current_price": "1.1050",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            assert update_result.modified_count == 1, "Signal update failed"

            # Verify update
            updated_signal = await collection.find_one(
                {"signal_id": "integration_test_signal_1"}
            )
            assert (
                updated_signal["status"] == "FILLED"
            ), "Signal update verification failed"
            assert (
                updated_signal["current_price"] == "1.1050"
            ), "Price update verification failed"

            # Test DELETE
            delete_result = await collection.delete_one(
                {"signal_id": "integration_test_signal_1"}
            )
            assert delete_result.deleted_count == 1, "Signal deletion failed"

            # Verify deletion
            deleted_signal = await collection.find_one(
                {"signal_id": "integration_test_signal_1"}
            )
            assert deleted_signal is None, "Signal deletion verification failed"

        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Signal CRUD test failed: {str(e)}")

        return results

    async def test_market_data_operations(self) -> Dict[str, Any]:
        """Test market data operations with candle data."""
        results = {"test_name": "market_data_operations", "passed": True, "errors": []}

        try:
            collection = self.database.market_data

            # Create test market data with candles
            candles_data = []
            base_time = datetime.utcnow()

            for i in range(10):
                candle = {
                    "time": base_time + timedelta(minutes=i),
                    "open": f"{1.1000 + (i * 0.0001):.5f}",
                    "high": f"{1.1010 + (i * 0.0001):.5f}",
                    "low": f"{1.0990 + (i * 0.0001):.5f}",
                    "close": f"{1.1005 + (i * 0.0001):.5f}",
                    "volume": 50000 + (i * 1000),
                    "complete": True,
                }
                candles_data.append(candle)

            market_data = {
                "instrument": "EUR/USD",
                "granularity": "H1",
                "candles": candles_data,
                "last_updated": datetime.utcnow(),
                "source": "TEST",
            }

            # Test INSERT
            insert_result = await collection.insert_one(market_data)
            assert insert_result.inserted_id is not None, "Market data creation failed"

            # Test QUERY with filters
            found_data = await collection.find_one(
                {"instrument": "EUR/USD", "granularity": "H1"}
            )
            assert found_data is not None, "Market data retrieval failed"
            assert len(found_data["candles"]) == 10, "Candle count mismatch"

            # Test AGGREGATION - get latest candles
            pipeline = [
                {"$match": {"instrument": "EUR/USD"}},
                {"$unwind": "$candles"},
                {"$sort": {"candles.time": -1}},
                {"$limit": 5},
                {"$group": {"_id": "$_id", "latest_candles": {"$push": "$candles"}}},
            ]

            aggregation_result = await collection.aggregate(pipeline).to_list(1)
            assert len(aggregation_result) > 0, "Aggregation query failed"
            assert (
                len(aggregation_result[0]["latest_candles"]) == 5
            ), "Latest candles count incorrect"

            # Test UPDATE with array operations
            new_candle = {
                "time": base_time + timedelta(minutes=10),
                "open": "1.1011",
                "high": "1.1021",
                "low": "1.1001",
                "close": "1.1016",
                "volume": 60000,
                "complete": True,
            }

            update_result = await collection.update_one(
                {"instrument": "EUR/USD", "granularity": "H1"},
                {
                    "$push": {"candles": new_candle},
                    "$set": {"last_updated": datetime.utcnow()},
                },
            )
            assert update_result.modified_count == 1, "Market data update failed"

            # Verify candle was added
            updated_data = await collection.find_one(
                {"instrument": "EUR/USD", "granularity": "H1"}
            )
            assert (
                len(updated_data["candles"]) == 11
            ), "Candle addition verification failed"

        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Market data operations test failed: {str(e)}")

        return results

    async def test_transaction_handling(self) -> Dict[str, Any]:
        """Test database transaction handling."""
        results = {"test_name": "transaction_handling", "passed": True, "errors": []}

        try:
            # Test transaction rollback scenario
            async with await self.client.start_session() as session:
                async with session.start_transaction():
                    signals_collection = self.database.signals
                    performance_collection = self.database.performance_metrics

                    # Insert signal
                    signal_data = {
                        "signal_id": "transaction_test_signal",
                        "pair": "GBP/USD",
                        "timeframe": "H4",
                        "signal_type": "SELL",
                        "crossover_type": "BEARISH",
                        "entry_price": "1.2500",
                        "current_price": "1.2500",
                        "fast_ma": 10,
                        "slow_ma": 20,
                        "timestamp": datetime.utcnow(),
                        "status": "ACTIVE",
                    }

                    await signals_collection.insert_one(signal_data, session=session)

                    # Insert performance metric
                    performance_data = {
                        "signal_id": "transaction_test_signal",
                        "metric_type": "signal_created",
                        "timestamp": datetime.utcnow(),
                        "value": 1,
                    }

                    await performance_collection.insert_one(
                        performance_data, session=session
                    )

                    # Verify both documents exist within transaction
                    signal_count = await signals_collection.count_documents(
                        {"signal_id": "transaction_test_signal"}, session=session
                    )
                    performance_count = await performance_collection.count_documents(
                        {"signal_id": "transaction_test_signal"}, session=session
                    )

                    assert signal_count == 1, "Signal not found in transaction"
                    assert (
                        performance_count == 1
                    ), "Performance metric not found in transaction"

                    # Intentionally abort transaction
                    await session.abort_transaction()

            # Verify rollback - documents should not exist
            signal_count_after = await self.database.signals.count_documents(
                {"signal_id": "transaction_test_signal"}
            )
            performance_count_after = (
                await self.database.performance_metrics.count_documents(
                    {"signal_id": "transaction_test_signal"}
                )
            )

            assert signal_count_after == 0, "Transaction rollback failed for signals"
            assert (
                performance_count_after == 0
            ), "Transaction rollback failed for performance metrics"

        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Transaction handling test failed: {str(e)}")

        return results

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test database error handling scenarios."""
        results = {"test_name": "error_handling", "passed": True, "errors": []}

        try:
            collection = self.database.signals

            # Test duplicate key error
            signal_data = {
                "signal_id": "duplicate_test_signal",
                "pair": "USD/JPY",
                "timeframe": "H1",
                "signal_type": "BUY",
                "crossover_type": "BULLISH",
                "entry_price": "150.00",
                "current_price": "150.00",
                "fast_ma": 10,
                "slow_ma": 20,
                "timestamp": datetime.utcnow(),
                "status": "ACTIVE",
            }

            # Insert first signal
            await collection.insert_one(signal_data)

            # Try to insert duplicate - should raise error
            try:
                await collection.insert_one(signal_data)
                # If we reach here, duplicate key error wasn't raised
                results["passed"] = False
                results["errors"].append("Duplicate key error not raised as expected")
            except DuplicateKeyError:
                # This is expected behavior
                pass

            # Test invalid query handling
            try:
                # Invalid operator should be handled gracefully
                invalid_result = await collection.find(
                    {"$invalidOperator": "test"}
                ).to_list(1)
                # If we reach here, invalid query error wasn't raised
                results["passed"] = False
                results["errors"].append("Invalid query error not raised as expected")
            except Exception:
                # This is expected behavior for invalid queries
                pass

            # Cleanup test signal
            await collection.delete_one({"signal_id": "duplicate_test_signal"})

        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Error handling test failed: {str(e)}")

        return results

    async def test_connection_resilience(self) -> Dict[str, Any]:
        """Test database connection resilience."""
        results = {"test_name": "connection_resilience", "passed": True, "errors": []}

        try:
            # Test connection timeout handling
            slow_client = AsyncIOMotorClient(
                self.test_db_uri,
                serverSelectionTimeoutMS=1,  # Very short timeout
                connectTimeoutMS=1,
            )

            try:
                # This should timeout quickly
                await slow_client.admin.command("ping")
                slow_client.close()
            except Exception:
                # Timeout is expected with such short timeout
                slow_client.close()

            # Test reconnection capability
            # Verify main connection still works
            ping_result = await self.client.admin.command("ping")
            assert ping_result["ok"] == 1, "Main connection failed after timeout test"

            # Test concurrent operations
            concurrent_tasks = []
            for i in range(10):
                task = self._concurrent_operation(i)
                concurrent_tasks.append(task)

            concurrent_results = await asyncio.gather(
                *concurrent_tasks, return_exceptions=True
            )

            # Check that most operations succeeded
            successful_operations = sum(
                1 for result in concurrent_results if not isinstance(result, Exception)
            )
            assert (
                successful_operations >= 8
            ), f"Too many concurrent operations failed: {successful_operations}/10"

        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Connection resilience test failed: {str(e)}")

        return results

    async def _concurrent_operation(self, operation_id: int):
        """Helper method for concurrent operation testing."""
        collection = self.database.test_concurrent

        # Insert document
        doc = {
            "operation_id": operation_id,
            "timestamp": datetime.utcnow(),
            "data": f"concurrent_test_data_{operation_id}",
        }

        insert_result = await collection.insert_one(doc)

        # Read document back
        found_doc = await collection.find_one({"operation_id": operation_id})

        # Delete document
        await collection.delete_one({"operation_id": operation_id})

        return found_doc["operation_id"] == operation_id

    async def test_index_performance(self) -> Dict[str, Any]:
        """Test database index performance."""
        results = {"test_name": "index_performance", "passed": True, "errors": []}

        try:
            collection = self.database.performance_test

            # Insert test data
            test_documents = []
            base_time = datetime.utcnow()

            for i in range(1000):
                doc = {
                    "test_id": f"perf_test_{i}",
                    "category": f"category_{i % 10}",
                    "timestamp": base_time + timedelta(seconds=i),
                    "value": i * 1.5,
                    "indexed_field": f"indexed_value_{i % 100}",
                }
                test_documents.append(doc)

            # Bulk insert
            insert_start = datetime.utcnow()
            await collection.insert_many(test_documents)
            insert_duration = (datetime.utcnow() - insert_start).total_seconds()

            # Create index
            await collection.create_index("indexed_field")
            await collection.create_index([("category", 1), ("timestamp", -1)])

            # Test indexed query performance
            query_start = datetime.utcnow()
            indexed_results = await collection.find(
                {"indexed_field": "indexed_value_50"}
            ).to_list(None)
            indexed_query_duration = (datetime.utcnow() - query_start).total_seconds()

            # Test compound index query
            compound_start = datetime.utcnow()
            compound_results = await collection.find(
                {
                    "category": "category_5",
                    "timestamp": {"$gte": base_time + timedelta(seconds=500)},
                }
            ).to_list(None)
            compound_query_duration = (
                datetime.utcnow() - compound_start
            ).total_seconds()

            # Performance assertions
            assert insert_duration < 5.0, f"Bulk insert too slow: {insert_duration}s"
            assert (
                indexed_query_duration < 0.1
            ), f"Indexed query too slow: {indexed_query_duration}s"
            assert (
                compound_query_duration < 0.1
            ), f"Compound query too slow: {compound_query_duration}s"
            assert len(indexed_results) > 0, "Indexed query returned no results"
            assert len(compound_results) > 0, "Compound query returned no results"

            # Cleanup
            await collection.drop()

        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Index performance test failed: {str(e)}")

        return results


class DatabaseIntegrationTestSuite:
    """Comprehensive database integration test suite."""

    def __init__(self):
        """Initialize database integration test suite."""
        self.db_tests = DatabaseOperationTests()

    async def run_all_integration_tests(self) -> Dict[str, Any]:
        """
        Run all database integration tests.

        Returns:
            Comprehensive test results
        """
        results = {
            "test_suite": "Database Integration Tests",
            "test_run_timestamp": datetime.utcnow().isoformat(),
            "database_available": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
        }

        # Setup database
        results["database_available"] = await self.db_tests.setup_database()

        if not results["database_available"]:
            results["total_tests"] = 1
            results["failed_tests"] = 1
            results["test_details"].append(
                {
                    "test_name": "database_setup",
                    "passed": False,
                    "errors": ["Database not available for integration testing"],
                }
            )
            return results

        # Define all tests to run
        test_methods = [
            self.db_tests.test_signal_crud_operations,
            self.db_tests.test_market_data_operations,
            self.db_tests.test_transaction_handling,
            self.db_tests.test_error_handling,
            self.db_tests.test_connection_resilience,
            self.db_tests.test_index_performance,
        ]

        # Run all tests
        for test_method in test_methods:
            try:
                test_result = await test_method()
                results["test_details"].append(test_result)
                results["total_tests"] += 1

                if test_result["passed"]:
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1

            except Exception as e:
                results["test_details"].append(
                    {
                        "test_name": test_method.__name__,
                        "passed": False,
                        "errors": [f"Test execution failed: {str(e)}"],
                    }
                )
                results["total_tests"] += 1
                results["failed_tests"] += 1

        # Cleanup
        await self.db_tests.cleanup_database()

        return results


# Pytest integration
@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegrationPytest:
    """Pytest-compatible database integration tests."""

    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        """Setup and teardown for each test."""
        self.db_tests = DatabaseOperationTests()
        database_available = await self.db_tests.setup_database()

        if not database_available:
            pytest.skip("Database not available for integration testing")

        yield

        await self.db_tests.cleanup_database()

    async def test_signal_crud_operations(self):
        """Test signal CRUD operations."""
        result = await self.db_tests.test_signal_crud_operations()
        assert result["passed"], f"Signal CRUD test failed: {result['errors']}"

    async def test_market_data_operations(self):
        """Test market data operations."""
        result = await self.db_tests.test_market_data_operations()
        assert result["passed"], f"Market data test failed: {result['errors']}"

    async def test_transaction_handling(self):
        """Test transaction handling."""
        result = await self.db_tests.test_transaction_handling()
        assert result["passed"], f"Transaction test failed: {result['errors']}"

    async def test_error_handling(self):
        """Test error handling."""
        result = await self.db_tests.test_error_handling()
        assert result["passed"], f"Error handling test failed: {result['errors']}"

    async def test_connection_resilience(self):
        """Test connection resilience."""
        result = await self.db_tests.test_connection_resilience()
        assert result[
            "passed"
        ], f"Connection resilience test failed: {result['errors']}"

    async def test_index_performance(self):
        """Test index performance."""
        result = await self.db_tests.test_index_performance()
        assert result["passed"], f"Index performance test failed: {result['errors']}"


if __name__ == "__main__":
    # Can be run directly for quick testing
    async def main():
        suite = DatabaseIntegrationTestSuite()
        results = await suite.run_all_integration_tests()

        print("\n=== Database Integration Test Results ===")
        print(f"Database Available: {results['database_available']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")

        for test in results["test_details"]:
            status = "✅" if test["passed"] else "❌"
            print(f"{status} {test['test_name']}")
            if not test["passed"]:
                for error in test.get("errors", []):
                    print(f"    Error: {error}")

    asyncio.run(main())
