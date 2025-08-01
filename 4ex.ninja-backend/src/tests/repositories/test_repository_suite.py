"""
Comprehensive repository test suite with test database setup.

This module provides complete testing infrastructure for all repository implementations,
including test database setup, data fixtures, and comprehensive test coverage.
"""

import pytest
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from dataclasses import dataclass
import logging
from decimal import Decimal

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from pymongo.errors import ServerSelectionTimeoutError

    MOTOR_AVAILABLE = True
except ImportError:
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None
    ServerSelectionTimeoutError = Exception
    MOTOR_AVAILABLE = False

from ...core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from ...core.entities.market_data import MarketData, Candle, Granularity
from ...core.entities.strategy import (
    StrategyType,
    StrategyStatus,
    StrategyParameters,
    StrategyPerformance,
)
from ...infrastructure.repositories.mongo_signal_repository import MongoSignalRepository
from ...infrastructure.repositories.mongo_market_data_repository import (
    MongoMarketDataRepository,
)
from ...infrastructure.repositories.mongo_strategy_repository import (
    MongoStrategyRepository,
)

logger = logging.getLogger(__name__)


@dataclass
class TestConfiguration:
    """Configuration for repository tests."""

    test_db_name: str = "test_4ex_ninja"
    test_db_uri: str = "mongodb://localhost:27017"
    timeout_seconds: int = 5
    cleanup_after_tests: bool = True
    use_in_memory_db: bool = False


class TestDatabaseManager:
    """
    Manages test database setup, teardown, and fixtures.

    Provides isolated test environments with proper cleanup
    and data fixture management.
    """

    def __init__(self, config: Optional[TestConfiguration] = None):
        """Initialize test database manager."""
        self.config = config or TestConfiguration()
        self.client = None
        self.database = None

    async def setup_test_database(self) -> bool:
        """
        Setup test database with schema and indexes.

        Returns:
            True if setup successful
        """
        if not MOTOR_AVAILABLE:
            logger.error("Motor not available for database testing")
            return False

        try:
            # Connect to test database
            self.client = AsyncIOMotorClient(
                self.config.test_db_uri,
                serverSelectionTimeoutMS=self.config.timeout_seconds * 1000,
            )

            # Test connection
            await self.client.admin.command("ping")

            # Get test database
            self.database = self.client[self.config.test_db_name]

            logger.info(f"Test database '{self.config.test_db_name}' setup complete")
            return True

        except ServerSelectionTimeoutError:
            logger.error(
                "Cannot connect to MongoDB for testing. Please ensure MongoDB is running."
            )
            return False
        except Exception as e:
            logger.error(f"Error setting up test database: {e}")
            return False

    async def cleanup_test_database(self) -> bool:
        """
        Cleanup test database and close connections.

        Returns:
            True if cleanup successful
        """
        try:
            if self.config.cleanup_after_tests and self.database:
                # Drop test database
                await self.client.drop_database(self.config.test_db_name)
                logger.info(f"Test database '{self.config.test_db_name}' dropped")

            if self.client:
                self.client.close()

            return True

        except Exception as e:
            logger.error(f"Error cleaning up test database: {e}")
            return False

    async def clear_collections(
        self, collection_names: Optional[List[str]] = None
    ) -> bool:
        """
        Clear specific collections or all collections.

        Args:
            collection_names: List of collections to clear, or None for all

        Returns:
            True if successful
        """
        try:
            if not self.database:
                return False

            if collection_names is None:
                collection_names = await self.database.list_collection_names()

            for collection_name in collection_names:
                await self.database[collection_name].delete_many({})

            logger.debug(f"Cleared collections: {collection_names}")
            return True

        except Exception as e:
            logger.error(f"Error clearing collections: {e}")
            return False


