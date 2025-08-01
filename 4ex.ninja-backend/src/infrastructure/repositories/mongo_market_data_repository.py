"""
MongoDB MarketData Repository Implementation

Concrete implementation of IMarketDataRepository for MongoDB database operations.
Provides optimized queries and time-series data access methods for market data.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from .mongo_base_repository import MongoBaseRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...core.entities.market_data import MarketData, Candle, Granularity
from ...core.interfaces.repository import RepositoryError

# Set up logging
logger = logging.getLogger(__name__)


class MongoMarketDataRepository(MongoBaseRepository[MarketData], IMarketDataRepository):
    """
    MongoDB implementation of market data repository.

    Provides optimized time-series queries and market data operations including
    candle management, technical indicators, and data validation.
    """

    def __init__(self, database: Any, session: Optional[Any] = None):
        """
        Initialize the market data repository.

        Args:
            database: MongoDB database instance
            session: Optional MongoDB session for transactions
        """
        super().__init__(database, "market_data", MarketData, session)

    async def get_by_pair_and_timeframe(
        self, pair: str, granularity: Granularity, limit: Optional[int] = None
    ) -> Optional[MarketData]:
        """Get market data for a specific pair and timeframe."""
        try:
            filters = {"instrument": pair, "granularity": granularity.value}

            if limit:
                # Use aggregation to limit candles when limit is specified
                pipeline = [
                    {"$match": filters},
                    {
                        "$project": {
                            "instrument": 1,
                            "granularity": 1,
                            "last_updated": 1,
                            "candles": {
                                "$slice": ["$candles", -limit]
                            },  # Get latest N candles
                        }
                    },
                ]

                cursor = self._collection.aggregate(
                    pipeline, **self._get_session_kwargs()
                )
                results = await cursor.to_list(length=1)

                if results:
                    return self._dict_to_entity(results[0])
                return None
            else:
                results = await self.find_by_criteria(filters, limit=1)
                return results[0] if results else None

        except Exception as e:
            raise RepositoryError(
                f"Failed to get market data for {pair} {granularity.value}",
                original_error=e,
            )

    async def get_latest_candles(
        self, pair: str, granularity: Granularity, count: int
    ) -> List[Candle]:
        """Get the latest N candles for a pair and timeframe."""
        try:
            # Use aggregation pipeline for efficient latest candles retrieval
            pipeline = [
                {"$match": {"instrument": pair, "granularity": granularity.value}},
                {"$unwind": "$candles"},
                {"$sort": {"candles.time": -1}},  # Sort by candle time descending
                {"$limit": count},
                {"$group": {"_id": None, "candles": {"$push": "$candles"}}},
            ]

            cursor = self._collection.aggregate(pipeline, **self._get_session_kwargs())
            results = await cursor.to_list(length=1)

            if not results or not results[0].get("candles"):
                return []

            # Convert to Candle objects and reverse to get chronological order
            candles_data = results[0]["candles"]
            candles = []

            for candle_data in reversed(candles_data):  # Reverse to chronological order
                candle = Candle(
                    time=candle_data["time"],
                    open=Decimal(str(candle_data["open"])),
                    high=Decimal(str(candle_data["high"])),
                    low=Decimal(str(candle_data["low"])),
                    close=Decimal(str(candle_data["close"])),
                    volume=candle_data.get("volume", 0),
                )
                candles.append(candle)

            return candles

        except Exception as e:
            raise RepositoryError(
                f"Failed to get latest candles for {pair} {granularity.value}",
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
            # Use aggregation pipeline for efficient date range filtering
            pipeline = [
                {"$match": {"instrument": pair, "granularity": granularity.value}},
                {"$unwind": "$candles"},
                {"$match": {"candles.time": {"$gte": start_date, "$lte": end_date}}},
                {"$sort": {"candles.time": 1}},  # Sort chronologically
                {"$group": {"_id": None, "candles": {"$push": "$candles"}}},
            ]

            cursor = self._collection.aggregate(pipeline, **self._get_session_kwargs())
            results = await cursor.to_list(length=1)

            if not results or not results[0].get("candles"):
                return []

            # Convert to Candle objects
            candles_data = results[0]["candles"]
            candles = []

            for candle_data in candles_data:
                candle = Candle(
                    time=candle_data["time"],
                    open=Decimal(str(candle_data["open"])),
                    high=Decimal(str(candle_data["high"])),
                    low=Decimal(str(candle_data["low"])),
                    close=Decimal(str(candle_data["close"])),
                    volume=candle_data.get("volume", 0),
                )
                candles.append(candle)

            return candles

        except Exception as e:
            raise RepositoryError(
                f"Failed to get candles by date range for {pair} {granularity.value}",
                original_error=e,
            )

    async def add_candles(
        self, pair: str, granularity: Granularity, candles: List[Candle]
    ) -> bool:
        """Add new candles to existing market data."""
        try:
            if not candles:
                return True

            # Convert candles to dict format for MongoDB
            candle_dicts = []
            for candle in candles:
                candle_dicts.append(
                    {
                        "time": candle.time,
                        "open": float(candle.open),
                        "high": float(candle.high),
                        "low": float(candle.low),
                        "close": float(candle.close),
                        "volume": candle.volume,
                    }
                )

            # Use upsert with atomic operations to handle concurrent updates
            filters = {"instrument": pair, "granularity": granularity.value}

            # First, try to find existing document
            existing = await self._collection.find_one(
                filters, **self._get_session_kwargs()
            )

            if not existing:
                # Create new document
                new_doc = {
                    "instrument": pair,
                    "granularity": granularity.value,
                    "candles": candle_dicts,
                    "last_updated": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                }
                await self._collection.insert_one(new_doc, **self._get_session_kwargs())
                logger.info(
                    f"Created new market data for {pair} {granularity.value} with {len(candles)} candles"
                )
            else:
                # Get existing timestamps to avoid duplicates
                existing_times = {
                    candle["time"] for candle in existing.get("candles", [])
                }
                new_candles = [
                    c for c in candle_dicts if c["time"] not in existing_times
                ]

                if new_candles:
                    # Use $push with $each to add multiple candles atomically
                    update_doc = {
                        "$push": {"candles": {"$each": new_candles}},
                        "$set": {"last_updated": datetime.utcnow()},
                    }
                    await self._collection.update_one(
                        filters, update_doc, **self._get_session_kwargs()
                    )
                    logger.info(
                        f"Added {len(new_candles)} new candles for {pair} {granularity.value}"
                    )
                else:
                    logger.info(
                        f"No new candles to add for {pair} {granularity.value} (all already exist)"
                    )

            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to add candles for {pair} {granularity.value}",
                original_error=e,
            )

    async def update_latest_candle(
        self, pair: str, granularity: Granularity, candle: Candle
    ) -> bool:
        """Update the latest candle for a pair and timeframe."""
        try:
            filters = {"instrument": pair, "granularity": granularity.value}

            # Convert candle to dict format
            candle_dict = {
                "time": candle.time,
                "open": float(candle.open),
                "high": float(candle.high),
                "low": float(candle.low),
                "close": float(candle.close),
                "volume": candle.volume,
            }

            # Use arrayFilters to update specific candle by timestamp
            update_doc = {
                "$set": {
                    "candles.$[elem]": candle_dict,
                    "last_updated": datetime.utcnow(),
                }
            }

            array_filters = [{"elem.time": candle.time}]

            result = await self._collection.update_one(
                filters,
                update_doc,
                array_filters=array_filters,
                **self._get_session_kwargs(),
            )

            if result.modified_count == 0:
                # Candle doesn't exist, add it instead
                add_doc = {
                    "$push": {"candles": candle_dict},
                    "$set": {"last_updated": datetime.utcnow()},
                }
                result = await self._collection.update_one(
                    filters, add_doc, **self._get_session_kwargs()
                )

                if result.modified_count > 0:
                    logger.info(
                        f"Added new candle for {pair} {granularity.value} at {candle.time}"
                    )
                else:
                    logger.warning(
                        f"Failed to add candle for {pair} {granularity.value}"
                    )
                    return False
            else:
                logger.info(
                    f"Updated candle for {pair} {granularity.value} at {candle.time}"
                )

            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to update latest candle for {pair} {granularity.value}",
                original_error=e,
            )

    async def get_pairs_with_data(self) -> List[str]:
        """Get all currency pairs that have market data."""
        try:
            # Use distinct operation with session support
            pairs = await self._collection.distinct(
                "instrument", {}, **self._get_session_kwargs()
            )
            return sorted(pairs)

        except Exception as e:
            raise RepositoryError("Failed to get pairs with data", original_error=e)

    async def get_available_timeframes(self, pair: str) -> List[Granularity]:
        """Get all available timeframes for a specific pair."""
        try:
            # Get distinct granularities for the pair with session support
            granularities = await self._collection.distinct(
                "granularity", {"instrument": pair}, **self._get_session_kwargs()
            )

            # Convert string values back to Granularity enum
            valid_timeframes = []
            for g in granularities:
                try:
                    timeframe = Granularity(g)
                    valid_timeframes.append(timeframe)
                except ValueError:
                    logger.warning(f"Invalid granularity value found: {g}")
                    continue

            return sorted(valid_timeframes, key=lambda x: x.value)

        except Exception as e:
            raise RepositoryError(
                f"Failed to get available timeframes for {pair}", original_error=e
            )

    async def get_data_coverage(
        self, pair: str, granularity: Granularity
    ) -> Dict[str, Any]:
        """Get data coverage information for a pair and timeframe."""
        try:
            # Use aggregation pipeline for efficient min/max calculation
            pipeline = [
                {"$match": {"instrument": pair, "granularity": granularity.value}},
                {"$unwind": "$candles"},
                {
                    "$group": {
                        "_id": None,
                        "first_candle": {"$min": "$candles.time"},
                        "last_candle": {"$max": "$candles.time"},
                        "total_candles": {"$sum": 1},
                    }
                },
            ]

            cursor = self._collection.aggregate(pipeline, **self._get_session_kwargs())
            results = await cursor.to_list(length=1)

            if not results:
                return {"first_candle": None, "last_candle": None, "total_candles": 0}

            result = results[0]
            return {
                "first_candle": result.get("first_candle"),
                "last_candle": result.get("last_candle"),
                "total_candles": result.get("total_candles", 0),
            }

        except Exception as e:
            raise RepositoryError(
                f"Failed to get data coverage for {pair} {granularity.value}",
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
