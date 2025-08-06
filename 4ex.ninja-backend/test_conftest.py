"""
Test file to verify conftest.py fixtures are working correctly.
"""

import pytest
from src.core.entities.signal import Signal, SignalType, CrossoverType
from src.core.entities.market_data import MarketData, Granularity
from src.core.entities.strategy import Strategy, StrategyType


def test_sample_signal_fixture(sample_signal):
    """Test that the sample_signal fixture creates a valid Signal."""
    assert isinstance(sample_signal, Signal)
    assert sample_signal.signal_id == "test_signal_001"
    assert sample_signal.pair == "EUR_USD"
    assert sample_signal.timeframe == "H4"
    assert sample_signal.signal_type == SignalType.BUY
    assert sample_signal.crossover_type == CrossoverType.BULLISH
    assert sample_signal.fast_ma == 20
    assert sample_signal.slow_ma == 50


def test_sample_market_data_fixture(sample_market_data):
    """Test that the sample_market_data fixture creates valid MarketData."""
    assert isinstance(sample_market_data, MarketData)
    assert sample_market_data.instrument == "EUR_USD"
    assert sample_market_data.granularity == Granularity.H4
    assert len(sample_market_data.candles) == 2
    assert sample_market_data.candles[0].volume == 1500000
    assert sample_market_data.candles[1].volume == 1600000


def test_sample_strategy_fixture(sample_strategy):
    """Test that the sample_strategy fixture creates a valid Strategy."""
    assert isinstance(sample_strategy, Strategy)
    assert sample_strategy.strategy_id == "test_strategy_001"
    assert sample_strategy.name == "Test MA Crossover"
    assert sample_strategy.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER
    assert sample_strategy.pair == "EUR_USD"
    assert sample_strategy.timeframe == "H4"
    assert sample_strategy.parameters.fast_ma_period == 20
    assert sample_strategy.parameters.slow_ma_period == 50


def test_sample_signals_list_fixture(sample_signals_list):
    """Test that the sample_signals_list fixture creates valid signals."""
    assert len(sample_signals_list) == 4
    assert all(isinstance(signal, Signal) for signal in sample_signals_list)

    # Check that we have different pairs
    pairs = [signal.pair for signal in sample_signals_list]
    assert "EUR_USD" in pairs
    assert "GBP_USD" in pairs
    assert "USD_JPY" in pairs
    assert "AUD_USD" in pairs


def test_sample_market_data_list_fixture(sample_market_data_list):
    """Test that the sample_market_data_list fixture creates valid market data."""
    assert len(sample_market_data_list) == 10
    assert all(isinstance(data, MarketData) for data in sample_market_data_list)
    assert all(data.instrument == "EUR_USD" for data in sample_market_data_list)
    assert all(data.granularity == Granularity.H4 for data in sample_market_data_list)


def test_mock_repositories_fixture(
    mock_signal_repository, mock_market_data_repository, mock_strategy_repository
):
    """Test that the mock repository fixtures are available."""
    # These should all be AsyncMock objects
    assert mock_signal_repository is not None
    assert mock_market_data_repository is not None
    assert mock_strategy_repository is not None

    # Verify they have the expected methods
    assert hasattr(mock_signal_repository, "create")
    assert hasattr(mock_signal_repository, "get_by_id")
    assert hasattr(mock_market_data_repository, "get_candles_by_timeframe")
    assert hasattr(mock_strategy_repository, "get_active_strategies")
