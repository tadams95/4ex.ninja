"""
MarketData Repository Interface - Domain-specific repository for MarketData entities

This module defines the MarketData repository interface with domain-specific
methods for MarketData and Candle operations.
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .repository import IBaseRepository
from ..entities.market_data import MarketData, Candle, Granularity


class IMarketDataRepository(IBaseRepository[MarketData]):
    """
    MarketData repository interface defining MarketData-specific data access methods.

    Extends the base repository with domain-specific operations for MarketData entities.
    """

    @abstractmethod
    async def get_by_pair_and_timeframe(
        self, pair: str, granularity: Granularity, limit: Optional[int] = None
    ) -> Optional[MarketData]:
        """
        Get market data for a specific pair and timeframe.

        Args:
            pair: The currency pair (e.g., "EUR_USD")
            granularity: The timeframe granularity
            limit: Maximum number of candles to include

        Returns:
            MarketData object if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_latest_candles(
        self, pair: str, granularity: Granularity, count: int
    ) -> List[Candle]:
        """
        Get the latest N candles for a pair and timeframe.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            count: Number of latest candles to retrieve

        Returns:
            List of latest candles
        """
        pass

    @abstractmethod
    async def get_candles_by_date_range(
        self,
        pair: str,
        granularity: Granularity,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Candle]:
        """
        Get candles within a specific date range.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            List of candles within the date range
        """
        pass

    @abstractmethod
    async def add_candles(
        self, pair: str, granularity: Granularity, candles: List[Candle]
    ) -> bool:
        """
        Add new candles to existing market data.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            candles: List of candles to add

        Returns:
            True if candles added successfully, False otherwise
        """
        pass

    @abstractmethod
    async def update_latest_candle(
        self, pair: str, granularity: Granularity, candle: Candle
    ) -> bool:
        """
        Update the latest candle for a pair and timeframe.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            candle: The updated candle data

        Returns:
            True if update successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_pairs_with_data(self) -> List[str]:
        """
        Get all currency pairs that have market data.

        Returns:
            List of currency pairs with available data
        """
        pass

    @abstractmethod
    async def get_available_timeframes(self, pair: str) -> List[Granularity]:
        """
        Get all available timeframes for a specific pair.

        Args:
            pair: The currency pair

        Returns:
            List of available granularities for the pair
        """
        pass

    @abstractmethod
    async def get_data_coverage(
        self, pair: str, granularity: Granularity
    ) -> Dict[str, Any]:
        """
        Get data coverage information for a pair and timeframe.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity

        Returns:
            Dictionary with 'first_candle', 'last_candle' timestamps and 'total_candles' count
        """
        pass

    @abstractmethod
    async def calculate_technical_indicators(
        self,
        pair: str,
        granularity: Granularity,
        indicator: str,
        parameters: Dict[str, Any],
    ) -> List[float]:
        """
        Calculate technical indicators for market data.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            indicator: The indicator name (e.g., "SMA", "ATR")
            parameters: Indicator parameters (e.g., {"period": 20})

        Returns:
            List of indicator values
        """
        pass

    @abstractmethod
    async def cleanup_old_data(
        self, pair: str, granularity: Granularity, keep_days: int
    ) -> int:
        """
        Clean up old market data beyond the specified retention period.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            keep_days: Number of days to retain

        Returns:
            Number of candles removed
        """
        pass

    @abstractmethod
    async def validate_data_integrity(
        self, pair: str, granularity: Granularity
    ) -> Dict[str, Any]:
        """
        Validate data integrity for a pair and timeframe.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity

        Returns:
            Dictionary with validation results and any issues found
        """
        pass

    @abstractmethod
    async def get_price_at_time(
        self, pair: str, granularity: Granularity, timestamp: datetime
    ) -> Optional[Decimal]:
        """
        Get the price at a specific timestamp.

        Args:
            pair: The currency pair
            granularity: The timeframe granularity
            timestamp: The specific timestamp

        Returns:
            Price at the timestamp if available, None otherwise
        """
        pass
