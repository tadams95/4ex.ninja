"""
Base data provider interface for swing trading backtesting.

This module defines the abstract base class for data providers, focusing on
swing trading requirements with 4H, Daily, and Weekly timeframes.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SwingCandleData:
    """
    Candle data optimized for swing trading timeframes.

    Attributes:
        timestamp: Time of the candle
        open: Opening price
        high: Highest price
        close: Closing price
        low: Lowest price
        volume: Trading volume (if available)
        spread: Average spread during the period
    """

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Optional[int] = None
    spread: Optional[Decimal] = None


@dataclass
class DataQualityMetrics:
    """
    Data quality metrics for swing trading validation.

    Attributes:
        missing_candles: Number of missing candles in the period
        gap_percentage: Percentage of time gaps in data
        outlier_count: Number of price outliers detected
        spread_consistency: Spread consistency score (0-1)
        last_update: Last data update timestamp
    """

    missing_candles: int
    gap_percentage: float
    outlier_count: int
    spread_consistency: float
    last_update: datetime


class BaseDataProvider(ABC):
    """
    Abstract base class for data providers optimized for swing trading.

    This interface focuses on longer timeframes (4H, Daily, Weekly) and
    simplified data validation suitable for swing trading strategies.
    """

    # Supported timeframes for swing trading
    SWING_TIMEFRAMES = ["4H", "D", "W"]

    # Major forex pairs for swing trading
    MAJOR_PAIRS = [
        "EUR_USD",
        "GBP_USD",
        "USD_JPY",
        "USD_CHF",
        "AUD_USD",
        "USD_CAD",
        "NZD_USD",
    ]

    def __init__(self, name: str, priority: int = 1):
        """
        Initialize the data provider.

        Args:
            name: Provider name (e.g., 'oanda', 'alpha_vantage')
            priority: Provider priority (1=primary, 2=secondary, etc.)
        """
        self.name = name
        self.priority = priority
        self.is_available = False
        self.last_health_check = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the data provider.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_candles(
        self,
        pair: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        count: Optional[int] = None,
    ) -> List[SwingCandleData]:
        """
        Retrieve historical candle data for swing trading.

        Args:
            pair: Currency pair (e.g., 'EUR_USD')
            timeframe: Timeframe ('4H', 'D', 'W')
            start_time: Start datetime
            end_time: End datetime
            count: Maximum number of candles (optional)

        Returns:
            List of candle data
        """
        pass

    @abstractmethod
    async def get_current_spread(self, pair: str) -> Optional[Decimal]:
        """
        Get current spread for a currency pair.

        Args:
            pair: Currency pair

        Returns:
            Current spread in pips, None if unavailable
        """
        pass

    @abstractmethod
    async def get_average_spread(self, pair: str, days: int = 30) -> Optional[Decimal]:
        """
        Get average spread for a currency pair over specified days.

        Args:
            pair: Currency pair
            days: Number of days to calculate average

        Returns:
            Average spread in pips, None if unavailable
        """
        pass

    @abstractmethod
    async def validate_data_quality(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> DataQualityMetrics:
        """
        Validate data quality for the specified period.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Data quality metrics
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform health check on the data provider.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    def supports_timeframe(self, timeframe: str) -> bool:
        """
        Check if timeframe is supported for swing trading.

        Args:
            timeframe: Timeframe to check

        Returns:
            True if supported, False otherwise
        """
        return timeframe in self.SWING_TIMEFRAMES

    def supports_pair(self, pair: str) -> bool:
        """
        Check if currency pair is supported.

        Args:
            pair: Currency pair to check

        Returns:
            True if supported, False otherwise
        """
        return pair in self.MAJOR_PAIRS

    async def get_swap_rate(self, pair: str) -> Optional[Decimal]:
        """
        Get swap rate for overnight positions (default implementation).

        Args:
            pair: Currency pair

        Returns:
            Daily swap rate, None if unavailable
        """
        # Default implementation returns None
        # Providers can override with actual swap rate data
        return None

    def calculate_pip_value(self, pair: str, position_size: Decimal) -> Decimal:
        """
        Calculate pip value for position sizing.

        Args:
            pair: Currency pair
            position_size: Position size in base currency units

        Returns:
            Value of one pip for the position
        """
        # Standard pip values for major pairs
        if pair.endswith("JPY"):
            # JPY pairs: 1 pip = 0.01
            pip_size = Decimal("0.01")
        else:
            # Other major pairs: 1 pip = 0.0001
            pip_size = Decimal("0.0001")

        return position_size * pip_size

    def __str__(self) -> str:
        """String representation of the provider."""
        return (
            f"{self.name} (Priority: {self.priority}, Available: {self.is_available})"
        )
