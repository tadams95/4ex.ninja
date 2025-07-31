"""
Market Data Service Interface
Defines the interface for market data operations and analysis.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from ...core.entities.market_data import MarketData, Candle, Granularity


class IMarketDataService(ABC):
    """
    Market data service interface for data retrieval and analysis.
    """

    @abstractmethod
    async def get_latest_price(self, pair: str) -> Optional[Decimal]:
        """
        Get latest price for a currency pair.

        Args:
            pair: Currency pair (e.g., "EUR_USD")

        Returns:
            Latest price if available
        """
        pass

    @abstractmethod
    async def get_candles(
        self,
        pair: str,
        granularity: Granularity,
        count: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Candle]:
        """
        Get historical candle data.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            count: Number of candles to retrieve
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            List of candles
        """
        pass

    @abstractmethod
    async def get_spread(self, pair: str) -> Optional[Decimal]:
        """
        Get current spread for a currency pair.

        Args:
            pair: Currency pair

        Returns:
            Current spread
        """
        pass

    @abstractmethod
    async def calculate_moving_average(
        self, pair: str, granularity: Granularity, period: int, ma_type: str = "SMA"
    ) -> List[Decimal]:
        """
        Calculate moving average for a pair.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            period: MA period
            ma_type: Type of MA (SMA, EMA, etc.)

        Returns:
            List of MA values
        """
        pass

    @abstractmethod
    async def calculate_rsi(
        self, pair: str, granularity: Granularity, period: int = 14
    ) -> List[Decimal]:
        """
        Calculate RSI indicator.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            period: RSI period

        Returns:
            List of RSI values
        """
        pass

    @abstractmethod
    async def calculate_bollinger_bands(
        self, pair: str, granularity: Granularity, period: int = 20, std_dev: int = 2
    ) -> Dict[str, List[Decimal]]:
        """
        Calculate Bollinger Bands.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            period: Period for calculation
            std_dev: Standard deviation multiplier

        Returns:
            Dictionary with upper, middle, lower bands
        """
        pass

    @abstractmethod
    async def detect_patterns(
        self, pair: str, granularity: Granularity, pattern_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect chart patterns in price data.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            pattern_types: Types of patterns to detect

        Returns:
            List of detected patterns
        """
        pass

    @abstractmethod
    async def get_support_resistance(
        self, pair: str, granularity: Granularity, lookback_periods: int = 100
    ) -> Dict[str, List[Decimal]]:
        """
        Calculate support and resistance levels.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            lookback_periods: Number of periods to analyze

        Returns:
            Dictionary with support and resistance levels
        """
        pass

    @abstractmethod
    async def get_volatility(
        self, pair: str, granularity: Granularity, period: int = 20
    ) -> Decimal:
        """
        Calculate volatility for a pair.

        Args:
            pair: Currency pair
            granularity: Candle granularity
            period: Period for calculation

        Returns:
            Volatility value
        """
        pass

    @abstractmethod
    async def start_price_stream(self, pairs: List[str]) -> None:
        """
        Start streaming price data for specified pairs.

        Args:
            pairs: List of currency pairs to stream
        """
        pass

    @abstractmethod
    async def stop_price_stream(self) -> None:
        """Stop streaming price data."""
        pass

    @abstractmethod
    async def get_market_status(self, pair: str) -> Dict[str, Any]:
        """
        Get market status for a pair.

        Args:
            pair: Currency pair

        Returns:
            Market status information
        """
        pass

    @abstractmethod
    async def synchronize_data(
        self, pair: str, granularity: Granularity, max_gaps: int = 100
    ) -> bool:
        """
        Synchronize historical data (fill gaps).

        Args:
            pair: Currency pair
            granularity: Candle granularity
            max_gaps: Maximum gaps to fill

        Returns:
            True if synchronization successful
        """
        pass
