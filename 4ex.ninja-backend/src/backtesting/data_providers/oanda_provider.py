"""
OANDA data provider for swing trading backtesting.

This module implements the OANDA API integration focusing on swing trading
requirements with proper error handling and data validation.
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from dataclasses import asdict

# Import existing OANDA API components
import sys
import os

# Add the api and config directories to the path
backend_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
api_path = os.path.join(backend_dir, "api")
config_path = os.path.join(backend_dir, "config")

if api_path not in sys.path:
    sys.path.insert(0, api_path)
if config_path not in sys.path:
    sys.path.insert(0, config_path)

try:
    from oanda_api import OandaAPI  # type: ignore
    from settings import API_KEY, ACCOUNT_ID  # type: ignore

    REAL_OANDA_AVAILABLE = True
except ImportError as e:
    # Fallback for testing or when OANDA API is not available
    class OandaAPI:
        def __init__(self):
            self.account_id = "demo"
            self.client = None

        def get_account_summary(self):
            return {"id": "demo", "balance": "10000"}

        def get_candles(self, *args, **kwargs):
            return []

        def get_current_price(self, *args, **kwargs):
            return 1.1000

    API_KEY = None
    ACCOUNT_ID = "demo"
    REAL_OANDA_AVAILABLE = False

from .base_provider import BaseDataProvider, SwingCandleData, DataQualityMetrics

logger = logging.getLogger(__name__)

# Log the API status after logger is defined
if "REAL_OANDA_AVAILABLE" in locals() and REAL_OANDA_AVAILABLE:
    logger.info("Real OANDA API loaded successfully")
else:
    logger.warning("OANDA API not available, using fallback")

logger = logging.getLogger(__name__)


class OandaLiveProvider(BaseDataProvider):
    """
    OANDA Live data provider for real-time market data.

    This provider focuses on live data streaming for regime monitoring
    and real-time market analysis.
    """

    def __init__(self):
        """Initialize OANDA Live provider with live endpoints."""
        super().__init__(name="oanda_live", priority=1)
        self.api_url = "https://api-fxtrade.oanda.com/v3"  # Live endpoint
        self.real_time = True  # Enable live data streaming
        self.oanda_api = None
        self._connection_retries = 3
        self._retry_delay = 1.0

    async def connect(self) -> bool:
        """Establish connection to OANDA API for live data."""
        try:
            # Initialize OANDA API
            self.oanda_api = OandaAPI()

            # Test connection with account summary
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None, self.oanda_api.get_account_summary
            )

            if summary:
                logger.info("OANDA live provider connected successfully")
                self.is_available = True
                return True
            else:
                logger.error(
                    "OANDA live provider connection failed - no account summary"
                )
                self.is_available = False
                return False

        except Exception as e:
            logger.error(f"OANDA live provider connection failed: {str(e)}")
            self.is_available = False
            return False

    async def get_live_quotes(self, pairs: List[str]) -> Dict[str, dict]:
        """Get real-time market quotes for regime analysis"""
        if not self.is_available or not self.oanda_api:
            logger.error("OANDA live provider not available")
            return {}

        quotes = {}
        try:
            for pair in pairs:
                # Convert pair format from EUR/USD to EUR_USD for OANDA API
                oanda_pair = pair.replace("/", "_")

                loop = asyncio.get_event_loop()
                current_price = await loop.run_in_executor(
                    None, self.oanda_api.get_current_price, oanda_pair
                )

                if current_price:
                    quotes[pair] = {
                        "bid": current_price * 0.9999,  # Approximate bid
                        "ask": current_price,
                        "timestamp": datetime.utcnow(),
                        "pair": pair,
                    }

            logger.info(f"Retrieved live quotes for {len(quotes)} pairs")
            return quotes

        except Exception as e:
            logger.error(f"Failed to get live quotes: {str(e)}")
            return {}

    # Implement required abstract methods (simplified for live provider)
    async def get_candles(
        self,
        pair: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        count: Optional[int] = None,
    ) -> List[SwingCandleData]:
        """Get historical candles (delegated to main OandaProvider)"""
        # For live provider, we don't need historical candles
        return []

    async def get_current_spread(self, pair: str) -> Optional[Decimal]:
        """Get current spread (simplified)"""
        return Decimal("2.0")  # Default spread for live provider

    async def get_average_spread(self, pair: str, days: int = 30) -> Optional[Decimal]:
        """Get average spread (simplified)"""
        return Decimal("2.0")  # Default average spread

    async def validate_data_quality(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> DataQualityMetrics:
        """Validate data quality (simplified for live data)"""
        return DataQualityMetrics(
            missing_candles=0,
            gap_percentage=0.0,
            outlier_count=0,
            spread_consistency=1.0,
            last_update=datetime.utcnow(),
        )

    async def health_check(self) -> bool:
        """Perform health check on live provider"""
        if not self.oanda_api:
            return False

        try:
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None, self.oanda_api.get_account_summary
            )
            return summary is not None
        except:
            return False


class OandaProvider(BaseDataProvider):
    """
    OANDA data provider implementation for swing trading.

    This provider leverages the existing OANDA API integration with focus on
    swing trading timeframes and simplified data validation.
    """

    def __init__(self):
        """Initialize OANDA provider as primary data source."""
        super().__init__(name="oanda", priority=1)
        self.oanda_api = None
        self._connection_retries = 3
        self._retry_delay = 1.0

    async def connect(self) -> bool:
        """
        Establish connection to OANDA API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize OANDA API
            self.oanda_api = OandaAPI()

            # Test connection with account summary
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None, self.oanda_api.get_account_summary
            )

            if summary:
                self.is_available = True
                self.last_health_check = datetime.utcnow()
                logger.info(f"OANDA provider connected successfully")
                return True
            else:
                logger.error("Failed to get OANDA account summary")
                return False

        except Exception as e:
            logger.error(f"OANDA connection failed: {str(e)}")
            self.is_available = False
            return False

    async def get_candles(
        self,
        pair: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        count: Optional[int] = None,
    ) -> List[SwingCandleData]:
        """
        Retrieve historical candle data from OANDA.

        Args:
            pair: Currency pair (e.g., 'EUR_USD')
            timeframe: Timeframe ('4H', 'D', 'W')
            start_time: Start datetime
            end_time: End datetime
            count: Maximum number of candles (optional)

        Returns:
            List of candle data
        """
        if not self.is_available or not self.oanda_api:
            logger.error("OANDA provider not available")
            return []

        # Validate inputs
        if not self.supports_timeframe(timeframe):
            logger.error(f"Unsupported timeframe: {timeframe}")
            return []

        if not self.supports_pair(pair):
            logger.warning(f"Non-major pair requested: {pair}")

        try:
            # Convert timeframe to OANDA format
            oanda_granularity = self._convert_timeframe(timeframe)

            # Format timestamps for OANDA API
            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # Get candles from OANDA API
            # Note: OANDA API doesn't allow 'count' when 'from' and 'to' are specified
            loop = asyncio.get_event_loop()
            raw_candles = await loop.run_in_executor(
                None,
                self.oanda_api.get_candles,
                pair,
                oanda_granularity,
                None,  # Don't use count when we have time range
                start_str,
                end_str,
            )

            if not raw_candles:
                logger.warning(f"No candles returned for {pair} {timeframe}")
                return []

            # Convert to SwingCandleData format
            candles = []
            for raw_candle in raw_candles:
                try:
                    candle = self._convert_candle(raw_candle, pair)
                    if candle:
                        candles.append(candle)
                except Exception as e:
                    logger.warning(f"Failed to convert candle: {str(e)}")
                    continue

            logger.info(f"Retrieved {len(candles)} candles for {pair} {timeframe}")
            return candles

        except Exception as e:
            logger.error(f"Failed to get candles from OANDA: {str(e)}")
            return []

    async def get_current_spread(self, pair: str) -> Optional[Decimal]:
        """
        Get current spread for a currency pair from OANDA.

        Args:
            pair: Currency pair

        Returns:
            Current spread in pips, None if unavailable
        """
        if not self.is_available or not self.oanda_api:
            return None

        try:
            loop = asyncio.get_event_loop()

            # Get current pricing info using existing API method
            current_price = await loop.run_in_executor(
                None, self.oanda_api.get_current_price, pair
            )

            if current_price:
                # For swing trading, use fixed spread assumptions since exact spreads
                # are less critical for longer timeframe strategies
                return await self.get_average_spread(pair)

        except Exception as e:
            logger.error(f"Failed to get current spread for {pair}: {str(e)}")

        return None

    async def get_average_spread(self, pair: str, days: int = 30) -> Optional[Decimal]:
        """
        Get average spread for a currency pair over specified days.

        Args:
            pair: Currency pair
            days: Number of days to calculate average

        Returns:
            Average spread in pips, None if unavailable
        """
        # For simplicity in swing trading, use fixed spread assumptions
        # This is adequate for swing trading where execution precision is less critical

        fixed_spreads = {
            "EUR_USD": Decimal("1.5"),
            "GBP_USD": Decimal("2.0"),
            "USD_JPY": Decimal("1.8"),
            "USD_CHF": Decimal("2.2"),
            "AUD_USD": Decimal("2.5"),
            "USD_CAD": Decimal("2.8"),
            "NZD_USD": Decimal("3.0"),
        }

        return fixed_spreads.get(pair, Decimal("3.0"))  # Default 3 pips for other pairs

    async def validate_data_quality(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> DataQualityMetrics:
        """
        Validate data quality for OANDA data.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Data quality metrics
        """
        try:
            # Get candles for validation
            candles = await self.get_candles(pair, timeframe, start_time, end_time)

            if not candles:
                return DataQualityMetrics(
                    missing_candles=0,
                    gap_percentage=100.0,
                    outlier_count=0,
                    spread_consistency=0.0,
                    last_update=datetime.utcnow(),
                )

            # Calculate expected number of candles
            expected_candles = self._calculate_expected_candles(
                timeframe, start_time, end_time
            )

            # Calculate missing candles
            missing_candles = max(0, expected_candles - len(candles))
            gap_percentage = (
                (missing_candles / expected_candles * 100)
                if expected_candles > 0
                else 0
            )

            # Basic outlier detection (price gaps > 5% between consecutive candles)
            outlier_count = 0
            for i in range(1, len(candles)):
                prev_close = candles[i - 1].close
                curr_open = candles[i].open
                gap_percentage_price = abs(curr_open - prev_close) / prev_close * 100
                if gap_percentage_price > 5.0:  # 5% gap threshold
                    outlier_count += 1

            # Spread consistency (simplified for swing trading)
            spread_consistency = 0.8 if len(candles) > 0 else 0.0  # Fixed assumption

            return DataQualityMetrics(
                missing_candles=missing_candles,
                gap_percentage=gap_percentage,
                outlier_count=outlier_count,
                spread_consistency=spread_consistency,
                last_update=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Data quality validation failed: {str(e)}")
            return DataQualityMetrics(
                missing_candles=0,
                gap_percentage=100.0,
                outlier_count=0,
                spread_consistency=0.0,
                last_update=datetime.utcnow(),
            )

    async def health_check(self) -> bool:
        """
        Perform health check on OANDA provider.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            if not self.oanda_api:
                return False

            # Simple health check - get account summary
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None, self.oanda_api.get_account_summary
            )

            if summary:
                self.is_available = True
                self.last_health_check = datetime.utcnow()
                return True
            else:
                self.is_available = False
                return False

        except Exception as e:
            logger.error(f"OANDA health check failed: {str(e)}")
            self.is_available = False
            return False

    async def get_swap_rate(self, pair: str) -> Optional[Decimal]:
        """
        Get swap rate for overnight positions from OANDA.

        Args:
            pair: Currency pair

        Returns:
            Daily swap rate, None if unavailable
        """
        # For swing trading, use simplified swap rate assumptions
        # In production, this could fetch actual swap rates from OANDA

        # Simplified swap rates (daily, in pips)
        swap_rates = {
            "EUR_USD": Decimal("-0.5"),  # Short EUR typically pays
            "GBP_USD": Decimal("-0.8"),
            "USD_JPY": Decimal("0.3"),  # Long USD typically earns
            "USD_CHF": Decimal("0.2"),
            "AUD_USD": Decimal("-0.6"),
            "USD_CAD": Decimal("0.1"),
            "NZD_USD": Decimal("-0.7"),
        }

        return swap_rates.get(pair, Decimal("0.0"))

    def _convert_timeframe(self, timeframe: str) -> str:
        """
        Convert internal timeframe to OANDA granularity.

        Args:
            timeframe: Internal timeframe ('4H', 'D', 'W')

        Returns:
            OANDA granularity string
        """
        timeframe_mapping = {"4H": "H4", "D": "D", "W": "W"}

        return timeframe_mapping.get(timeframe, "H4")

    def _convert_candle(self, raw_candle: dict, pair: str) -> Optional[SwingCandleData]:
        """
        Convert OANDA candle format to SwingCandleData.

        Args:
            raw_candle: Raw candle data from OANDA
            pair: Currency pair

        Returns:
            SwingCandleData object or None if conversion fails
        """
        try:
            # Extract mid prices from OANDA format
            mid = raw_candle.get("mid", {})

            # Parse timestamp
            timestamp_str = raw_candle.get("time", "")
            # Remove trailing 'Z' and parse
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1]

            # Handle potential microseconds
            if "." in timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.fromisoformat(timestamp_str + ".000")

            # Extract OHLC prices
            open_price = Decimal(str(mid.get("o", "0")))
            high_price = Decimal(str(mid.get("h", "0")))
            low_price = Decimal(str(mid.get("l", "0")))
            close_price = Decimal(str(mid.get("c", "0")))

            # Volume (if available)
            volume = raw_candle.get("volume", None)

            # Use fixed spread assumptions for swing trading (synchronous)
            fixed_spreads = {
                "EUR_USD": Decimal("1.5"),
                "GBP_USD": Decimal("2.0"),
                "USD_JPY": Decimal("1.8"),
                "USD_CHF": Decimal("2.2"),
                "AUD_USD": Decimal("2.5"),
                "USD_CAD": Decimal("2.8"),
                "NZD_USD": Decimal("3.0"),
            }
            spread = fixed_spreads.get(pair, Decimal("3.0"))

            return SwingCandleData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                spread=spread,
            )

        except Exception as e:
            logger.error(f"Failed to convert candle: {str(e)}")
            return None

    def _calculate_expected_candles(
        self, timeframe: str, start_time: datetime, end_time: datetime
    ) -> int:
        """
        Calculate expected number of candles for the given period.

        Args:
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Expected number of candles
        """
        time_diff = end_time - start_time

        if timeframe == "4H":
            # 6 candles per day (4-hour intervals), minus weekends
            days = time_diff.days
            weekdays = days - (days // 7 * 2)  # Rough weekend calculation
            return weekdays * 6
        elif timeframe == "D":
            # 1 candle per day, minus weekends
            days = time_diff.days
            return days - (days // 7 * 2)
        elif timeframe == "W":
            # 1 candle per week
            return time_diff.days // 7

        return 0
