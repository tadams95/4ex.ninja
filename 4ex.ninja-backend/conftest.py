"""
Pytest configuration and fixtures for 4ex.ninja backend testing.

This file provides shared fixtures and configuration for all tests,
including database setup, async support, and repository mocking.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Generator, Optional
from datetime import datetime, timedelta

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/4ex_ninja_test"
os.environ["DATABASE_NAME"] = "4ex_ninja_test"

# Import core components after setting environment
from src.core.entities.signal import Signal, SignalType, CrossoverType, SignalStatus
from src.core.entities.market_data import MarketData, Granularity, Candle
from src.core.entities.strategy import (
    Strategy,
    StrategyType,
    StrategyStatus,
    StrategyParameters,
)
from decimal import Decimal


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database connection for unit tests."""
    mock_db = MagicMock()
    mock_collection = MagicMock()

    # Configure mock collection methods
    mock_collection.find.return_value = AsyncMock()
    mock_collection.find_one.return_value = AsyncMock()
    mock_collection.insert_one.return_value = AsyncMock()
    mock_collection.insert_many.return_value = AsyncMock()
    mock_collection.update_one.return_value = AsyncMock()
    mock_collection.update_many.return_value = AsyncMock()
    mock_collection.delete_one.return_value = AsyncMock()
    mock_collection.delete_many.return_value = AsyncMock()
    mock_collection.count_documents.return_value = AsyncMock()
    mock_collection.aggregate.return_value = AsyncMock()

    # Configure database to return our mock collection
    mock_db.__getitem__.return_value = mock_collection
    mock_db.get_collection.return_value = mock_collection

    return mock_db


@pytest.fixture
def mock_signal_repository():
    """Mock signal repository for testing services."""
    mock_repo = AsyncMock()

    # Configure common repository methods
    mock_repo.create.return_value = AsyncMock()
    mock_repo.get_by_id.return_value = AsyncMock()
    mock_repo.get_all.return_value = AsyncMock()
    mock_repo.update.return_value = AsyncMock()
    mock_repo.delete.return_value = AsyncMock()
    mock_repo.find_by_criteria.return_value = AsyncMock()
    mock_repo.get_by_pair_and_timeframe.return_value = AsyncMock()
    mock_repo.get_recent_signals.return_value = AsyncMock()
    mock_repo.update_signal_status.return_value = AsyncMock()

    return mock_repo


@pytest.fixture
def mock_market_data_repository():
    """Mock market data repository for testing services."""
    mock_repo = AsyncMock()

    # Configure market data specific methods
    mock_repo.create.return_value = AsyncMock()
    mock_repo.get_by_id.return_value = AsyncMock()
    mock_repo.get_all.return_value = AsyncMock()
    mock_repo.update.return_value = AsyncMock()
    mock_repo.delete.return_value = AsyncMock()
    mock_repo.get_candles_by_timeframe.return_value = AsyncMock()
    mock_repo.get_latest_candles.return_value = AsyncMock()
    mock_repo.add_or_update_candle.return_value = AsyncMock()
    mock_repo.get_data_coverage.return_value = AsyncMock()

    return mock_repo


@pytest.fixture
def mock_strategy_repository():
    """Mock strategy repository for testing services."""
    mock_repo = AsyncMock()

    # Configure strategy specific methods
    mock_repo.create.return_value = AsyncMock()
    mock_repo.get_by_id.return_value = AsyncMock()
    mock_repo.get_all.return_value = AsyncMock()
    mock_repo.update.return_value = AsyncMock()
    mock_repo.delete.return_value = AsyncMock()
    mock_repo.get_active_strategies.return_value = AsyncMock()
    mock_repo.update_strategy_status.return_value = AsyncMock()
    mock_repo.get_strategy_performance.return_value = AsyncMock()
    mock_repo.clone_strategy.return_value = AsyncMock()

    return mock_repo


