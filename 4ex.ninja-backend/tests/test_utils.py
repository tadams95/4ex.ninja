"""
Test utilities for 4ex.ninja backend testing.

This module provides helper functions, decorators, and utilities
to make testing easier and more consistent across the test suite.
"""

import asyncio
import functools
import json
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from unittest.mock import AsyncMock, MagicMock

from src.core.entities.signal import Signal, SignalType, CrossoverType, SignalStatus
from src.core.entities.market_data import MarketData, Granularity, Candle
from src.core.entities.strategy import (
    Strategy,
    StrategyType,
    StrategyStatus,
    StrategyParameters,
)

T = TypeVar("T")


class TestDataBuilder:
    """Builder class for creating test data with fluent interface."""

    @staticmethod
    def signal() -> "SignalBuilder":
        """Create a signal builder."""
        return SignalBuilder()

    @staticmethod
    def market_data() -> "MarketDataBuilder":
        """Create a market data builder."""
        return MarketDataBuilder()

    @staticmethod
    def strategy() -> "StrategyBuilder":
        """Create a strategy builder."""
        return StrategyBuilder()


class SignalBuilder:
    """Builder for creating Signal objects with customizable properties."""

    def __init__(self):
        self._signal_id = "test_signal"
        self._pair = "EUR_USD"
        self._timeframe = "H4"
        self._signal_type = SignalType.BUY
        self._crossover_type = CrossoverType.BULLISH
        self._entry_price = Decimal("1.1000")
        self._current_price = Decimal("1.1010")
        self._fast_ma = 20
        self._slow_ma = 50
        self._timestamp = datetime.utcnow()
        self._status = SignalStatus.ACTIVE

    def with_id(self, signal_id: str) -> "SignalBuilder":
        self._signal_id = signal_id
        return self

    def with_pair(self, pair: str) -> "SignalBuilder":
        self._pair = pair
        return self

    def with_timeframe(self, timeframe: str) -> "SignalBuilder":
        self._timeframe = timeframe
        return self

    def with_signal_type(self, signal_type: SignalType) -> "SignalBuilder":
        self._signal_type = signal_type
        return self

    def with_crossover_type(self, crossover_type: CrossoverType) -> "SignalBuilder":
        self._crossover_type = crossover_type
        return self

    def with_entry_price(self, price: Union[str, Decimal, float]) -> "SignalBuilder":
        self._entry_price = Decimal(str(price))
        return self

    def with_current_price(self, price: Union[str, Decimal, float]) -> "SignalBuilder":
        self._current_price = Decimal(str(price))
        return self

    def with_ma_periods(self, fast: int, slow: int) -> "SignalBuilder":
        self._fast_ma = fast
        self._slow_ma = slow
        return self

    def with_timestamp(self, timestamp: datetime) -> "SignalBuilder":
        self._timestamp = timestamp
        return self

    def with_status(self, status: SignalStatus) -> "SignalBuilder":
        self._status = status
        return self

    def build(self) -> Signal:
        """Build the Signal object."""
        return Signal(
            signal_id=self._signal_id,
            pair=self._pair,
            timeframe=self._timeframe,
            signal_type=self._signal_type,
            crossover_type=self._crossover_type,
            entry_price=self._entry_price,
            current_price=self._current_price,
            fast_ma=self._fast_ma,
            slow_ma=self._slow_ma,
            timestamp=self._timestamp,
            status=self._status,
        )


class MarketDataBuilder:
    """Builder for creating MarketData objects with customizable properties."""

    def __init__(self):
        self._instrument = "EUR_USD"
        self._granularity = Granularity.H4
        self._candles = []

    def with_instrument(self, instrument: str) -> "MarketDataBuilder":
        self._instrument = instrument
        return self

    def with_granularity(self, granularity: Granularity) -> "MarketDataBuilder":
        self._granularity = granularity
        return self

    def with_candles(self, candles: List[Candle]) -> "MarketDataBuilder":
        self._candles = candles
        return self

    def with_sample_candles(self, count: int = 5) -> "MarketDataBuilder":
        """Add sample candles for testing."""
        base_time = datetime.utcnow()
        candles = []

        for i in range(count):
            candle = Candle(
                time=base_time - timedelta(hours=i * 4),
                open=Decimal(f"1.{1000 + i:04d}"),
                high=Decimal(f"1.{1020 + i:04d}"),
                low=Decimal(f"1.{980 + i:04d}"),
                close=Decimal(f"1.{1010 + i:04d}"),
                volume=1000000 + (i * 100000),
            )
            candles.append(candle)

        self._candles = candles
        return self

    def build(self) -> MarketData:
        """Build the MarketData object."""
        return MarketData(
            instrument=self._instrument,
            granularity=self._granularity,
            candles=self._candles,
        )


