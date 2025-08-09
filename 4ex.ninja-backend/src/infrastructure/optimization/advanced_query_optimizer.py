"""
Advanced Database Query Optimization

This module implements enhanced database optimization strategies including:
- Advanced indexing strategies for common query patterns
- Aggregation pipeline optimizations for crossover data
- Query batching capabilities
- Materialized views for complex analytics

Designed for lean, efficient database operations without breaking changes.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BatchQuery:
    """Represents a query that can be batched."""

    collection: str
    operation: str
    filters: Dict[str, Any]
    options: Dict[str, Any]
    callback_id: str


class AdvancedIndexManager:
    """Manages advanced indexing strategies for optimal query performance."""

    def __init__(self, database):
        """
        Initialize the advanced index manager.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def create_advanced_indexes(self) -> bool:
        """
        Create advanced indexes for optimal query performance.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Advanced signal indexes for crossover analysis
            await self._create_signal_indexes()

            # Market data indexes for time-series analysis
            await self._create_market_data_indexes()

            # Strategy performance indexes
            await self._create_strategy_indexes()

            self.logger.info("Advanced indexes created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create advanced indexes: {e}")
            return False

    async def _create_signal_indexes(self):
        """Create optimized indexes for signal queries."""
        signals_collection = self.database["signals"]

        # Text index for full-text search on signal descriptions/notes
        try:
            await signals_collection.create_index(
                [("pair", "text"), ("signal_type", "text")],
                name="signals_text_search",
                background=True,
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                self.logger.warning(f"Text index creation failed: {e}")

        # Partial indexes for active signals only (reduces index size)
        await signals_collection.create_index(
            [("pair", 1), ("created_at", -1)],
            partialFilterExpression={"status": {"$in": ["ACTIVE", "FILLED"]}},
            name="active_signals_pair_time",
            background=True,
        )

        # Sparse index for stop_loss/take_profit (only when values exist)
        await signals_collection.create_index(
            [("stop_loss", 1)],
            sparse=True,
            name="signals_stop_loss_sparse",
            background=True,
        )

        await signals_collection.create_index(
            [("take_profit", 1)],
            sparse=True,
            name="signals_take_profit_sparse",
            background=True,
        )

        # Compound index for crossover analysis
        await signals_collection.create_index(
            [("pair", 1), ("signal_type", 1), ("created_at", -1), ("status", 1)],
            name="crossover_analysis_compound",
            background=True,
        )

    async def _create_market_data_indexes(self):
        """Create optimized indexes for market data queries."""
        market_data_collection = self.database["market_data"]

        # Partial index for recent data (last 30 days) for faster queries
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        await market_data_collection.create_index(
            [("pair", 1), ("timestamp", -1)],
            partialFilterExpression={"timestamp": {"$gte": thirty_days_ago}},
            name="recent_market_data",
            background=True,
        )

        # Index for OHLC analysis with granularity
        await market_data_collection.create_index(
            [("pair", 1), ("timeframe", 1), ("timestamp", -1)],
            name="ohlc_analysis_optimized",
            background=True,
        )

        # Index for volume analysis
        await market_data_collection.create_index(
            [("volume", -1)], sparse=True, name="volume_analysis", background=True
        )

    async def _create_strategy_indexes(self):
        """Create optimized indexes for strategy queries."""
        strategies_collection = self.database["strategies"]

        # Compound index for strategy performance queries
        await strategies_collection.create_index(
            [("strategy_type", 1), ("is_active", 1), ("created_at", -1)],
            name="strategy_performance_compound",
            background=True,
        )

        # Text index for strategy search
        try:
            await strategies_collection.create_index(
                [("name", "text"), ("description", "text")],
                name="strategy_text_search",
                background=True,
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                self.logger.warning(f"Strategy text index creation failed: {e}")


class CrossoverAggregationOptimizer:
    """Optimizes aggregation pipelines specifically for crossover data analysis."""

    def __init__(self, database):
        """
        Initialize the aggregation optimizer.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def get_crossover_signals_optimized(
        self, pairs: List[str], timeframe: str = "1h", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get crossover signals using optimized aggregation pipeline.

        Args:
            pairs: List of currency pairs
            timeframe: Timeframe for analysis
            limit: Maximum number of results

        Returns:
            List of crossover signals with analytics
        """
        try:
            signals_collection = self.database["signals"]

            # Optimized aggregation pipeline
            pipeline = [
                # Stage 1: Match active signals for specified pairs
                {
                    "$match": {
                        "pair": {"$in": pairs},
                        "status": {"$in": ["ACTIVE", "FILLED"]},
                        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)},
                    }
                },
                # Stage 2: Add computed fields for analysis
                {
                    "$addFields": {
                        "signal_score": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {"$eq": ["$signal_type", "BUY"]},
                                        "then": 1,
                                    },
                                    {
                                        "case": {"$eq": ["$signal_type", "SELL"]},
                                        "then": -1,
                                    },
                                ],
                                "default": 0,
                            }
                        },
                        "risk_reward_ratio": {
                            "$cond": {
                                "if": {
                                    "$and": [
                                        {"$ne": ["$stop_loss", None]},
                                        {"$ne": ["$take_profit", None]},
                                        {"$ne": ["$entry_price", None]},
                                    ]
                                },
                                "then": {
                                    "$divide": [
                                        {
                                            "$abs": {
                                                "$subtract": [
                                                    "$take_profit",
                                                    "$entry_price",
                                                ]
                                            }
                                        },
                                        {
                                            "$abs": {
                                                "$subtract": [
                                                    "$entry_price",
                                                    "$stop_loss",
                                                ]
                                            }
                                        },
                                    ]
                                },
                                "else": None,
                            }
                        },
                    }
                },
                # Stage 3: Group by pair for crossover analysis
                {
                    "$group": {
                        "_id": "$pair",
                        "signals": {"$push": "$$ROOT"},
                        "buy_signals": {
                            "$sum": {"$cond": [{"$eq": ["$signal_type", "BUY"]}, 1, 0]}
                        },
                        "sell_signals": {
                            "$sum": {"$cond": [{"$eq": ["$signal_type", "SELL"]}, 1, 0]}
                        },
                        "avg_risk_reward": {"$avg": "$risk_reward_ratio"},
                        "latest_signal": {"$max": "$created_at"},
                        "total_signals": {"$sum": 1},
                    }
                },
                # Stage 4: Add crossover strength calculation
                {
                    "$addFields": {
                        "crossover_strength": {
                            "$cond": {
                                "if": {"$eq": ["$total_signals", 0]},
                                "then": 0,
                                "else": {
                                    "$divide": [
                                        {
                                            "$abs": {
                                                "$subtract": [
                                                    "$buy_signals",
                                                    "$sell_signals",
                                                ]
                                            }
                                        },
                                        "$total_signals",
                                    ]
                                },
                            }
                        },
                        "signal_bias": {
                            "$cond": [
                                {"$gt": ["$buy_signals", "$sell_signals"]},
                                "BULLISH",
                                {"$gt": ["$sell_signals", "$buy_signals"]},
                                "BEARISH",
                                "NEUTRAL",
                            ]
                        },
                    }
                },
                # Stage 5: Sort by crossover strength and limit
                {"$sort": {"crossover_strength": -1, "latest_signal": -1}},
                {"$limit": limit},
            ]

            # Execute optimized aggregation
            cursor = signals_collection.aggregate(pipeline, allowDiskUse=True)
            results = await cursor.to_list(length=None)

            self.logger.info(
                f"Crossover analysis completed for {len(pairs)} pairs, found {len(results)} results"
            )
            return results

        except Exception as e:
            self.logger.error(f"Crossover aggregation failed: {e}")
            return []

    async def get_market_trend_analysis(
        self, pairs: List[str], days: int = 7
    ) -> Dict[str, Any]:
        """
        Get market trend analysis using optimized aggregation.

        Args:
            pairs: List of currency pairs
            days: Number of days to analyze

        Returns:
            Market trend analysis data
        """
        try:
            market_data_collection = self.database["market_data"]
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            pipeline = [
                # Stage 1: Match recent data for specified pairs
                {
                    "$match": {
                        "pair": {"$in": pairs},
                        "timestamp": {"$gte": cutoff_date},
                    }
                },
                # Stage 2: Add technical indicators
                {
                    "$addFields": {
                        "price_change": {"$subtract": ["$close", "$open"]},
                        "price_change_pct": {
                            "$multiply": [
                                {
                                    "$divide": [
                                        {"$subtract": ["$close", "$open"]},
                                        "$open",
                                    ]
                                },
                                100,
                            ]
                        },
                        "day_range": {"$subtract": ["$high", "$low"]},
                        "is_green": {"$gt": ["$close", "$open"]},
                    }
                },
                # Stage 3: Group by pair for trend analysis
                {
                    "$group": {
                        "_id": "$pair",
                        "candle_count": {"$sum": 1},
                        "green_candles": {"$sum": {"$cond": ["$is_green", 1, 0]}},
                        "avg_price_change": {"$avg": "$price_change"},
                        "avg_price_change_pct": {"$avg": "$price_change_pct"},
                        "total_volume": {"$sum": "$volume"},
                        "avg_range": {"$avg": "$day_range"},
                        "latest_close": {"$last": "$close"},
                        "first_open": {"$first": "$open"},
                    }
                },
                # Stage 4: Calculate trend indicators
                {
                    "$addFields": {
                        "bullish_ratio": {
                            "$divide": ["$green_candles", "$candle_count"]
                        },
                        "overall_change_pct": {
                            "$multiply": [
                                {
                                    "$divide": [
                                        {"$subtract": ["$latest_close", "$first_open"]},
                                        "$first_open",
                                    ]
                                },
                                100,
                            ]
                        },
                        "trend_strength": {
                            "$abs": {"$divide": ["$avg_price_change", "$avg_range"]}
                        },
                    }
                },
                # Stage 5: Classify trends
                {
                    "$addFields": {
                        "trend_direction": {
                            "$cond": [
                                {"$gt": ["$overall_change_pct", 1]},
                                "STRONG_BULLISH",
                                {"$gt": ["$overall_change_pct", 0.2]},
                                "BULLISH",
                                {"$lt": ["$overall_change_pct", -1]},
                                "STRONG_BEARISH",
                                {"$lt": ["$overall_change_pct", -0.2]},
                                "BEARISH",
                                "SIDEWAYS",
                            ]
                        }
                    }
                },
                {"$sort": {"trend_strength": -1}},
            ]

            cursor = market_data_collection.aggregate(pipeline, allowDiskUse=True)
            results = await cursor.to_list(length=None)

            # Calculate summary statistics
            summary = {
                "analysis_date": datetime.utcnow().isoformat(),
                "pairs_analyzed": len(results),
                "bullish_pairs": len(
                    [r for r in results if "BULLISH" in r.get("trend_direction", "")]
                ),
                "bearish_pairs": len(
                    [r for r in results if "BEARISH" in r.get("trend_direction", "")]
                ),
                "sideways_pairs": len(
                    [r for r in results if r.get("trend_direction") == "SIDEWAYS"]
                ),
                "results": results,
            }

            self.logger.info(f"Market trend analysis completed for {len(pairs)} pairs")
            return summary

        except Exception as e:
            self.logger.error(f"Market trend analysis failed: {e}")
            return {"error": str(e), "results": []}


class QueryBatchProcessor:
    """Handles batching of database queries for improved performance."""

    def __init__(self, database, batch_size: int = 10, batch_timeout: float = 0.1):
        """
        Initialize the query batch processor.

        Args:
            database: MongoDB database instance
            batch_size: Maximum number of queries per batch
            batch_timeout: Timeout in seconds before processing partial batch
        """
        self.database = database
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Batch storage
        self.pending_batches: Dict[str, List[BatchQuery]] = defaultdict(list)
        self.batch_results: Dict[str, Any] = {}
        self.batch_timers: Dict[str, asyncio.Task] = {}

    async def add_query_to_batch(
        self,
        collection: str,
        operation: str,
        filters: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        callback_id: Optional[str] = None,
    ) -> str:
        """
        Add a query to the batch for processing.

        Args:
            collection: Collection name
            operation: Operation type (find, count, etc.)
            filters: Query filters
            options: Query options (limit, sort, etc.)
            callback_id: Unique identifier for result retrieval

        Returns:
            str: Batch callback ID for result retrieval
        """
        if callback_id is None:
            callback_id = f"{collection}_{operation}_{datetime.utcnow().timestamp()}"

        if options is None:
            options = {}

        batch_query = BatchQuery(
            collection=collection,
            operation=operation,
            filters=filters,
            options=options,
            callback_id=callback_id,
        )

        # Group by collection and operation for efficient batching
        batch_key = f"{collection}_{operation}"
        self.pending_batches[batch_key].append(batch_query)

        # Process batch if it reaches batch_size
        if len(self.pending_batches[batch_key]) >= self.batch_size:
            await self._process_batch(batch_key)
        else:
            # Set timer for batch timeout
            if batch_key not in self.batch_timers:
                self.batch_timers[batch_key] = asyncio.create_task(
                    self._batch_timeout_handler(batch_key)
                )

        return callback_id

    async def get_batch_result(
        self, callback_id: str, timeout: float = 5.0
    ) -> Optional[Any]:
        """
        Get the result of a batched query.

        Args:
            callback_id: Batch callback ID
            timeout: Timeout in seconds

        Returns:
            Query result or None if not found/timeout
        """
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if callback_id in self.batch_results:
                result = self.batch_results.pop(callback_id)
                return result

            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting

        self.logger.warning(f"Batch result timeout for callback_id: {callback_id}")
        return None

    async def _batch_timeout_handler(self, batch_key: str):
        """Handle batch timeout and process partial batch."""
        try:
            await asyncio.sleep(self.batch_timeout)
            if batch_key in self.pending_batches and self.pending_batches[batch_key]:
                await self._process_batch(batch_key)
        except asyncio.CancelledError:
            pass  # Timer was cancelled, batch was processed manually

    async def _process_batch(self, batch_key: str):
        """Process a batch of queries efficiently."""
        try:
            batch_queries = self.pending_batches[batch_key]
            if not batch_queries:
                return

            # Cancel timer if exists
            if batch_key in self.batch_timers:
                self.batch_timers[batch_key].cancel()
                del self.batch_timers[batch_key]

            collection_name = batch_queries[0].collection
            operation = batch_queries[0].operation
            collection = self.database[collection_name]

            if operation == "find":
                await self._process_find_batch(collection, batch_queries)
            elif operation == "count":
                await self._process_count_batch(collection, batch_queries)
            elif operation == "aggregate":
                await self._process_aggregate_batch(collection, batch_queries)

            # Clear processed batch
            self.pending_batches[batch_key] = []

            self.logger.debug(
                f"Processed batch {batch_key} with {len(batch_queries)} queries"
            )

        except Exception as e:
            self.logger.error(f"Batch processing failed for {batch_key}: {e}")
            # Store error results
            for query in batch_queries:
                self.batch_results[query.callback_id] = {"error": str(e)}

    async def _process_find_batch(self, collection, batch_queries: List[BatchQuery]):
        """Process a batch of find queries using $or aggregation."""
        try:
            # Build aggregation pipeline for multiple find queries
            or_conditions = []
            query_map = {}

            for i, query in enumerate(batch_queries):
                # Add index to each condition to map results back
                condition = query.filters.copy()
                condition["_batch_index"] = i
                or_conditions.append(condition)
                query_map[i] = query.callback_id

            # Execute aggregation with $or
            pipeline = [
                {"$addFields": {"_batch_index": {"$literal": -1}}},
                {"$match": {"$or": or_conditions}},
                {"$group": {"_id": "$_batch_index", "documents": {"$push": "$$ROOT"}}},
            ]

            cursor = collection.aggregate(pipeline)
            async for result in cursor:
                batch_index = result["_id"]
                if batch_index in query_map:
                    callback_id = query_map[batch_index]

                    # Apply individual query options (limit, sort)
                    documents = result["documents"]
                    query = batch_queries[batch_index]

                    # Apply sort if specified
                    if "sort" in query.options:
                        sort_field, sort_order = list(query.options["sort"].items())[0]
                        documents.sort(
                            key=lambda x: x.get(sort_field, 0),
                            reverse=(sort_order == -1),
                        )

                    # Apply limit if specified
                    if "limit" in query.options:
                        documents = documents[: query.options["limit"]]

                    self.batch_results[callback_id] = documents

        except Exception as e:
            self.logger.error(f"Find batch processing failed: {e}")
            # Store error for all queries in batch
            for query in batch_queries:
                self.batch_results[query.callback_id] = {"error": str(e)}

    async def _process_count_batch(self, collection, batch_queries: List[BatchQuery]):
        """Process a batch of count queries."""
        try:
            # Use aggregation to count multiple conditions
            facet_stages = {}

            for i, query in enumerate(batch_queries):
                stage_name = f"count_{i}"
                facet_stages[stage_name] = [
                    {"$match": query.filters},
                    {"$count": "total"},
                ]

            pipeline = [{"$facet": facet_stages}]

            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)

            if result:
                facet_result = result[0]
                for i, query in enumerate(batch_queries):
                    stage_name = f"count_{i}"
                    count_result = facet_result.get(stage_name, [])
                    count = count_result[0]["total"] if count_result else 0
                    self.batch_results[query.callback_id] = count

        except Exception as e:
            self.logger.error(f"Count batch processing failed: {e}")
            for query in batch_queries:
                self.batch_results[query.callback_id] = {"error": str(e)}

    async def _process_aggregate_batch(
        self, collection, batch_queries: List[BatchQuery]
    ):
        """Process a batch of aggregation queries using $facet."""
        try:
            facet_stages = {}

            for i, query in enumerate(batch_queries):
                stage_name = f"agg_{i}"
                # Assume filters contain the aggregation pipeline
                pipeline = query.filters.get("pipeline", [])
                facet_stages[stage_name] = pipeline

            main_pipeline = [{"$facet": facet_stages}]

            cursor = collection.aggregate(main_pipeline)
            result = await cursor.to_list(length=1)

            if result:
                facet_result = result[0]
                for i, query in enumerate(batch_queries):
                    stage_name = f"agg_{i}"
                    agg_result = facet_result.get(stage_name, [])
                    self.batch_results[query.callback_id] = agg_result

        except Exception as e:
            self.logger.error(f"Aggregation batch processing failed: {e}")
            for query in batch_queries:
                self.batch_results[query.callback_id] = {"error": str(e)}


class MaterializedViewManager:
    """Manages materialized views for complex analytics queries."""

    def __init__(self, database):
        """
        Initialize the materialized view manager.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.views = {}

    async def create_crossover_analytics_view(self) -> bool:
        """
        Create materialized view for crossover analytics.

        Returns:
            bool: True if successful
        """
        try:
            # Create crossover analytics collection
            view_name = "crossover_analytics_view"

            # Check if view already exists
            collections = await self.database.list_collection_names()
            if view_name in collections:
                await self.database[view_name].drop()
                self.logger.info(f"Dropped existing view: {view_name}")

            # Create aggregation pipeline for the view
            pipeline = [
                # Stage 1: Match recent signals
                {
                    "$match": {
                        "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)},
                        "status": {"$in": ["ACTIVE", "FILLED", "CANCELLED"]},
                    }
                },
                # Stage 2: Add computed fields
                {
                    "$addFields": {
                        "day_of_week": {"$dayOfWeek": "$created_at"},
                        "hour_of_day": {"$hour": "$created_at"},
                        "is_profitable": {
                            "$cond": {
                                "if": {
                                    "$and": [
                                        {"$ne": ["$exit_price", None]},
                                        {"$ne": ["$entry_price", None]},
                                    ]
                                },
                                "then": {
                                    "$cond": [
                                        {"$eq": ["$signal_type", "BUY"]},
                                        {"$gt": ["$exit_price", "$entry_price"]},
                                        {"$lt": ["$exit_price", "$entry_price"]},
                                    ]
                                },
                                "else": None,
                            }
                        },
                    }
                },
                # Stage 3: Group by pair and day for analytics
                {
                    "$group": {
                        "_id": {
                            "pair": "$pair",
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$created_at",
                                }
                            },
                        },
                        "total_signals": {"$sum": 1},
                        "buy_signals": {
                            "$sum": {"$cond": [{"$eq": ["$signal_type", "BUY"]}, 1, 0]}
                        },
                        "sell_signals": {
                            "$sum": {"$cond": [{"$eq": ["$signal_type", "SELL"]}, 1, 0]}
                        },
                        "profitable_signals": {
                            "$sum": {"$cond": ["$is_profitable", 1, 0]}
                        },
                        "avg_entry_price": {"$avg": "$entry_price"},
                        "signals_by_hour": {
                            "$push": {
                                "hour": "$hour_of_day",
                                "signal_type": "$signal_type",
                                "is_profitable": "$is_profitable",
                            }
                        },
                        "first_signal": {"$min": "$created_at"},
                        "last_signal": {"$max": "$created_at"},
                    }
                },
                # Stage 4: Calculate analytics
                {
                    "$addFields": {
                        "profit_rate": {
                            "$cond": {
                                "if": {"$gt": ["$total_signals", 0]},
                                "then": {
                                    "$divide": ["$profitable_signals", "$total_signals"]
                                },
                                "else": 0,
                            }
                        },
                        "signal_balance": {
                            "$subtract": ["$buy_signals", "$sell_signals"]
                        },
                        "signal_diversity": {
                            "$cond": {
                                "if": {"$gt": ["$total_signals", 1]},
                                "then": {
                                    "$divide": [
                                        {"$min": ["$buy_signals", "$sell_signals"]},
                                        "$total_signals",
                                    ]
                                },
                                "else": 0,
                            }
                        },
                    }
                },
                # Stage 5: Add metadata
                {
                    "$addFields": {
                        "view_created": {"$literal": datetime.utcnow()},
                        "pair": "$_id.pair",
                        "date": "$_id.date",
                    }
                },
                # Stage 6: Output to collection
                {"$out": view_name},
            ]

            # Execute aggregation to create materialized view
            signals_collection = self.database["signals"]
            await signals_collection.aggregate(pipeline).to_list(length=None)

            # Create index on the materialized view
            view_collection = self.database[view_name]
            await view_collection.create_index(
                [("pair", 1), ("date", -1)], background=True
            )
            await view_collection.create_index([("profit_rate", -1)], background=True)
            await view_collection.create_index([("total_signals", -1)], background=True)

            self.views[view_name] = {
                "created": datetime.utcnow(),
                "pipeline": pipeline,
                "refresh_interval_hours": 6,
            }

            self.logger.info(f"Created materialized view: {view_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create crossover analytics view: {e}")
            return False

    async def create_market_performance_view(self) -> bool:
        """
        Create materialized view for market performance analytics.

        Returns:
            bool: True if successful
        """
        try:
            view_name = "market_performance_view"

            # Check if view already exists
            collections = await self.database.list_collection_names()
            if view_name in collections:
                await self.database[view_name].drop()
                self.logger.info(f"Dropped existing view: {view_name}")

            pipeline = [
                # Stage 1: Match recent market data
                {
                    "$match": {
                        "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
                    }
                },
                # Stage 2: Add technical indicators
                {
                    "$addFields": {
                        "price_change": {"$subtract": ["$close", "$open"]},
                        "price_change_pct": {
                            "$multiply": [
                                {
                                    "$divide": [
                                        {"$subtract": ["$close", "$open"]},
                                        "$open",
                                    ]
                                },
                                100,
                            ]
                        },
                        "volatility": {
                            "$divide": [{"$subtract": ["$high", "$low"]}, "$open"]
                        },
                        "date": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp",
                            }
                        },
                    }
                },
                # Stage 3: Group by pair and date
                {
                    "$group": {
                        "_id": {"pair": "$pair", "date": "$date"},
                        "open_price": {"$first": "$open"},
                        "close_price": {"$last": "$close"},
                        "high_price": {"$max": "$high"},
                        "low_price": {"$min": "$low"},
                        "total_volume": {"$sum": "$volume"},
                        "candle_count": {"$sum": 1},
                        "avg_volatility": {"$avg": "$volatility"},
                        "total_price_change": {"$sum": "$price_change"},
                        "avg_price_change_pct": {"$avg": "$price_change_pct"},
                    }
                },
                # Stage 4: Calculate daily performance metrics
                {
                    "$addFields": {
                        "daily_return_pct": {
                            "$multiply": [
                                {
                                    "$divide": [
                                        {"$subtract": ["$close_price", "$open_price"]},
                                        "$open_price",
                                    ]
                                },
                                100,
                            ]
                        },
                        "intraday_range_pct": {
                            "$multiply": [
                                {
                                    "$divide": [
                                        {"$subtract": ["$high_price", "$low_price"]},
                                        "$open_price",
                                    ]
                                },
                                100,
                            ]
                        },
                        "pair": "$_id.pair",
                        "date": "$_id.date",
                        "view_created": {"$literal": datetime.utcnow()},
                    }
                },
                {"$out": view_name},
            ]

            # Execute aggregation to create materialized view
            market_data_collection = self.database["market_data"]
            await market_data_collection.aggregate(pipeline).to_list(length=None)

            # Create indexes on the materialized view
            view_collection = self.database[view_name]
            await view_collection.create_index(
                [("pair", 1), ("date", -1)], background=True
            )
            await view_collection.create_index(
                [("daily_return_pct", -1)], background=True
            )
            await view_collection.create_index(
                [("avg_volatility", -1)], background=True
            )

            self.views[view_name] = {
                "created": datetime.utcnow(),
                "pipeline": pipeline,
                "refresh_interval_hours": 4,
            }

            self.logger.info(f"Created materialized view: {view_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create market performance view: {e}")
            return False

    async def refresh_views(self) -> Dict[str, bool]:
        """
        Refresh all materialized views that need updating.

        Returns:
            Dict with view names and refresh status
        """
        results = {}

        for view_name, view_info in self.views.items():
            try:
                # Check if view needs refresh
                created_time = view_info["created"]
                refresh_interval = timedelta(hours=view_info["refresh_interval_hours"])

                if datetime.utcnow() - created_time >= refresh_interval:
                    if view_name == "crossover_analytics_view":
                        results[view_name] = (
                            await self.create_crossover_analytics_view()
                        )
                    elif view_name == "market_performance_view":
                        results[view_name] = await self.create_market_performance_view()
                    else:
                        results[view_name] = False
                else:
                    results[view_name] = True  # No refresh needed

            except Exception as e:
                self.logger.error(f"Failed to refresh view {view_name}: {e}")
                results[view_name] = False

        return results

    async def query_crossover_analytics(
        self,
        pairs: Optional[List[str]] = None,
        min_profit_rate: float = 0.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query the crossover analytics materialized view.

        Args:
            pairs: Filter by currency pairs
            min_profit_rate: Minimum profit rate filter
            limit: Maximum results

        Returns:
            Analytics results
        """
        try:
            view_collection = self.database["crossover_analytics_view"]

            # Build query
            query: Dict[str, Any] = {"profit_rate": {"$gte": min_profit_rate}}
            if pairs:
                query["pair"] = {"$in": pairs}

            # Execute query with sorting
            cursor = (
                view_collection.find(query)
                .sort([("profit_rate", -1), ("total_signals", -1)])
                .limit(limit)
            )

            results = await cursor.to_list(length=None)
            self.logger.info(
                f"Queried crossover analytics view, found {len(results)} results"
            )
            return results

        except Exception as e:
            self.logger.error(f"Failed to query crossover analytics view: {e}")
            return []

    async def query_market_performance(
        self,
        pairs: Optional[List[str]] = None,
        min_volatility: float = 0.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query the market performance materialized view.

        Args:
            pairs: Filter by currency pairs
            min_volatility: Minimum volatility filter
            limit: Maximum results

        Returns:
            Performance results
        """
        try:
            view_collection = self.database["market_performance_view"]

            # Build query
            query: Dict[str, Any] = {"avg_volatility": {"$gte": min_volatility}}
            if pairs:
                query["pair"] = {"$in": pairs}

            # Execute query with sorting
            cursor = (
                view_collection.find(query)
                .sort([("daily_return_pct", -1), ("avg_volatility", -1)])
                .limit(limit)
            )

            results = await cursor.to_list(length=None)
            self.logger.info(
                f"Queried market performance view, found {len(results)} results"
            )
            return results

        except Exception as e:
            self.logger.error(f"Failed to query market performance view: {e}")
            return []


# Global optimization manager instance
_optimization_manager = None


def get_optimization_manager(database):
    """Get or create the global optimization manager."""
    global _optimization_manager
    if _optimization_manager is None:
        _optimization_manager = DatabaseOptimizationManager(database)
    return _optimization_manager


class DatabaseOptimizationManager:
    """Central manager for all database optimization features."""

    def __init__(self, database):
        """
        Initialize the database optimization manager.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize optimization components
        self.index_manager = AdvancedIndexManager(database)
        self.aggregation_optimizer = CrossoverAggregationOptimizer(database)
        self.batch_processor = QueryBatchProcessor(database)
        self.view_manager = MaterializedViewManager(database)

    async def initialize_optimizations(self) -> bool:
        """
        Initialize all database optimizations.

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info("Initializing database optimizations...")

            # Create advanced indexes
            if not await self.index_manager.create_advanced_indexes():
                self.logger.warning("Advanced index creation failed")
                return False

            # Create materialized views
            if not await self.view_manager.create_crossover_analytics_view():
                self.logger.warning("Crossover analytics view creation failed")

            if not await self.view_manager.create_market_performance_view():
                self.logger.warning("Market performance view creation failed")

            self.logger.info("Database optimizations initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize optimizations: {e}")
            return False

    async def get_optimization_status(self) -> Dict[str, Any]:
        """
        Get the status of all optimizations.

        Returns:
            Status information
        """
        try:
            collections = await self.database.list_collection_names()

            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "indexes": {
                    "advanced_indexes_present": True,  # Would need to check specific indexes
                },
                "materialized_views": {
                    "crossover_analytics": "crossover_analytics_view" in collections,
                    "market_performance": "market_performance_view" in collections,
                },
                "batch_processor": {
                    "pending_batches": len(self.batch_processor.pending_batches),
                    "active_timers": len(self.batch_processor.batch_timers),
                },
                "views_info": self.view_manager.views,
            }

            return status

        except Exception as e:
            self.logger.error(f"Failed to get optimization status: {e}")
            return {"error": str(e)}