# Test data factories
@pytest.fixture
def sample_signal() -> Signal:
    """Create a sample signal for testing."""
    return Signal(
        signal_id="test_signal_001",
        pair="EUR_USD",
        timeframe="H4",
        signal_type=SignalType.BUY,
        crossover_type=CrossoverType.BULLISH,
        entry_price=Decimal("1.0950"),
        current_price=Decimal("1.0960"),
        fast_ma=20,
        slow_ma=50,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def sample_market_data() -> MarketData:
    """Create sample market data for testing."""
    # Create sample candles
    candles = [
        Candle(
            time=datetime.utcnow() - timedelta(hours=4),
            open=Decimal("1.0940"),
            high=Decimal("1.0980"),
            low=Decimal("1.0920"),
            close=Decimal("1.0950"),
            volume=1500000,
        ),
        Candle(
            time=datetime.utcnow(),
            open=Decimal("1.0950"),
            high=Decimal("1.0970"),
            low=Decimal("1.0930"),
            close=Decimal("1.0960"),
            volume=1600000,
        ),
    ]

    return MarketData(instrument="EUR_USD", granularity=Granularity.H4, candles=candles)


@pytest.fixture
def sample_strategy() -> Strategy:
    """Create a sample strategy for testing."""
    # Create strategy parameters
    parameters = StrategyParameters(
        fast_ma_period=20,
        slow_ma_period=50,
        atr_period=14,
        sl_atr_multiplier=2.0,
        tp_atr_multiplier=3.0,
    )

    return Strategy(
        strategy_id="test_strategy_001",
        name="Test MA Crossover",
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        pair="EUR_USD",
        timeframe="H4",
        parameters=parameters,
        description="Test moving average crossover strategy",
        status=StrategyStatus.ACTIVE,
    )


@pytest.fixture
def sample_signals_list(sample_signal) -> list[Signal]:
    """Create a list of sample signals for testing."""
    signals = []
    pairs = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
    signal_types = [SignalType.BUY, SignalType.SELL]

    for i, pair in enumerate(pairs):
        signal = Signal(
            signal_id=f"signal_{i}",
            pair=pair,
            timeframe="H4",
            signal_type=signal_types[i % 2],
            crossover_type=(
                CrossoverType.BULLISH
                if signal_types[i % 2] == SignalType.BUY
                else CrossoverType.BEARISH
            ),
            entry_price=Decimal(str(1.1000 + (i * 0.01))),
            current_price=Decimal(str(1.1000 + (i * 0.01))),
            fast_ma=20,
            slow_ma=50,
            timestamp=datetime.utcnow() - timedelta(hours=i),
            stop_loss=Decimal(str(1.0950 + (i * 0.01))),
            take_profit=Decimal(str(1.1050 + (i * 0.01))),
        )
        signals.append(signal)

    return signals


@pytest.fixture
def sample_market_data_list() -> list[MarketData]:
    """Create a list of sample market data for testing."""
    data_list = []
    base_time = datetime.utcnow()

    for i in range(10):
        # Create a single candle for each market data instance
        candle = Candle(
            time=base_time - timedelta(hours=i * 4),
            open=Decimal(str(1.0900 + (i * 0.001))),
            high=Decimal(str(1.0920 + (i * 0.001))),
            low=Decimal(str(1.0880 + (i * 0.001))),
            close=Decimal(str(1.0910 + (i * 0.001))),
            volume=1000000 + (i * 50000),
        )

        data = MarketData(
            instrument="EUR_USD", granularity=Granularity.H4, candles=[candle]
        )
        data_list.append(data)

    return data_list


# Configuration fixtures
@pytest.fixture
def test_config():
    """Test configuration dictionary."""
    return {
        "database": {
            "host": "localhost",
            "port": 27017,
            "name": "4ex_ninja_test",
            "uri": "mongodb://localhost:27017/4ex_ninja_test",
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "testing": {"timeout": 30, "max_retries": 3, "async_timeout": 10},
    }


# Async context managers for testing
@pytest_asyncio.fixture
async def async_test_context():
    """Async context for testing async operations."""
    # Setup
    context = {"start_time": datetime.utcnow(), "test_data": {}, "cleanup_tasks": []}

    try:
        yield context
    finally:
        # Cleanup
        for cleanup_task in context["cleanup_tasks"]:
            if asyncio.iscoroutinefunction(cleanup_task):
                await cleanup_task()
            else:
                cleanup_task()


# Mock external services
@pytest.fixture
def mock_oanda_api():
    """Mock OANDA API for testing market data fetching."""
    mock_api = MagicMock()

    # Configure mock responses
    mock_api.get_candles.return_value = {
        "candles": [
            {
                "time": "2024-01-01T12:00:00.000000Z",
                "mid": {"o": "1.0950", "h": "1.0980", "l": "1.0920", "c": "1.0960"},
                "volume": 1500000,
            }
        ]
    }

    mock_api.get_instruments.return_value = {
        "instruments": [
            {"name": "EUR_USD", "type": "CURRENCY"},
            {"name": "GBP_USD", "type": "CURRENCY"},
            {"name": "USD_JPY", "type": "CURRENCY"},
        ]
    }

    return mock_api


# Helper functions for tests
def assert_signal_equal(
    signal1: Signal, signal2: Signal, ignore_fields: Optional[list] = None
):
    """Helper function to compare signals, optionally ignoring certain fields."""
    ignore_fields = ignore_fields or ["id", "created_at", "updated_at"]

    signal1_dict = signal1.to_dict()
    signal2_dict = signal2.to_dict()

    for field in ignore_fields:
        signal1_dict.pop(field, None)
        signal2_dict.pop(field, None)

    assert signal1_dict == signal2_dict


def assert_market_data_equal(
    data1: MarketData, data2: MarketData, ignore_fields: Optional[list] = None
):
    """Helper function to compare market data, optionally ignoring certain fields."""
    ignore_fields = ignore_fields or ["id", "created_at", "updated_at"]

    data1_dict = data1.to_dict()
    data2_dict = data2.to_dict()

    for field in ignore_fields:
        data1_dict.pop(field, None)
        data2_dict.pop(field, None)

    assert data1_dict == data2_dict


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "async_test: mark test as an async test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add async marker for async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.async_test)


# Timeout configuration for async tests is handled via pytest.ini
# The timeout setting is configured in pytest.ini under asyncio_default_fixture_loop_scope
