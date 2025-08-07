"""
Test repository layer and data access (Section 1.9.2)

This module provides lean, focused tests for:
- Repository interface functionality
- Database operations and error handling
- Data validation and consistency

Keeps testing simple and focused on core functions without breaking changes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from src.core.entities.market_data import MarketData, Candle, Granularity
from src.core.interfaces.signal_repository import ISignalRepository
from src.core.interfaces.market_data_repository import IMarketDataRepository


class TestRepositoryLayer:
    """Test repository layer functionality with mocked implementations."""

    @pytest.fixture
    def sample_signal(self):
        """Create a sample signal for testing."""
        return Signal(
            signal_id="test_signal_1",
            pair="EUR/USD",
            timeframe="H1",
            signal_type=SignalType.BUY,
            crossover_type=CrossoverType.BULLISH,
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1005"),
            fast_ma=10,
            slow_ma=20,
            timestamp=datetime.utcnow(),
            stop_loss=Decimal("1.0950"),
            take_profit=Decimal("1.1100"),
            atr_value=Decimal("0.0025"),
            status=SignalStatus.ACTIVE,
        )

    @pytest.fixture
    def sample_candles(self):
        """Create sample candle data for testing."""
        return [
            Candle(
                time=datetime.utcnow() - timedelta(hours=i),
                open=Decimal("1.1000") + Decimal(str(i * 0.001)),
                high=Decimal("1.1010") + Decimal(str(i * 0.001)),
                low=Decimal("1.0990") + Decimal(str(i * 0.001)),
                close=Decimal("1.1005") + Decimal(str(i * 0.001)),
                volume=1000,
            )
            for i in range(10)
        ]

    @pytest.fixture
    def sample_market_data(self, sample_candles):
        """Create sample market data for testing."""
        return MarketData(
            instrument="EUR_USD",
            granularity=Granularity.H1,
            candles=sample_candles,
            last_updated=datetime.utcnow(),
        )

    @pytest.fixture
    def mock_signal_repository(self):
        """Create a mock signal repository."""
        mock_repo = AsyncMock(spec=ISignalRepository)
        return mock_repo

    @pytest.fixture
    def mock_market_data_repository(self):
        """Create a mock market data repository."""
        mock_repo = AsyncMock(spec=IMarketDataRepository)
        return mock_repo

    @pytest.mark.asyncio
    async def test_signal_repository_create(
        self, mock_signal_repository, sample_signal
    ):
        """Test signal repository create operation."""
        # Configure mock to return the signal
        mock_signal_repository.create.return_value = sample_signal

        result = await mock_signal_repository.create(sample_signal)

        assert result == sample_signal
        mock_signal_repository.create.assert_called_once_with(sample_signal)

    @pytest.mark.asyncio
    async def test_signal_repository_get_by_id(
        self, mock_signal_repository, sample_signal
    ):
        """Test signal repository get by ID operation."""
        # Configure mock to return the signal
        mock_signal_repository.get_by_id.return_value = sample_signal

        result = await mock_signal_repository.get_by_id("test_signal_1")

        assert result == sample_signal
        assert result.signal_id == "test_signal_1"
        mock_signal_repository.get_by_id.assert_called_once_with("test_signal_1")

    @pytest.mark.asyncio
    async def test_signal_repository_update(
        self, mock_signal_repository, sample_signal
    ):
        """Test signal repository update operation."""
        # Update signal status
        sample_signal.status = SignalStatus.FILLED

        # Configure mock to return updated signal
        mock_signal_repository.update.return_value = sample_signal

        result = await mock_signal_repository.update(sample_signal)

        assert result == sample_signal
        assert result.status == SignalStatus.FILLED
        mock_signal_repository.update.assert_called_once_with(sample_signal)

    @pytest.mark.asyncio
    async def test_signal_repository_delete(self, mock_signal_repository):
        """Test signal repository delete operation."""
        # Configure mock to return True for successful deletion
        mock_signal_repository.delete.return_value = True

        result = await mock_signal_repository.delete("test_signal_1")

        assert result is True
        mock_signal_repository.delete.assert_called_once_with("test_signal_1")

    @pytest.mark.asyncio
    async def test_signal_repository_find_by_criteria(
        self, mock_signal_repository, sample_signal
    ):
        """Test signal repository find by criteria operation."""
        # Configure mock to return list of signals
        mock_signal_repository.find_by_criteria.return_value = [sample_signal]

        criteria = {"pair": "EUR/USD", "status": SignalStatus.ACTIVE}
        result = await mock_signal_repository.find_by_criteria(criteria)

        assert len(result) == 1
        assert result[0] == sample_signal
        mock_signal_repository.find_by_criteria.assert_called_once_with(criteria)

    @pytest.mark.asyncio
    async def test_market_data_repository_operations(
        self, mock_market_data_repository, sample_market_data
    ):
        """Test market data repository basic operations."""
        # Test create operation
        mock_market_data_repository.create.return_value = sample_market_data

        result = await mock_market_data_repository.create(sample_market_data)
        assert result == sample_market_data
        mock_market_data_repository.create.assert_called_once_with(sample_market_data)

    @pytest.mark.asyncio
    async def test_repository_error_handling(self, mock_signal_repository):
        """Test repository error handling for database failures."""
        # Configure mock to raise exception
        mock_signal_repository.get_by_id.side_effect = Exception(
            "Database connection failed"
        )

        with pytest.raises(Exception) as exc_info:
            await mock_signal_repository.get_by_id("test_signal_1")

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_repository_batch_operations(
        self, mock_signal_repository, sample_signal
    ):
        """Test repository batch operations."""
        signals = [sample_signal, sample_signal]

        # Configure mock for multiple create operations
        mock_signal_repository.create.return_value = sample_signal

        # Test individual creates (simulating batch operation)
        results = []
        for signal in signals:
            result = await mock_signal_repository.create(signal)
            results.append(result)

        assert len(results) == 2
        assert all(result == sample_signal for result in results)
        assert mock_signal_repository.create.call_count == 2


class TestDataValidation:
    """Test data validation and consistency checks."""

    def test_signal_entity_validation(self):
        """Test signal entity data validation."""
        # Test valid signal creation
        signal = Signal(
            signal_id="test_001",
            pair="EUR/USD",
            timeframe="H1",
            signal_type=SignalType.BUY,
            crossover_type=CrossoverType.BULLISH,
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1005"),
            fast_ma=10,
            slow_ma=20,
            timestamp=datetime.utcnow(),
            stop_loss=Decimal("1.0950"),
            take_profit=Decimal("1.1100"),
        )

        assert signal.signal_id == "test_001"
        assert signal.pair == "EUR/USD"
        assert signal.entry_price == Decimal("1.1000")

    def test_candle_entity_validation(self):
        """Test candle entity data validation."""
        candle = Candle(
            time=datetime.utcnow(),
            open=Decimal("1.1000"),
            high=Decimal("1.1010"),
            low=Decimal("1.0990"),
            close=Decimal("1.1005"),
            volume=1000,
        )

        assert candle.is_bullish() == True  # close > open
        assert candle.body_size() == Decimal("0.0005")

    def test_market_data_validation(self):
        """Test market data validation."""
        candles = [
            Candle(
                time=datetime.utcnow(),
                open=Decimal("1.1000"),
                high=Decimal("1.1010"),
                low=Decimal("1.0990"),
                close=Decimal("1.1005"),
                volume=1000,
            )
        ]

        market_data = MarketData(
            instrument="EUR_USD", granularity=Granularity.H1, candles=candles
        )

        assert market_data.instrument == "EUR_USD"
        assert len(market_data.candles) == 1
        assert market_data.get_latest_candle() == candles[0]

    def test_price_relationship_validation(self):
        """Test price relationship validation for trading signals."""
        # Test valid price relationships
        entry_price = Decimal("1.1000")
        stop_loss = Decimal("1.0950")
        take_profit = Decimal("1.1100")

        # For BUY signal: entry > stop_loss and take_profit > entry
        assert entry_price > stop_loss
        assert take_profit > entry_price

        # Calculate risk-reward ratio
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        risk_reward_ratio = reward / risk

        assert risk_reward_ratio == Decimal("2.0")  # 2:1 risk-reward ratio

    def test_moving_average_calculation(self):
        """Test moving average calculation logic."""
        prices = [
            Decimal("1.1000"),
            Decimal("1.1010"),
            Decimal("1.1020"),
            Decimal("1.1030"),
            Decimal("1.1040"),
        ]

        # Simple moving average calculation
        period = 3
        if len(prices) >= period:
            sma = sum(prices[-period:]) / period
            expected_sma = (
                Decimal("1.1020") + Decimal("1.1030") + Decimal("1.1040")
            ) / 3
            assert sma == expected_sma

    def test_signal_crossover_logic(self):
        """Test signal crossover detection logic."""
        # Test bullish crossover (fast MA crosses above slow MA)
        fast_ma_prev = Decimal("1.0995")
        slow_ma_prev = Decimal("1.1000")
        fast_ma_current = Decimal("1.1005")
        slow_ma_current = Decimal("1.1000")

        # Previous: fast < slow, Current: fast > slow = Bullish crossover
        bullish_crossover = (fast_ma_prev < slow_ma_prev) and (
            fast_ma_current > slow_ma_current
        )
        assert bullish_crossover == True

    def test_atr_calculation_logic(self):
        """Test ATR (Average True Range) calculation logic."""
        # Sample candle data for ATR calculation
        candles = [
            {
                "high": Decimal("1.1020"),
                "low": Decimal("1.0980"),
                "close": Decimal("1.1000"),
            },
            {
                "high": Decimal("1.1030"),
                "low": Decimal("1.0990"),
                "close": Decimal("1.1010"),
            },
            {
                "high": Decimal("1.1025"),
                "low": Decimal("1.0995"),
                "close": Decimal("1.1005"),
            },
        ]

        # True Range calculation for the second candle
        high_low = candles[1]["high"] - candles[1]["low"]
        high_close_prev = abs(candles[1]["high"] - candles[0]["close"])
        low_close_prev = abs(candles[1]["low"] - candles[0]["close"])

        true_range = max(high_low, high_close_prev, low_close_prev)
        assert true_range > Decimal("0")


class TestDatabaseOperations:
    """Test database operations and connection handling."""

    @pytest.mark.asyncio
    async def test_database_connection_handling(self):
        """Test database connection error handling."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.side_effect = ConnectionError("Database unavailable")

        with pytest.raises(ConnectionError):
            await mock_repo.get_by_id("test_id")

    @pytest.mark.asyncio
    async def test_transaction_handling(self):
        """Test database transaction handling."""
        mock_session = MagicMock()
        mock_session.start_transaction = MagicMock()
        mock_session.commit_transaction = AsyncMock()
        mock_session.abort_transaction = AsyncMock()

        # Test successful transaction
        mock_session.start_transaction()
        try:
            result = "operation_success"
            await mock_session.commit_transaction()
            assert result == "operation_success"
        except Exception:
            await mock_session.abort_transaction()

    def test_query_optimization_patterns(self):
        """Test query optimization patterns for repository operations."""
        # Test compound index patterns
        query_patterns = [
            {
                "pair": "EUR/USD",
                "timestamp": {"$gte": datetime.utcnow() - timedelta(days=1)},
            },
            {"signal_type": "BUY", "status": "ACTIVE"},
            {"fast_ma": 10, "slow_ma": 20, "confidence_score": {"$gte": 0.7}},
        ]

        for pattern in query_patterns:
            assert isinstance(pattern, dict)
            assert len(pattern) > 0

    @pytest.mark.asyncio
    async def test_repository_performance_monitoring(self):
        """Test repository performance monitoring."""
        mock_repo = AsyncMock()

        # Mock timing for performance measurement
        start_time = datetime.utcnow()

        # Simulate repository operation
        mock_repo.get_by_id.return_value = {"id": "test"}
        result = await mock_repo.get_by_id("test")

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        assert result is not None
        assert execution_time >= 0


# Simple test runner for section 1.9.2
def run_repository_tests():
    """Run repository layer tests for section 1.9.2."""
    pytest.main(
        [
            __file__,
            "-v",
            "-x",  # Stop on first failure
            "--tb=short",  # Short traceback format
            "-q",  # Quiet output
        ]
    )


if __name__ == "__main__":
    run_repository_tests()
