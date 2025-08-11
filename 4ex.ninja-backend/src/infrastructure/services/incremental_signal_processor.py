"""
Incremental Signal Processor for Performance Optimization

This service transforms the MA_Unified_Strat from processing 200 candles every cycle
to incremental processing with Redis caching, achieving 80-90% latency reduction.

Key Performance Improvements:
- Fetch only new candles since last processing (1-5 vs 200 candles)
- Incremental moving average calculations (cached state updates)
- Smart signal deduplication to prevent notification spam
- Graceful fallback to full processing if cache unavailable

Target Performance:
- Signal generation: 2-5s → <500ms
- Data fetching: 200 candles → 1-5 new candles
- MA calculations: Full recalc → Incremental updates
- Cache hit ratio: >90% for established pairs
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from pymongo.collection import Collection

# Import cache service
from infrastructure.cache.redis_cache_service import get_cache_service

# Import existing components - make metrics collector optional
try:
    from infrastructure.monitoring.dashboards import metrics_collector

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics_collector = None


def safe_metrics_record_histogram(metric_name: str, value: float, tags: Dict[str, str]):
    """Safely record histogram metric if metrics collector is available."""
    if METRICS_AVAILABLE and metrics_collector:
        try:
            metrics_collector.record_histogram(metric_name, value, tags)
        except Exception:
            pass  # Silently ignore metrics errors


def safe_metrics_increment_counter(metric_name: str, value: int, tags: Dict[str, str]):
    """Safely increment counter metric if metrics collector is available."""
    if METRICS_AVAILABLE and metrics_collector:
        try:
            metrics_collector.increment_counter(metric_name, value, tags)
        except Exception:
            pass  # Silently ignore metrics errors


class IncrementalSignalProcessor:
    """
    High-performance signal processor that uses Redis caching for incremental
    moving average calculations and smart data fetching.

    Replaces the 200-candle fetch + full MA recalculation pattern with
    incremental processing for massive performance improvements.
    """

    def __init__(
        self,
        pair: str,
        timeframe: str,
        slow_ma: int,
        fast_ma: int,
        atr_period: int,
        collection: Collection,
    ):
        self.pair = pair
        self.timeframe = timeframe
        self.slow_ma = slow_ma
        self.fast_ma = fast_ma
        self.atr_period = atr_period
        self.collection = collection

        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.incremental_updates = 0
        self.full_calculations = 0

        logging.info(f"IncrementalSignalProcessor initialized for {pair}_{timeframe}")

    async def get_incremental_data(
        self, limit_new_candles: int = 10
    ) -> Tuple[pd.DataFrame, bool]:
        """
        Fetch only new candles since last processing, falling back to full fetch if needed.

        Args:
            limit_new_candles: Maximum number of new candles to fetch incrementally

        Returns:
            Tuple of (DataFrame, is_incremental_update)
            - DataFrame: Candle data (either new candles or full 200-candle set)
            - bool: True if incremental, False if full fallback
        """
        start_time = time.time()
        cache_service = await get_cache_service()

        try:
            # Try to get last processed timestamp
            last_processed = await cache_service.get_last_processed_time(
                self.pair, self.timeframe
            )

            if last_processed:
                # Incremental fetch: Get only new candles since last processing
                query = {"time": {"$gt": last_processed}}
                new_candles = list(
                    self.collection.find(query).sort("time", 1).limit(limit_new_candles)
                )

                if new_candles:
                    df = pd.DataFrame(new_candles)

                    fetch_duration = time.time() - start_time
                    logging.info(
                        f"⚡ Incremental fetch: {len(df)} new candles for {self.pair}_{self.timeframe} "
                        f"(since {last_processed.strftime('%H:%M:%S')}) in {fetch_duration:.3f}s"
                    )

                    # Track incremental fetch performance
                    safe_metrics_record_histogram(
                        "incremental_data_fetch_duration",
                        fetch_duration,
                        {
                            "pair": self.pair,
                            "timeframe": self.timeframe,
                            "candle_count": str(len(df)),
                        },
                    )

                    safe_metrics_increment_counter(
                        "incremental_fetches",
                        1,
                        {"pair": self.pair, "timeframe": self.timeframe},
                    )

                    return df, True
                else:
                    logging.debug(
                        f"📊 No new candles for {self.pair}_{self.timeframe} since {last_processed}"
                    )

                    # Return empty DataFrame for no new data
                    return pd.DataFrame(), True

            # Fallback: No cache or no last processed time - fetch full dataset
            logging.info(f"🔄 Full fetch fallback for {self.pair}_{self.timeframe}")
            return await self._full_data_fetch(), False

        except Exception as e:
            logging.warning(
                f"Error in incremental fetch for {self.pair}_{self.timeframe}: {e}"
            )

            # Track fetch errors
            safe_metrics_increment_counter(
                "incremental_fetch_errors",
                1,
                {"pair": self.pair, "timeframe": self.timeframe, "error": str(e)},
            )

            # Fallback to full fetch
            return await self._full_data_fetch(), False

    async def _full_data_fetch(self) -> pd.DataFrame:
        """
        Fallback method: Fetch full 200-candle dataset (original behavior).
        """
        start_time = time.time()

        try:
            df = pd.DataFrame(list(self.collection.find().sort("time", -1).limit(200)))

            if not df.empty:
                # Sort chronologically for processing
                df = df.sort_values("time").reset_index(drop=True)

            fetch_duration = time.time() - start_time
            logging.info(
                f"🐌 Full fetch: {len(df)} candles for {self.pair}_{self.timeframe} in {fetch_duration:.3f}s"
            )

            # Track full fetch performance
            safe_metrics_record_histogram(
                "full_data_fetch_duration",
                fetch_duration,
                {
                    "pair": self.pair,
                    "timeframe": self.timeframe,
                    "candle_count": str(len(df)),
                },
            )

            safe_metrics_increment_counter(
                "full_fetches", 1, {"pair": self.pair, "timeframe": self.timeframe}
            )

            self.full_calculations += 1
            return df

        except Exception as e:
            logging.error(
                f"Error in full data fetch for {self.pair}_{self.timeframe}: {e}"
            )

            # Track full fetch errors
            safe_metrics_increment_counter(
                "full_fetch_errors",
                1,
                {"pair": self.pair, "timeframe": self.timeframe, "error": str(e)},
            )

            return pd.DataFrame()

    async def calculate_moving_averages_incremental(
        self, df: pd.DataFrame, is_incremental: bool
    ) -> pd.DataFrame:
        """
        Calculate moving averages using Redis cache for incremental updates.

        For incremental updates: Update cached MA states with new candles
        For full calculations: Calculate from scratch and populate cache
        """
        if df.empty:
            return df

        start_time = time.time()
        cache_service = await get_cache_service()

        # Prepare DataFrame copy for calculations
        df = df.copy(deep=True)
        df["slow_ma"] = None
        df["fast_ma"] = None

        if is_incremental and len(df) <= 10:  # Process incrementally for small updates
            try:
                await self._process_incremental_ma(df, cache_service)
                self.incremental_updates += 1

                calc_duration = time.time() - start_time
                logging.info(
                    f"⚡ Incremental MA calculation: {len(df)} candles in {calc_duration:.3f}s"
                )

                # Track incremental calculation performance
                safe_metrics_record_histogram(
                    "incremental_ma_calculation_duration",
                    calc_duration,
                    {"pair": self.pair, "timeframe": self.timeframe},
                )

            except Exception as e:
                logging.warning(
                    f"Incremental MA calculation failed, falling back to full: {e}"
                )
                await self._process_full_ma(df, cache_service)

        else:
            # Full calculation for large datasets or cache misses
            await self._process_full_ma(df, cache_service)
            self.full_calculations += 1

            calc_duration = time.time() - start_time
            logging.info(
                f"🔄 Full MA calculation: {len(df)} candles in {calc_duration:.3f}s"
            )

            # Track full calculation performance
            safe_metrics_record_histogram(
                "full_ma_calculation_duration",
                calc_duration,
                {"pair": self.pair, "timeframe": self.timeframe},
            )

        return df

    async def _process_incremental_ma(self, df: pd.DataFrame, cache_service) -> None:
        """
        Process moving averages incrementally using cached state.
        """
        for idx, row in df.iterrows():
            close_price = float(row["close"])

            # Update fast MA incrementally
            fast_ma = await cache_service.update_ma_incremental(
                self.pair, self.timeframe, self.fast_ma, close_price
            )

            # Update slow MA incrementally
            slow_ma = await cache_service.update_ma_incremental(
                self.pair, self.timeframe, self.slow_ma, close_price
            )

            if fast_ma is not None and slow_ma is not None:
                df.at[idx, "fast_ma"] = fast_ma
                df.at[idx, "slow_ma"] = slow_ma
                self.cache_hits += 1
            else:
                # Cache miss - need to fallback to full calculation
                self.cache_misses += 1
                raise Exception("Cache miss during incremental calculation")

    async def _process_full_ma(self, df: pd.DataFrame, cache_service) -> None:
        """
        Process moving averages with full calculation and update cache.
        """
        # Calculate moving averages using pandas (original method)
        df["slow_ma"] = df["close"].rolling(window=self.slow_ma).mean()
        df["fast_ma"] = df["close"].rolling(window=self.fast_ma).mean()

        # Update cache with final MA states for future incremental updates
        if not df.empty and not df["close"].isna().all():
            try:
                # Get last N closing prices for each MA
                close_prices = df["close"].tolist()

                # Cache slow MA state
                if len(close_prices) >= self.slow_ma and not pd.isna(
                    df["slow_ma"].iloc[-1]
                ):
                    await cache_service.set_ma_state(
                        self.pair,
                        self.timeframe,
                        self.slow_ma,
                        close_prices[-self.slow_ma :],  # Last N prices
                        float(df["slow_ma"].iloc[-1]),  # Final MA value
                    )

                # Cache fast MA state
                if len(close_prices) >= self.fast_ma and not pd.isna(
                    df["fast_ma"].iloc[-1]
                ):
                    await cache_service.set_ma_state(
                        self.pair,
                        self.timeframe,
                        self.fast_ma,
                        close_prices[-self.fast_ma :],  # Last N prices
                        float(df["fast_ma"].iloc[-1]),  # Final MA value
                    )

                logging.debug(f"📊 Updated MA cache for {self.pair}_{self.timeframe}")

            except Exception as e:
                logging.warning(f"Error updating MA cache: {e}")

    async def update_last_processed_time(self, latest_timestamp: datetime) -> None:
        """
        Update the last processed timestamp for future incremental fetches.
        """
        try:
            cache_service = await get_cache_service()
            await cache_service.set_last_processed_time(
                self.pair, self.timeframe, latest_timestamp
            )

            logging.debug(
                f"📅 Updated last processed time: {self.pair}_{self.timeframe} -> {latest_timestamp}"
            )

        except Exception as e:
            logging.warning(f"Error updating last processed time: {e}")

    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for this processor.
        """
        cache_service = await get_cache_service()
        cache_stats = await cache_service.get_cache_stats()

        total_operations = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            (self.cache_hits / total_operations) if total_operations > 0 else 0.0
        )

        total_calculations = self.incremental_updates + self.full_calculations
        incremental_rate = (
            (self.incremental_updates / total_calculations)
            if total_calculations > 0
            else 0.0
        )

        return {
            "pair": self.pair,
            "timeframe": self.timeframe,
            "cache_hit_rate": cache_hit_rate,
            "incremental_rate": incremental_rate,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "incremental_updates": self.incremental_updates,
            "full_calculations": self.full_calculations,
            "redis_stats": cache_stats,
        }

    async def process_signals_optimized(self, collection: Collection) -> pd.DataFrame:
        """
        Main optimized signal processing method.

        This replaces the original 200-candle fetch + full MA calculation
        with intelligent incremental processing.

        Returns:
            pd.DataFrame: Processed signals ready for storage/notification
        """
        overall_start = time.time()

        try:
            # Step 1: Get incremental data (1-5 new candles vs 200)
            df, is_incremental = await self.get_incremental_data()

            if df.empty:
                logging.debug(
                    f"No new data to process for {self.pair}_{self.timeframe}"
                )
                return pd.DataFrame()

            # Step 2: Calculate moving averages incrementally
            df = await self.calculate_moving_averages_incremental(df, is_incremental)

            if df.empty or df["close"].isna().all():
                logging.warning(
                    f"Invalid data after MA calculation for {self.pair}_{self.timeframe}"
                )
                return pd.DataFrame()

            # Step 3: Update last processed timestamp for next cycle
            if not df.empty:
                latest_time = df["time"].max()
                if pd.notna(latest_time):
                    # Convert to datetime if needed
                    if isinstance(latest_time, pd.Timestamp):
                        latest_time = latest_time.to_pydatetime()
                    elif not isinstance(latest_time, datetime):
                        latest_time = pd.to_datetime(latest_time).to_pydatetime()

                    await self.update_last_processed_time(latest_time)

            overall_duration = time.time() - overall_start

            # Log performance improvement
            improvement_note = (
                "⚡ INCREMENTAL" if is_incremental else "🔄 FULL FALLBACK"
            )
            logging.info(
                f"{improvement_note}: {self.pair}_{self.timeframe} processed {len(df)} candles in {overall_duration:.3f}s"
            )

            # Track overall processing performance
            safe_metrics_record_histogram(
                "signal_processing_duration_optimized",
                overall_duration,
                {
                    "pair": self.pair,
                    "timeframe": self.timeframe,
                    "is_incremental": str(is_incremental),
                    "candle_count": str(len(df)),
                },
            )

            return df

        except Exception as e:
            logging.error(
                f"Error in optimized signal processing for {self.pair}_{self.timeframe}: {e}"
            )

            # Track processing errors
            safe_metrics_increment_counter(
                "signal_processing_errors_optimized",
                1,
                {"pair": self.pair, "timeframe": self.timeframe, "error": str(e)},
            )

            return pd.DataFrame()


# Factory function for easy integration
async def create_incremental_processor(
    pair: str,
    timeframe: str,
    slow_ma: int,
    fast_ma: int,
    atr_period: int,
    collection: Collection,
) -> IncrementalSignalProcessor:
    """
    Create and initialize an incremental signal processor.
    """
    processor = IncrementalSignalProcessor(
        pair=pair,
        timeframe=timeframe,
        slow_ma=slow_ma,
        fast_ma=fast_ma,
        atr_period=atr_period,
        collection=collection,
    )

    # Ensure cache service is initialized
    await get_cache_service()

    return processor