class StrategyBuilder:
    """Builder for creating Strategy objects with customizable properties."""

    def __init__(self):
        self._strategy_id = "test_strategy"
        self._name = "Test Strategy"
        self._strategy_type = StrategyType.MOVING_AVERAGE_CROSSOVER
        self._pair = "EUR_USD"
        self._timeframe = "H4"
        self._parameters = StrategyParameters(fast_ma_period=20, slow_ma_period=50)
        self._status = StrategyStatus.ACTIVE

    def with_id(self, strategy_id: str) -> "StrategyBuilder":
        self._strategy_id = strategy_id
        return self

    def with_name(self, name: str) -> "StrategyBuilder":
        self._name = name
        return self

    def with_strategy_type(self, strategy_type: StrategyType) -> "StrategyBuilder":
        self._strategy_type = strategy_type
        return self

    def with_pair(self, pair: str) -> "StrategyBuilder":
        self._pair = pair
        return self

    def with_timeframe(self, timeframe: str) -> "StrategyBuilder":
        self._timeframe = timeframe
        return self

    def with_parameters(self, parameters: StrategyParameters) -> "StrategyBuilder":
        self._parameters = parameters
        return self

    def with_ma_parameters(self, fast: int, slow: int) -> "StrategyBuilder":
        """Convenience method for setting MA parameters."""
        self._parameters = StrategyParameters(
            fast_ma_period=fast,
            slow_ma_period=slow,
            atr_period=14,
            sl_atr_multiplier=2.0,
            tp_atr_multiplier=3.0,
        )
        return self

    def with_status(self, status: StrategyStatus) -> "StrategyBuilder":
        self._status = status
        return self

    def build(self) -> Strategy:
        """Build the Strategy object."""
        return Strategy(
            strategy_id=self._strategy_id,
            name=self._name,
            strategy_type=self._strategy_type,
            pair=self._pair,
            timeframe=self._timeframe,
            parameters=self._parameters,
            status=self._status,
        )


# Helper functions
def create_mock_async_repository() -> AsyncMock:
    """Create a mock async repository with common methods."""
    mock_repo = AsyncMock()

    # Configure standard repository methods
    mock_repo.create.return_value = AsyncMock()
    mock_repo.get_by_id.return_value = AsyncMock()
    mock_repo.get_all.return_value = AsyncMock()
    mock_repo.update.return_value = AsyncMock()
    mock_repo.delete.return_value = AsyncMock()
    mock_repo.find_by_criteria.return_value = AsyncMock()

    return mock_repo


def assert_equal_ignoring_fields(
    obj1: T, obj2: T, ignore_fields: Optional[List[str]] = None
) -> None:
    """
    Assert two objects are equal, optionally ignoring certain fields.

    Args:
        obj1: First object to compare
        obj2: Second object to compare
        ignore_fields: List of field names to ignore in comparison
    """
    ignore_fields = ignore_fields or []

    # Convert objects to dicts if they have a to_dict method
    if hasattr(obj1, "to_dict") and hasattr(obj2, "to_dict"):
        dict1 = obj1.to_dict()
        dict2 = obj2.to_dict()
    else:
        dict1 = obj1.__dict__.copy()
        dict2 = obj2.__dict__.copy()

    # Remove ignored fields
    for field in ignore_fields:
        dict1.pop(field, None)
        dict2.pop(field, None)

    assert dict1 == dict2


def create_temp_file(content: str = "", suffix: str = ".json") -> Path:
    """
    Create a temporary file with optional content.

    Args:
        content: Content to write to the file
        suffix: File suffix/extension

    Returns:
        Path to the temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    temp_file.write(content)
    temp_file.close()
    return Path(temp_file.name)


def load_test_data(filename: str) -> Dict[str, Any]:
    """
    Load test data from a JSON file.

    Args:
        filename: Name of the test data file

    Returns:
        Loaded test data as a dictionary
    """
    test_data_dir = Path(__file__).parent / "data"
    file_path = test_data_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")

    with open(file_path, "r") as f:
        return json.load(f)


# Decorators
def async_test(func: Callable) -> Callable:
    """
    Decorator to mark a function as an async test.
    This is mainly for documentation and can be extended for specific behavior.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    wrapper._is_async_test = True
    return wrapper


def timeout_test(seconds: int = 30):
    """
    Decorator to add a timeout to a test function.

    Args:
        seconds: Timeout in seconds
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't easily add timeout without additional libraries
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Database testing utilities
def create_test_database_url(test_name: str) -> str:
    """
    Create a unique test database URL for a specific test.

    Args:
        test_name: Name of the test (used in database name)

    Returns:
        MongoDB connection URL for testing
    """
    safe_test_name = test_name.replace(" ", "_").replace("-", "_").lower()
    return f"mongodb://localhost:27017/4ex_ninja_test_{safe_test_name}"


# Performance testing utilities
class PerformanceTimer:
    """Context manager for measuring execution time."""

    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None

    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.utcnow()
        self.elapsed_time = (self.end_time - self.start_time).total_seconds()
        print(f"{self.description} completed in {self.elapsed_time:.4f} seconds")


def assert_performance_within_threshold(
    func: Callable, threshold_seconds: float, *args, **kwargs
):
    """
    Assert that a function executes within a specified time threshold.

    Args:
        func: Function to test
        threshold_seconds: Maximum allowed execution time
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    """
    with PerformanceTimer() as timer:
        result = func(*args, **kwargs)

    assert timer.elapsed_time <= threshold_seconds, (
        f"Function {func.__name__} took {timer.elapsed_time:.4f}s, "
        f"which exceeds the threshold of {threshold_seconds}s"
    )

    return result