class RepositoryTestFixtures:
    """
    Provides test data fixtures for repository testing.

    Creates realistic test data for signals, market data, and strategies.
    """

    @staticmethod
    def create_test_signals(count: int = 5) -> List[Signal]:
        """Create test signal entities."""
        signals = []
        base_time = datetime.utcnow()

        for i in range(count):
            signal = Signal(
                signal_id=f"test_signal_{i+1}",
                pair=["EUR/USD", "GBP/USD", "USD/JPY"][i % 3],
                timeframe="H1",
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                crossover_type=(
                    CrossoverType.BULLISH if i % 2 == 0 else CrossoverType.BEARISH
                ),
                entry_price=Decimal("1.1000") + Decimal(str(i * 0.0010)),
                current_price=Decimal("1.1005") + Decimal(str(i * 0.0010)),
                fast_ma=10 + i,
                slow_ma=20 + (i * 2),
                timestamp=base_time + timedelta(minutes=i * 15),
                stop_loss=Decimal("1.0950") + Decimal(str(i * 0.0010)),
                take_profit=Decimal("1.1100") + Decimal(str(i * 0.0010)),
                atr_value=Decimal("0.0025"),
                confidence_score=0.75 + (i * 0.05),
                status=SignalStatus.ACTIVE if i < 3 else SignalStatus.FILLED,
                strategy_name=f"test_strategy_{(i % 2) + 1}",
            )
            signals.append(signal)

        return signals

    @staticmethod
    def create_test_market_data(count: int = 10) -> List[MarketData]:
        """Create test market data entities."""
        market_data = []
        base_time = datetime.utcnow()

        for i in range(count):
            candles = []
            for j in range(5):  # 5 candles per market data entry
                candle_time = base_time + timedelta(hours=i, minutes=j * 15)
                candle = Candle(
                    time=candle_time,
                    open=Decimal("1.1000") + Decimal(str(j * 0.0001)),
                    high=Decimal("1.1010") + Decimal(str(j * 0.0001)),
                    low=Decimal("1.0990") + Decimal(str(j * 0.0001)),
                    close=Decimal("1.1005") + Decimal(str(j * 0.0001)),
                    volume=50000 + (j * 1000),
                )
                candles.append(candle)

            data = MarketData(
                instrument=["EUR/USD", "GBP/USD", "USD/JPY"][i % 3],
                granularity=Granularity.H1,
                candles=candles,
            )
            market_data.append(data)

        return market_data

    @staticmethod
    def create_test_strategies(count: int = 3) -> List[Strategy]:
        """Create test strategy entities."""
        strategies = []
        base_time = datetime.utcnow()

        strategy_types = [
            StrategyType.MA_CROSSOVER,
            StrategyType.BREAKOUT,
            StrategyType.MEAN_REVERSION,
        ]
        statuses = [
            StrategyStatus.ACTIVE,
            StrategyStatus.PAUSED,
            StrategyStatus.INACTIVE,
        ]

        for i in range(count):
            strategy = Strategy(
                strategy_id=f"test_strategy_{i+1}",
                name=f"Test Strategy {i+1}",
                description=f"Test strategy for automated testing purposes {i+1}",
                strategy_type=strategy_types[i % len(strategy_types)],
                parameters={
                    "short_ma": 10 + i,
                    "long_ma": 20 + (i * 5),
                    "atr_multiplier": 1.5 + (i * 0.1),
                    "risk_per_trade": 0.01 + (i * 0.005),
                },
                currency_pairs=["EUR/USD", "GBP/USD"],
                timeframe="H1",
                status=statuses[i % len(statuses)],
                created_at=base_time - timedelta(days=i * 7),
                last_executed_at=base_time - timedelta(hours=i) if i < 2 else None,
                performance_metrics={
                    "total_signals": 100 + (i * 50),
                    "win_rate": 0.65 + (i * 0.05),
                    "total_pnl": 1000.0 + (i * 500.0),
                    "max_drawdown": 0.05 + (i * 0.01),
                    "sharpe_ratio": 1.2 + (i * 0.3),
                },
                tags=["test", f"category_{i+1}"],
            )
            strategies.append(strategy)

        return strategies


