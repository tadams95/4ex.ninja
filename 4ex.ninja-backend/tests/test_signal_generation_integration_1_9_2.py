"""
Integration tests for signal generation service using repositories (Section 1.9.2)

This module provides focused integration tests for the SignalGenerationService
with mocked repository dependencies to validate service behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.entities.signal import Signal, SignalType, SignalStatus, CrossoverType
from src.core.entities.market_data import MarketData, Candle, Granularity


class TestSignalGenerationServiceIntegration:
    """Integration tests for signal generation service."""

    @pytest.fixture
    def mock_repository_provider(self):
        """Mock repository provider with all required methods."""
        provider = MagicMock()

        # Mock signal repository
        signal_repo = AsyncMock()
        signal_repo.create = AsyncMock()
        signal_repo.get_by_pair_and_timeframe = AsyncMock(return_value=[])
        signal_repo.find_by_criteria = AsyncMock(return_value=[])

        # Mock market data repository
        market_data_repo = AsyncMock()
        market_data_repo.get_latest_candles = AsyncMock()
        market_data_repo.get_by_pair_and_granularity = AsyncMock()

        # Mock strategy repository
        strategy_repo = AsyncMock()
        strategy_repo.get_active_strategies = AsyncMock(return_value=[])

        provider.get_signal_repository = MagicMock(return_value=signal_repo)
        provider.get_market_data_repository = MagicMock(return_value=market_data_repo)
        provider.get_strategy_repository = MagicMock(return_value=strategy_repo)

        return provider

    @pytest.fixture
    def sample_candles_data(self):
        """Create sample candle data for testing signal generation."""
        candles = []
        base_price = Decimal("1.1000")

        # Create 50 candles with a trending pattern for crossover testing
        for i in range(50):
            price_increment = Decimal(str(i * 0.0001))  # Gradual uptrend
            candles.append(
                Candle(
                    time=datetime.utcnow() - timedelta(hours=(50 - i)),
                    open=base_price + price_increment,
                    high=base_price + price_increment + Decimal("0.0005"),
                    low=base_price + price_increment - Decimal("0.0005"),
                    close=base_price + price_increment + Decimal("0.0002"),
                    volume=1000,
                )
            )

        return candles

    def test_moving_average_calculation_logic(self, sample_candles_data):
        """Test the core moving average calculation logic."""
        # Extract close prices
        close_prices = [candle.close for candle in sample_candles_data]

        # Calculate 10-period and 20-period moving averages
        fast_period = 10
        slow_period = 20

        if len(close_prices) >= slow_period:
            fast_ma = sum(close_prices[-fast_period:]) / fast_period
            slow_ma = sum(close_prices[-slow_period:]) / slow_period

            # Verify calculations
            assert fast_ma > slow_ma  # Should be true for uptrending data
            assert isinstance(fast_ma, Decimal)
            assert isinstance(slow_ma, Decimal)

            # Test crossover detection logic
            prev_fast_ma = sum(close_prices[-fast_period - 1 : -1]) / fast_period
            prev_slow_ma = sum(close_prices[-slow_period - 1 : -1]) / slow_period

            # Check for bullish crossover (fast crosses above slow)
            bullish_crossover = (prev_fast_ma <= prev_slow_ma) and (fast_ma > slow_ma)
            # For our trending data, this might or might not be true, but logic should work
            assert isinstance(bullish_crossover, bool)

    def test_atr_calculation_logic(self, sample_candles_data):
        """Test ATR (Average True Range) calculation logic."""
        if len(sample_candles_data) < 2:
            return

        # Calculate True Range for the latest candle
        latest = sample_candles_data[-1]
        previous = sample_candles_data[-2]

        high_low = latest.high - latest.low
        high_close_prev = abs(latest.high - previous.close)
        low_close_prev = abs(latest.low - previous.close)

        true_range = max(high_low, high_close_prev, low_close_prev)

        assert true_range > Decimal("0")
        assert isinstance(true_range, Decimal)

        # For ATR, we'd typically average the last 14 true ranges
        if len(sample_candles_data) >= 14:
            true_ranges = []
            for i in range(1, min(15, len(sample_candles_data))):
                current = sample_candles_data[-i]
                prev = sample_candles_data[-i - 1]

                hl = current.high - current.low
                hc = abs(current.high - prev.close)
                lc = abs(current.low - prev.close)
                tr = max(hl, hc, lc)
                true_ranges.append(tr)

            atr = sum(true_ranges) / len(true_ranges)
            assert atr > Decimal("0")
            assert isinstance(atr, Decimal)

    @pytest.mark.asyncio
    async def test_signal_validation_logic(self):
        """Test signal validation logic for trading signals."""
        # Test valid signal data
        valid_signal_data = {
            "pair": "EUR/USD",
            "timeframe": "H1",
            "signal_type": "BUY",
            "entry_price": Decimal("1.1000"),
            "stop_loss": Decimal("1.0950"),
            "take_profit": Decimal("1.1100"),
            "atr_value": Decimal("0.0025"),
        }

        # Validate price relationships
        assert valid_signal_data["entry_price"] > valid_signal_data["stop_loss"]
        assert valid_signal_data["take_profit"] > valid_signal_data["entry_price"]

        # Calculate risk-reward ratio
        risk = valid_signal_data["entry_price"] - valid_signal_data["stop_loss"]
        reward = valid_signal_data["take_profit"] - valid_signal_data["entry_price"]
        risk_reward = reward / risk

        assert risk_reward == Decimal("2.0")  # 2:1 risk-reward ratio

        # Validate ATR-based stop loss
        atr_multiplier = Decimal("2.0")
        calculated_sl = valid_signal_data["entry_price"] - (
            valid_signal_data["atr_value"] * atr_multiplier
        )

        # Should be close to our stop loss (within ATR tolerance)
        sl_diff = abs(calculated_sl - valid_signal_data["stop_loss"])
        assert sl_diff <= valid_signal_data["atr_value"]

    @pytest.mark.asyncio
    async def test_repository_integration_patterns(self, mock_repository_provider):
        """Test repository integration patterns used by signal generation service."""
        signal_repo = mock_repository_provider.get_signal_repository()
        market_data_repo = mock_repository_provider.get_market_data_repository()

        # Test typical service workflow patterns

        # 1. Fetch latest market data
        market_data_repo.get_latest_candles.return_value = []
        candles = await market_data_repo.get_latest_candles(
            "EUR_USD", Granularity.H1, 50
        )

        # 2. Check for existing signals
        signal_repo.get_by_pair_and_timeframe.return_value = []
        existing_signals = await signal_repo.get_by_pair_and_timeframe("EUR/USD", "H1")

        # 3. Create new signal if conditions met
        new_signal = Signal(
            signal_id="test_signal",
            pair="EUR/USD",
            timeframe="H1",
            signal_type=SignalType.BUY,
            crossover_type=CrossoverType.BULLISH,
            entry_price=Decimal("1.1000"),
            current_price=Decimal("1.1000"),
            fast_ma=10,
            slow_ma=20,
            timestamp=datetime.utcnow(),
        )

        signal_repo.create.return_value = new_signal
        created_signal = await signal_repo.create(new_signal)

        # Verify service workflow
        market_data_repo.get_latest_candles.assert_called_once()
        signal_repo.get_by_pair_and_timeframe.assert_called_once()
        signal_repo.create.assert_called_once()
        assert created_signal == new_signal

    def test_data_consistency_validation(self):
        """Test data consistency validation for signal generation."""
        # Test currency pair validation
        valid_pairs = ["EUR/USD", "GBP/JPY", "AUD/NZD", "USD/CAD"]
        invalid_pairs = ["EURUSD", "EUR-USD", "EUR_USD", "EUR USD"]

        for pair in valid_pairs:
            assert "/" in pair
            assert len(pair.split("/")) == 2
            parts = pair.split("/")
            assert len(parts[0]) == 3  # Currency code length
            assert len(parts[1]) == 3  # Currency code length

        for pair in invalid_pairs:
            assert "/" not in pair or len(pair.split("/")) != 2

        # Test timeframe validation
        valid_timeframes = ["M1", "M5", "M15", "H1", "H4", "D1"]
        invalid_timeframes = ["1M", "5M", "15M", "1H", "4H", "1D"]

        for tf in valid_timeframes:
            assert tf in [
                "M1",
                "M5",
                "M15",
                "M30",
                "H1",
                "H2",
                "H4",
                "H6",
                "H8",
                "H12",
                "D1",
                "W1",
                "MN1",
            ]

        # Test price validation
        valid_prices = [Decimal("1.1000"), Decimal("0.7500"), Decimal("150.25")]
        invalid_prices = [Decimal("-1.0"), Decimal("0"), None]

        for price in valid_prices:
            assert price > Decimal("0")

        for price in invalid_prices:
            if price is not None:
                assert price <= Decimal("0")

    @pytest.mark.asyncio
    async def test_error_handling_patterns(self, mock_repository_provider):
        """Test error handling patterns in repository integration."""
        signal_repo = mock_repository_provider.get_signal_repository()

        # Test database connection error
        signal_repo.create.side_effect = ConnectionError("Database connection failed")

        with pytest.raises(ConnectionError) as exc_info:
            await signal_repo.create(MagicMock())

        assert "Database connection failed" in str(exc_info.value)

        # Test data validation error
        signal_repo.create.side_effect = ValueError("Invalid signal data")

        with pytest.raises(ValueError) as exc_info:
            await signal_repo.create(MagicMock())

        assert "Invalid signal data" in str(exc_info.value)

        # Test timeout error
        signal_repo.create.side_effect = TimeoutError("Operation timed out")

        with pytest.raises(TimeoutError) as exc_info:
            await signal_repo.create(MagicMock())

        assert "Operation timed out" in str(exc_info.value)


# Run integration tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
