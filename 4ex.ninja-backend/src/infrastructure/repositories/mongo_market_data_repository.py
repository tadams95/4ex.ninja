"""
MongoDB MarketData Repository Implementation - Concrete implementation for MarketData entities

This module provides the MongoDB-specific implementation of the MarketData repository,
extending the base MongoDB repository with MarketData-specific operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .mongo_base_repository import MongoBaseRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...core.entities.market_data import MarketData, Candle, Granularity
from ...core.interfaces.repository import RepositoryError

logger = logging.getLogger(__name__)


class MongoMarketDataRepository(MongoBaseRepository[MarketData], IMarketDataRepository):
    """
    MongoDB implementation of the MarketData repository.

    Extends the base MongoDB repository with MarketData-specific query operations.
    """

    def __init__(self, database: Any):
        """
        Initialize the MarketData repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "market_data", MarketData)

    async def get_by_pair_and_timeframe(
        self, pair: str, granularity: Granularity, limit: Optional[int] = None
    ) -> Optional[MarketData]:
        """Get market data for a specific pair and timeframe."""
        try:
            filters = {"instrument": pair, "granularity": granularity}

            results = await self.find_by_criteria(filters, limit=1)
            return results[0] if results else None

        except Exception as e:
            raise RepositoryError(
                f"Failed to get market data for {pair} {granularity}", original_error=e
            )

    async def get_latest_candles(
        self, pair: str, granularity: Granularity, count: int
    ) -> List[Candle]:
        """Get the latest N candles for a pair and timeframe."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data or not market_data.candles:
                return []

            # Sort candles by time and get the latest ones
            sorted_candles = sorted(
                market_data.candles, key=lambda c: c.time, reverse=True
            )
            return sorted_candles[:count]

        except Exception as e:
            raise RepositoryError(
                f"Failed to get latest candles for {pair} {granularity}",
                original_error=e,
            )

    async def get_candles_by_date_range(
        self,
        pair: str,
        granularity: Granularity,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Candle]:
        """Get candles within a specific date range."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data or not market_data.candles:
                return []

            # Filter candles by date range
            filtered_candles = [
                candle
                for candle in market_data.candles
                if start_date <= candle.time <= end_date
            ]

            # Sort by time
            return sorted(filtered_candles, key=lambda c: c.time)

        except Exception as e:
            raise RepositoryError(
                f"Failed to get candles by date range for {pair} {granularity}",
                original_error=e,
            )

    async def add_candles(
        self, pair: str, granularity: Granularity, candles: List[Candle]
    ) -> bool:
        """Add new candles to existing market data."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)

            if not market_data:
                # Create new market data if it doesn't exist
                market_data = MarketData(
                    instrument=pair, granularity=granularity, candles=candles
                )
                await self.create(market_data)
            else:
                # Add new candles and avoid duplicates
                existing_timestamps = {c.time for c in market_data.candles}
                new_candles = [c for c in candles if c.time not in existing_timestamps]

                if new_candles:
                    market_data.candles.extend(new_candles)
                    market_data.last_updated = datetime.utcnow()
                    await self.update(market_data)

            logger.info(f"Added {len(candles)} candles for {pair} {granularity}")
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to add candles for {pair} {granularity}", original_error=e
            )

    async def update_latest_candle(
        self, pair: str, granularity: Granularity, candle: Candle
    ) -> bool:
        """Update the latest candle for a pair and timeframe."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data:
                return False

            # Find and update the latest candle or add if not exists
            updated = False
            for i, existing_candle in enumerate(market_data.candles):
                if existing_candle.time == candle.time:
                    market_data.candles[i] = candle
                    updated = True
                    break

            if not updated:
                market_data.candles.append(candle)

            market_data.last_updated = datetime.utcnow()
            await self.update(market_data)

            logger.info(
                f"Updated latest candle for {pair} {granularity} at {candle.time}"
            )
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to update latest candle for {pair} {granularity}",
                original_error=e,
            )

    async def get_pairs_with_data(self) -> List[str]:
        """Get all currency pairs that have market data."""
        try:
            # Get distinct instruments from the collection
            pairs = await self._collection.distinct("instrument")
            return sorted(pairs)

        except Exception as e:
            raise RepositoryError("Failed to get pairs with data", original_error=e)

    async def get_available_timeframes(self, pair: str) -> List[Granularity]:
        """Get all available timeframes for a specific pair."""
        try:
            # Get distinct granularities for the pair
            granularities = await self._collection.distinct(
                "granularity", {"instrument": pair}
            )

            # Convert string values back to Granularity enum
            return [
                Granularity(g)
                for g in granularities
                if g in [gv.value for gv in Granularity]
            ]

        except Exception as e:
            raise RepositoryError(
                f"Failed to get available timeframes for {pair}", original_error=e
            )

    async def get_data_coverage(
        self, pair: str, granularity: Granularity
    ) -> Dict[str, datetime]:
        """Get data coverage information for a pair and timeframe."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data or not market_data.candles:
                return {"first_candle": None, "last_candle": None}  # type: ignore

            sorted_candles = sorted(market_data.candles, key=lambda c: c.time)

            return {
                "first_candle": sorted_candles[0].time,
                "last_candle": sorted_candles[-1].time,
            }

        except Exception as e:
            raise RepositoryError(
                f"Failed to get data coverage for {pair} {granularity}",
                original_error=e,
            )

    async def calculate_technical_indicators(
        self,
        pair: str,
        granularity: Granularity,
        indicator: str,
        parameters: Dict[str, Any],
    ) -> List[float]:
        """Calculate technical indicators for market data."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data:
                return []

            if indicator.upper() == "SMA":
                period = parameters.get("period", 20)
                sma_value = market_data.calculate_sma(period)
                return [float(sma_value)] if sma_value is not None else []
            elif indicator.upper() == "ATR":
                period = parameters.get("period", 14)
                atr_value = market_data.calculate_atr(period)
                return [float(atr_value)] if atr_value is not None else []
            else:
                raise RepositoryError(f"Unsupported indicator: {indicator}")

        except Exception as e:
            raise RepositoryError(
                f"Failed to calculate {indicator} for {pair} {granularity}",
                original_error=e,
            )

    async def cleanup_old_data(
        self, pair: str, granularity: Granularity, keep_days: int
    ) -> int:
        """Clean up old market data beyond the specified retention period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data:
                return 0

            original_count = len(market_data.candles)

            # Keep only candles newer than cutoff date
            market_data.candles = [
                candle for candle in market_data.candles if candle.time >= cutoff_date
            ]

            removed_count = original_count - len(market_data.candles)

            if removed_count > 0:
                market_data.last_updated = datetime.utcnow()
                await self.update(market_data)

                logger.info(
                    f"Cleaned up {removed_count} old candles for {pair} {granularity}"
                )

            return removed_count

        except Exception as e:
            raise RepositoryError(
                f"Failed to cleanup old data for {pair} {granularity}", original_error=e
            )

    async def validate_data_integrity(
        self, pair: str, granularity: Granularity
    ) -> Dict[str, Any]:
        """Validate data integrity for a pair and timeframe."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data:
                return {"valid": False, "issues": ["No market data found"]}

            issues = []

            # Check for duplicate timestamps
            timestamps = [c.time for c in market_data.candles]
            if len(timestamps) != len(set(timestamps)):
                issues.append("Duplicate timestamps found")

            # Check for gaps in data (basic check)
            sorted_candles = sorted(market_data.candles, key=lambda c: c.time)
            for i in range(1, len(sorted_candles)):
                time_diff = sorted_candles[i].time - sorted_candles[i - 1].time
                # Basic gap detection - assume 1 hour max gap for most timeframes
                if time_diff.total_seconds() > 3600 * 2:  # 2 hours
                    issues.append(
                        f"Large time gap detected around {sorted_candles[i].time}"
                    )
                    break

            # Check for basic OHLC validation
            for candle in market_data.candles:
                try:
                    candle.validate()
                except ValueError as e:
                    issues.append(f"Invalid OHLC data at {candle.time}: {str(e)}")
                    break

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "total_candles": len(market_data.candles),
                "date_range": await self.get_data_coverage(pair, granularity),
            }

        except Exception as e:
            raise RepositoryError(
                f"Failed to validate data integrity for {pair} {granularity}",
                original_error=e,
            )

    async def get_price_at_time(
        self, pair: str, granularity: Granularity, timestamp: datetime
    ) -> Optional[Decimal]:
        """Get the price at a specific timestamp."""
        try:
            market_data = await self.get_by_pair_and_timeframe(pair, granularity)
            if not market_data:
                return None

            # Find the closest candle to the timestamp
            closest_candle = None
            min_diff = float("inf")

            for candle in market_data.candles:
                diff = abs((candle.time - timestamp).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest_candle = candle

            return closest_candle.close if closest_candle else None

        except Exception as e:
            raise RepositoryError(
                f"Failed to get price at time for {pair} {granularity}",
                original_error=e,
            )
