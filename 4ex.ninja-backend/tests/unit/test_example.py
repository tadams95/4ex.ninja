"""
Example unit tests demonstrating the testing infrastructure.

These tests show how to use the fixtures, builders, and utilities
provided by our testing framework.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.core.entities.signal import Signal, SignalType, CrossoverType
from src.core.entities.market_data import MarketData, Granularity
from src.core.entities.strategy import Strategy, StrategyType

from tests.test_utils import TestDataBuilder


class TestSignalEntity:
    """Tests for the Signal entity."""

    def test_signal_creation_with_fixture(self, sample_signal):
        """Test that signals can be created using fixtures."""
        assert isinstance(sample_signal, Signal)
        assert sample_signal.signal_id == "test_signal_001"
        assert sample_signal.pair == "EUR_USD"
        assert sample_signal.signal_type == SignalType.BUY

    def test_signal_creation_with_builder(self):
        """Test that signals can be created using the builder pattern."""
        signal = (
            TestDataBuilder.signal()
            .with_id("custom_signal")
            .with_pair("GBP_USD")
            .with_signal_type(SignalType.SELL)
            .with_crossover_type(CrossoverType.BEARISH)
            .with_entry_price("1.2500")
            .with_current_price("1.2480")
            .with_ma_periods(10, 30)
            .build()
        )

        assert signal.signal_id == "custom_signal"
        assert signal.pair == "GBP_USD"
        assert signal.signal_type == SignalType.SELL
        assert signal.crossover_type == CrossoverType.BEARISH
        assert signal.entry_price == Decimal("1.2500")
        assert signal.current_price == Decimal("1.2480")
        assert signal.fast_ma == 10
        assert signal.slow_ma == 30

    def test_signal_profitability_buy(self):
        """Test profit calculation for BUY signals."""
        signal = (
            TestDataBuilder.signal()
            .with_signal_type(SignalType.BUY)
            .with_entry_price("1.1000")
            .with_current_price("1.1050")  # Higher = profitable
            .build()
        )

        assert signal.is_profitable() is True
        assert signal.get_pnl() == Decimal("0.0050")

    def test_signal_profitability_sell(self):
        """Test profit calculation for SELL signals."""
        signal = (
            TestDataBuilder.signal()
            .with_signal_type(SignalType.SELL)
            .with_entry_price("1.1000")
            .with_current_price("1.0950")  # Lower = profitable for SELL
            .build()
        )

        assert signal.is_profitable() is True
        assert signal.get_pnl() == Decimal("0.0050")


class TestMarketDataEntity:
    """Tests for the MarketData entity."""

    def test_market_data_creation_with_fixture(self, sample_market_data):
        """Test that market data can be created using fixtures."""
        assert isinstance(sample_market_data, MarketData)
        assert sample_market_data.instrument == "EUR_USD"
        assert sample_market_data.granularity == Granularity.H4
        assert len(sample_market_data.candles) == 2

    def test_market_data_creation_with_builder(self):
        """Test that market data can be created using the builder pattern."""
        market_data = (
            TestDataBuilder.market_data()
            .with_instrument("GBP_USD")
            .with_granularity(Granularity.M15)
            .with_sample_candles(10)
            .build()
        )

        assert market_data.instrument == "GBP_USD"
        assert market_data.granularity == Granularity.M15
        assert len(market_data.candles) == 10

    def test_market_data_latest_candle(self, sample_market_data):
        """Test getting the latest candle from market data."""
        latest_candle = sample_market_data.get_latest_candle()
        assert latest_candle is not None
        assert latest_candle.volume == 1600000  # Latest candle from our fixture

    def test_market_data_recent_candles(self, sample_market_data):
        """Test getting recent candles from market data."""
        recent_candles = sample_market_data.get_recent_candles(1)
        assert len(recent_candles) == 1
        assert recent_candles[0].volume == 1600000


class TestStrategyEntity:
    """Tests for the Strategy entity."""

    def test_strategy_creation_with_fixture(self, sample_strategy):
        """Test that strategies can be created using fixtures."""
        assert isinstance(sample_strategy, Strategy)
        assert sample_strategy.strategy_id == "test_strategy_001"
        assert sample_strategy.name == "Test MA Crossover"
        assert sample_strategy.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER

    def test_strategy_creation_with_builder(self):
        """Test that strategies can be created using the builder pattern."""
        strategy = (
            TestDataBuilder.strategy()
            .with_id("custom_strategy")
            .with_name("Custom RSI Strategy")
            .with_pair("USD_JPY")
            .with_timeframe("M15")
            .with_ma_parameters(14, 28)
            .build()
        )

        assert strategy.strategy_id == "custom_strategy"
        assert strategy.name == "Custom RSI Strategy"
        assert strategy.pair == "USD_JPY"
        assert strategy.timeframe == "M15"
        assert strategy.parameters.fast_ma_period == 14
        assert strategy.parameters.slow_ma_period == 28

    def test_strategy_activation(self, sample_strategy):
        """Test strategy activation and status changes."""
        # Initially active from fixture
        assert sample_strategy.is_active() is True

        # Deactivate
        sample_strategy.deactivate()
        assert sample_strategy.is_active() is False

        # Activate again
        sample_strategy.activate()
        assert sample_strategy.is_active() is True

    def test_strategy_parameter_validation(self):
        """Test that strategy parameters are validated correctly."""
        with pytest.raises(
            ValueError, match="Fast MA period must be less than slow MA period"
        ):
            TestDataBuilder.strategy().with_ma_parameters(50, 20).build()


@pytest.mark.unit
class TestRepositoryMocks:
    """Tests demonstrating repository mocking."""

    def test_signal_repository_mock(self, mock_signal_repository):
        """Test that signal repository mock is properly configured."""
        assert mock_signal_repository is not None
        assert hasattr(mock_signal_repository, "create")
        assert hasattr(mock_signal_repository, "get_by_id")
        assert hasattr(mock_signal_repository, "get_recent_signals")

    def test_market_data_repository_mock(self, mock_market_data_repository):
        """Test that market data repository mock is properly configured."""
        assert mock_market_data_repository is not None
        assert hasattr(mock_market_data_repository, "get_candles_by_timeframe")
        assert hasattr(mock_market_data_repository, "get_latest_candles")

    def test_strategy_repository_mock(self, mock_strategy_repository):
        """Test that strategy repository mock is properly configured."""
        assert mock_strategy_repository is not None
        assert hasattr(mock_strategy_repository, "get_active_strategies")
        assert hasattr(mock_strategy_repository, "update_strategy_status")


@pytest.mark.async_test
class TestAsyncTestInfrastructure:
    """Tests demonstrating async test capabilities."""

    @pytest.mark.asyncio
    async def test_async_repository_operations(self, mock_signal_repository):
        """Test async repository operations with mocks."""
        # Configure mock to return a signal
        test_signal = TestDataBuilder.signal().with_id("async_test_signal").build()
        mock_signal_repository.get_by_id.return_value = test_signal

        # Test the async call
        result = await mock_signal_repository.get_by_id("async_test_signal")

        assert result.signal_id == "async_test_signal"
        mock_signal_repository.get_by_id.assert_called_once_with("async_test_signal")

    @pytest.mark.asyncio
    async def test_async_context_fixture(self, async_test_context):
        """Test the async context fixture."""
        assert async_test_context is not None
        assert "start_time" in async_test_context
        assert "test_data" in async_test_context
        assert "cleanup_tasks" in async_test_context