class BaseRepositoryTest:
    """
    Base class for repository tests with common setup and utilities.

    Provides shared test infrastructure and helper methods.
    """

    def __init__(self):
        """Initialize base repository test."""
        self.db_manager = TestDatabaseManager()
        self.fixtures = RepositoryTestFixtures()

    async def setup_method(self):
        """Setup method called before each test."""
        success = await self.db_manager.setup_test_database()
        if not success:
            pytest.skip("MongoDB not available for testing")

    async def teardown_method(self):
        """Teardown method called after each test."""
        await self.db_manager.cleanup_test_database()

    async def clear_test_data(self):
        """Clear all test data from collections."""
        await self.db_manager.clear_collections()


class TestSignalRepository(BaseRepositoryTest):
    """Comprehensive tests for SignalRepository implementation."""

    async def setup_method(self):
        """Setup signal repository tests."""
        await super().setup_method()
        self.repository = MongoSignalRepository(
            database=self.db_manager.database, collection_name="test_signals"
        )
        self.test_signals = self.fixtures.create_test_signals()

    async def test_create_signal(self):
        """Test signal creation."""
        signal = self.test_signals[0]

        created_signal = await self.repository.create(signal)

        assert created_signal is not None
        assert created_signal.signal_id == signal.signal_id
        assert created_signal.currency_pair == signal.currency_pair
        assert created_signal.signal_type == signal.signal_type

    async def test_get_signal_by_id(self):
        """Test signal retrieval by ID."""
        signal = self.test_signals[0]
        await self.repository.create(signal)

        retrieved_signal = await self.repository.get_by_id(signal.signal_id)

        assert retrieved_signal is not None
        assert retrieved_signal.signal_id == signal.signal_id
        assert retrieved_signal.currency_pair == signal.currency_pair

    async def test_update_signal(self):
        """Test signal updates."""
        signal = self.test_signals[0]
        created_signal = await self.repository.create(signal)

        # Update signal
        created_signal.status = SignalStatus.EXECUTED
        created_signal.exit_price = 1.1050
        created_signal.pnl = 50.0

        updated_signal = await self.repository.update(created_signal)

        assert updated_signal.status == SignalStatus.EXECUTED
        assert updated_signal.exit_price == 1.1050
        assert updated_signal.pnl == 50.0

    async def test_delete_signal(self):
        """Test signal deletion."""
        signal = self.test_signals[0]
        await self.repository.create(signal)

        success = await self.repository.delete(signal.signal_id)
        assert success

        deleted_signal = await self.repository.get_by_id(signal.signal_id)
        assert deleted_signal is None

    async def test_find_signals_by_strategy(self):
        """Test finding signals by strategy."""
        # Create multiple signals
        for signal in self.test_signals[:3]:
            await self.repository.create(signal)

        strategy_signals = await self.repository.find_by_strategy("test_strategy_1")

        assert len(strategy_signals) >= 1
        for signal in strategy_signals:
            assert signal.strategy_id == "test_strategy_1"

    async def test_find_signals_by_currency_pair(self):
        """Test finding signals by currency pair."""
        # Create multiple signals
        for signal in self.test_signals[:3]:
            await self.repository.create(signal)

        eur_usd_signals = await self.repository.find_by_currency_pair("EUR/USD")

        assert len(eur_usd_signals) >= 1
        for signal in eur_usd_signals:
            assert signal.currency_pair == "EUR/USD"

    async def test_bulk_create_signals(self):
        """Test bulk signal creation."""
        created_signals = await self.repository.bulk_create(self.test_signals)

        assert len(created_signals) == len(self.test_signals)
        for i, signal in enumerate(created_signals):
            assert signal.signal_id == self.test_signals[i].signal_id


class TestMarketDataRepository(BaseRepositoryTest):
    """Comprehensive tests for MarketDataRepository implementation."""

    async def setup_method(self):
        """Setup market data repository tests."""
        await super().setup_method()
        self.repository = MongoMarketDataRepository(
            database=self.db_manager.database, collection_name="test_market_data"
        )
        self.test_market_data = self.fixtures.create_test_market_data()

    async def test_create_market_data(self):
        """Test market data creation."""
        market_data = self.test_market_data[0]

        created_data = await self.repository.create(market_data)

        assert created_data is not None
        assert created_data.market_data_id == market_data.market_data_id
        assert created_data.currency_pair == market_data.currency_pair
        assert len(created_data.candles) == len(market_data.candles)

    async def test_get_latest_candles(self):
        """Test retrieving latest candles."""
        # Create market data
        for data in self.test_market_data[:2]:
            await self.repository.create(data)

        latest_candles = await self.repository.get_latest_candles(
            currency_pair="EUR/USD", timeframe=Timeframe.H1, limit=5
        )

        assert len(latest_candles) <= 5
        # Verify candles are sorted by timestamp descending
        for i in range(len(latest_candles) - 1):
            assert latest_candles[i].timestamp >= latest_candles[i + 1].timestamp

    async def test_get_candles_for_date_range(self):
        """Test retrieving candles for date range."""
        # Create market data
        market_data = self.test_market_data[0]
        await self.repository.create(market_data)

        start_date = market_data.candles[0].timestamp
        end_date = market_data.candles[-1].timestamp

        candles = await self.repository.get_candles_for_date_range(
            currency_pair=market_data.currency_pair,
            timeframe=market_data.timeframe,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(candles) > 0
        for candle in candles:
            assert start_date <= candle.timestamp <= end_date


class TestStrategyRepository(BaseRepositoryTest):
    """Comprehensive tests for StrategyRepository implementation."""

    async def setup_method(self):
        """Setup strategy repository tests."""
        await super().setup_method()
        self.repository = MongoStrategyRepository(
            database=self.db_manager.database, collection_name="test_strategies"
        )
        self.test_strategies = self.fixtures.create_test_strategies()

    async def test_create_strategy(self):
        """Test strategy creation."""
        strategy = self.test_strategies[0]

        created_strategy = await self.repository.create(strategy)

        assert created_strategy is not None
        assert created_strategy.strategy_id == strategy.strategy_id
        assert created_strategy.name == strategy.name
        assert created_strategy.strategy_type == strategy.strategy_type

    async def test_find_active_strategies(self):
        """Test finding active strategies."""
        # Create strategies with different statuses
        for strategy in self.test_strategies:
            await self.repository.create(strategy)

        active_strategies = await self.repository.find_active_strategies()

        assert len(active_strategies) >= 1
        for strategy in active_strategies:
            assert strategy.status == StrategyStatus.ACTIVE

    async def test_update_strategy_performance(self):
        """Test updating strategy performance metrics."""
        strategy = self.test_strategies[0]
        created_strategy = await self.repository.create(strategy)

        new_metrics = {"total_signals": 150, "win_rate": 0.75, "total_pnl": 1500.0}

        updated_strategy = await self.repository.update_performance_metrics(
            strategy_id=created_strategy.strategy_id, metrics=new_metrics
        )

        assert updated_strategy.performance_metrics["total_signals"] == 150
        assert updated_strategy.performance_metrics["win_rate"] == 0.75
        assert updated_strategy.performance_metrics["total_pnl"] == 1500.0


class RepositoryTestSuite:
    """
    Complete test suite coordinator for all repository tests.

    Provides unified test execution and reporting.
    """

    def __init__(self):
        """Initialize test suite."""
        self.test_classes = [
            TestSignalRepository,
            TestMarketDataRepository,
            TestStrategyRepository,
        ]

    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all repository tests and return results.

        Returns:
            Test results summary
        """
        results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_details": {},
        }

        for test_class in self.test_classes:
            class_name = test_class.__name__
            class_results = await self._run_test_class(test_class)

            results["test_details"][class_name] = class_results
            results["total_tests"] += class_results["total"]
            results["passed_tests"] += class_results["passed"]
            results["failed_tests"] += class_results["failed"]
            results["skipped_tests"] += class_results["skipped"]

        return results

    async def _run_test_class(self, test_class) -> Dict[str, Any]:
        """Run tests for a specific test class."""
        results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "methods": []}

        try:
            test_instance = test_class()

            # Get test methods
            test_methods = [
                method
                for method in dir(test_instance)
                if method.startswith("test_")
                and callable(getattr(test_instance, method))
            ]

            for method_name in test_methods:
                results["total"] += 1
                method_result = await self._run_test_method(test_instance, method_name)
                results["methods"].append(method_result)

                if method_result["status"] == "passed":
                    results["passed"] += 1
                elif method_result["status"] == "failed":
                    results["failed"] += 1
                elif method_result["status"] == "skipped":
                    results["skipped"] += 1

        except Exception as e:
            logger.error(f"Error running test class {test_class.__name__}: {e}")

        return results

    async def _run_test_method(self, test_instance, method_name: str) -> Dict[str, Any]:
        """Run a single test method."""
        result = {
            "method": method_name,
            "status": "unknown",
            "error": None,
            "duration_ms": 0,
        }

        try:
            start_time = datetime.utcnow()

            # Setup
            if hasattr(test_instance, "setup_method"):
                await test_instance.setup_method()

            # Run test
            test_method = getattr(test_instance, method_name)
            await test_method()

            # Teardown
            if hasattr(test_instance, "teardown_method"):
                await test_instance.teardown_method()

            end_time = datetime.utcnow()
            result["duration_ms"] = (end_time - start_time).total_seconds() * 1000
            result["status"] = "passed"

        except pytest.skip.Exception as e:
            result["status"] = "skipped"
            result["error"] = str(e)
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Test {method_name} failed: {e}")

        return result


# Test configuration for different environments
TEST_CONFIGURATIONS = {
    "local": TestConfiguration(
        test_db_name="test_4ex_ninja_local",
        test_db_uri="mongodb://localhost:27017",
        cleanup_after_tests=True,
    ),
    "ci": TestConfiguration(
        test_db_name="test_4ex_ninja_ci",
        test_db_uri=os.getenv("TEST_MONGODB_URI", "mongodb://localhost:27017"),
        cleanup_after_tests=True,
    ),
    "in_memory": TestConfiguration(
        test_db_name="test_4ex_ninja_memory",
        use_in_memory_db=True,
        cleanup_after_tests=True,
    ),
}


def get_test_configuration(env: str = "local") -> TestConfiguration:
    """Get test configuration for specified environment."""
    return TEST_CONFIGURATIONS.get(env, TEST_CONFIGURATIONS["local"])


# Pytest fixtures for easy test usage
@pytest.fixture
async def test_db_manager():
    """Pytest fixture for test database manager."""
    manager = TestDatabaseManager()
    await manager.setup_test_database()
    yield manager
    await manager.cleanup_test_database()


@pytest.fixture
def test_fixtures():
    """Pytest fixture for test data fixtures."""
    return RepositoryTestFixtures()


@pytest.fixture
async def signal_repository(test_db_manager):
    """Pytest fixture for signal repository."""
    return MongoSignalRepository(
        database=test_db_manager.database, collection_name="test_signals"
    )


@pytest.fixture
async def market_data_repository(test_db_manager):
    """Pytest fixture for market data repository."""
    return MongoMarketDataRepository(
        database=test_db_manager.database, collection_name="test_market_data"
    )


@pytest.fixture
async def strategy_repository(test_db_manager):
    """Pytest fixture for strategy repository."""
    return MongoStrategyRepository(
        database=test_db_manager.database, collection_name="test_strategies"
    )
