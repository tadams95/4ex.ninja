"""
Alpha Vantage data provider for swing trading validation.

This module implements the Alpha Vantage API integration as a secondary
data provider for validation purposes in swing trading backtesting.
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import json

from .base_provider import BaseDataProvider, SwingCandleData, DataQualityMetrics

logger = logging.getLogger(__name__)


class AlphaVantageProvider(BaseDataProvider):
    """
    Alpha Vantage data provider implementation for validation purposes.

    This provider serves as a secondary data source for validating OANDA data
    in swing trading scenarios. It focuses on daily and weekly timeframes.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage provider as secondary data source."""
        super().__init__(name="alpha_vantage", priority=2)
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self._session = None
        self._rate_limit_delay = 12.0  # Alpha Vantage free tier: 5 calls/minute

    async def connect(self) -> bool:
        """
        Establish connection to Alpha Vantage API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.warning("Alpha Vantage API key not provided - using demo mode")
                self.is_available = True  # Allow demo mode for validation
                return True

            # Create aiohttp session
            self._session = aiohttp.ClientSession()

            # Test connection with a simple API call
            test_url = f"{self.base_url}?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=EUR&apikey={self.api_key}"

            async with self._session.get(test_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "Error Message" not in data and "Note" not in data:
                        self.is_available = True
                        self.last_health_check = datetime.utcnow()
                        logger.info("Alpha Vantage provider connected successfully")
                        return True
                    else:
                        logger.error(f"Alpha Vantage API error: {data}")
                        return False
                else:
                    logger.error(
                        f"Alpha Vantage connection failed: HTTP {response.status}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Alpha Vantage connection failed: {str(e)}")
            self.is_available = False
            if self._session:
                await self._session.close()
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
        Retrieve historical candle data from Alpha Vantage.

        Args:
            pair: Currency pair (e.g., 'EUR_USD')
            timeframe: Timeframe ('D', 'W' - 4H not supported)
            start_time: Start datetime
            end_time: End datetime
            count: Maximum number of candles (optional)

        Returns:
            List of candle data
        """
        if not self.is_available:
            logger.error("Alpha Vantage provider not available")
            return []

        # Alpha Vantage only supports daily and weekly for FX
        if timeframe == "4H":
            logger.warning("Alpha Vantage doesn't support 4H timeframe, skipping")
            return []

        if not self.supports_pair(pair):
            logger.warning(f"Non-major pair requested: {pair}")

        try:
            # Convert pair format (EUR_USD -> EURUSD)
            av_pair = pair.replace("_", "")

            # Determine Alpha Vantage function
            if timeframe == "D":
                function = "FX_DAILY"
            elif timeframe == "W":
                function = "FX_WEEKLY"
            else:
                logger.error(f"Unsupported timeframe for Alpha Vantage: {timeframe}")
                return []

            # Handle demo mode
            if not self.api_key:
                return self._get_demo_candles(pair, timeframe, start_time, end_time)

            # Ensure session exists
            if not self._session:
                await self.connect()
                if not self._session:
                    logger.error("Failed to establish Alpha Vantage session")
                    return []

            # Build API URL
            url = f"{self.base_url}?function={function}&from_symbol={av_pair[:3]}&to_symbol={av_pair[3:]}&apikey={self.api_key}"

            # Rate limiting
            await asyncio.sleep(self._rate_limit_delay)

            # Make API request
            async with self._session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Alpha Vantage API error: HTTP {response.status}")
                    return []

                data = await response.json()

                # Check for API errors
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return []

                if "Note" in data:
                    logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                    return []

                # Extract time series data
                time_series_key = self._get_time_series_key(data)
                if not time_series_key or time_series_key not in data:
                    logger.error("No time series data found in Alpha Vantage response")
                    return []

                time_series = data[time_series_key]

                # Convert to SwingCandleData
                candles = []
                for date_str, candle_data in time_series.items():
                    try:
                        candle = self._convert_av_candle(date_str, candle_data, pair)
                        if candle and start_time <= candle.timestamp <= end_time:
                            candles.append(candle)

                        # Apply count limit
                        if count and len(candles) >= count:
                            break

                    except Exception as e:
                        logger.warning(
                            f"Failed to convert Alpha Vantage candle: {str(e)}"
                        )
                        continue

                # Sort by timestamp (oldest first)
                candles.sort(key=lambda x: x.timestamp)

                logger.info(
                    f"Retrieved {len(candles)} candles from Alpha Vantage for {pair} {timeframe}"
                )
                return candles

        except Exception as e:
            logger.error(f"Failed to get candles from Alpha Vantage: {str(e)}")
            return []

    async def get_current_spread(self, pair: str) -> Optional[Decimal]:
        """
        Get current spread for a currency pair.

        Note: Alpha Vantage doesn't provide spread data, so we use fixed assumptions.

        Args:
            pair: Currency pair

        Returns:
            Fixed spread assumption in pips
        """
        return await self.get_average_spread(pair)

    async def get_average_spread(self, pair: str, days: int = 30) -> Optional[Decimal]:
        """
        Get average spread for a currency pair (fixed assumptions).

        Args:
            pair: Currency pair
            days: Number of days (ignored for fixed spreads)

        Returns:
            Fixed spread assumption in pips
        """
        # Alpha Vantage doesn't provide spread data
        # Use slightly higher spreads than OANDA for validation
        fixed_spreads = {
            "EUR_USD": Decimal("2.0"),
            "GBP_USD": Decimal("2.5"),
            "USD_JPY": Decimal("2.3"),
            "USD_CHF": Decimal("2.7"),
            "AUD_USD": Decimal("3.0"),
            "USD_CAD": Decimal("3.3"),
            "NZD_USD": Decimal("3.5"),
        }

        return fixed_spreads.get(pair, Decimal("4.0"))

    async def validate_data_quality(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> DataQualityMetrics:
        """
        Validate data quality for Alpha Vantage data.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            Data quality metrics
        """
        try:
            candles = await self.get_candles(pair, timeframe, start_time, end_time)

            if not candles:
                return DataQualityMetrics(
                    missing_candles=0,
                    gap_percentage=100.0,
                    outlier_count=0,
                    spread_consistency=0.7,  # Lower than OANDA
                    last_update=datetime.utcnow(),
                )

            # Calculate expected candles (simplified)
            expected_candles = self._calculate_expected_candles(
                timeframe, start_time, end_time
            )

            missing_candles = max(0, expected_candles - len(candles))
            gap_percentage = (
                (missing_candles / expected_candles * 100)
                if expected_candles > 0
                else 0
            )

            # Basic outlier detection
            outlier_count = 0
            for i in range(1, len(candles)):
                prev_close = candles[i - 1].close
                curr_open = candles[i].open
                gap_percentage_price = abs(curr_open - prev_close) / prev_close * 100
                if gap_percentage_price > 3.0:  # More sensitive than OANDA
                    outlier_count += 1

            return DataQualityMetrics(
                missing_candles=missing_candles,
                gap_percentage=gap_percentage,
                outlier_count=outlier_count,
                spread_consistency=0.7,  # Fixed assumption
                last_update=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Alpha Vantage data quality validation failed: {str(e)}")
            return DataQualityMetrics(
                missing_candles=0,
                gap_percentage=100.0,
                outlier_count=0,
                spread_consistency=0.0,
                last_update=datetime.utcnow(),
            )

    async def health_check(self) -> bool:
        """
        Perform health check on Alpha Vantage provider.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            if not self.api_key:
                # Demo mode is always "healthy"
                self.is_available = True
                self.last_health_check = datetime.utcnow()
                return True

            if not self._session:
                return False

            # Simple health check
            test_url = f"{self.base_url}?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=EUR&apikey={self.api_key}"

            async with self._session.get(test_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "Error Message" not in data:
                        self.is_available = True
                        self.last_health_check = datetime.utcnow()
                        return True

            self.is_available = False
            return False

        except Exception as e:
            logger.error(f"Alpha Vantage health check failed: {str(e)}")
            self.is_available = False
            return False

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()

    def _get_demo_candles(
        self, pair: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> List[SwingCandleData]:
        """
        Generate demo candles for testing without API key.

        Args:
            pair: Currency pair
            timeframe: Timeframe
            start_time: Start datetime
            end_time: End datetime

        Returns:
            List of demo candle data
        """
        logger.info(f"Generating demo candles for {pair} {timeframe}")

        candles = []
        current_time = start_time
        base_price = Decimal("1.1000" if pair == "EUR_USD" else "1.0000")

        # Time increment based on timeframe
        if timeframe == "D":
            increment = timedelta(days=1)
        elif timeframe == "W":
            increment = timedelta(weeks=1)
        else:
            return []

        # Fixed spread for demo
        fixed_spreads = {
            "EUR_USD": Decimal("2.0"),
            "GBP_USD": Decimal("2.5"),
            "USD_JPY": Decimal("2.3"),
            "USD_CHF": Decimal("2.7"),
            "AUD_USD": Decimal("3.0"),
            "USD_CAD": Decimal("3.3"),
            "NZD_USD": Decimal("3.5"),
        }
        spread = fixed_spreads.get(pair, Decimal("4.0"))

        while current_time <= end_time:
            # Skip weekends for daily data
            if timeframe == "D" and current_time.weekday() >= 5:
                current_time += increment
                continue

            # Generate realistic price movement
            price_change = Decimal(str((hash(str(current_time)) % 200 - 100) / 10000))
            open_price = base_price + price_change

            high_price = open_price + Decimal("0.002")
            low_price = open_price - Decimal("0.002")
            close_price = open_price + Decimal(
                str((hash(str(current_time + increment)) % 100 - 50) / 10000)
            )

            candle = SwingCandleData(
                timestamp=current_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=None,
                spread=spread,
            )

            candles.append(candle)
            base_price = close_price  # Update base for next candle
            current_time += increment

        return candles

    def _get_time_series_key(self, data: dict) -> Optional[str]:
        """
        Get the time series key from Alpha Vantage response.

        Args:
            data: API response data

        Returns:
            Time series key or None
        """
        possible_keys = [
            "Time Series FX (Daily)",
            "Time Series FX (Weekly)",
            "Time Series (Daily)",
            "Time Series (Weekly)",
        ]

        for key in possible_keys:
            if key in data:
                return key

        return None

    def _convert_av_candle(
        self, date_str: str, candle_data: dict, pair: str
    ) -> Optional[SwingCandleData]:
        """
        Convert Alpha Vantage candle format to SwingCandleData.

        Args:
            date_str: Date string from Alpha Vantage
            candle_data: Candle data from Alpha Vantage
            pair: Currency pair

        Returns:
            SwingCandleData object or None if conversion fails
        """
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(date_str)

            # Extract OHLC prices
            open_price = Decimal(candle_data["1. open"])
            high_price = Decimal(candle_data["2. high"])
            low_price = Decimal(candle_data["3. low"])
            close_price = Decimal(candle_data["4. close"])

            # Fixed spread for Alpha Vantage
            fixed_spreads = {
                "EUR_USD": Decimal("2.0"),
                "GBP_USD": Decimal("2.5"),
                "USD_JPY": Decimal("2.3"),
                "USD_CHF": Decimal("2.7"),
                "AUD_USD": Decimal("3.0"),
                "USD_CAD": Decimal("3.3"),
                "NZD_USD": Decimal("3.5"),
            }
            spread = fixed_spreads.get(pair, Decimal("4.0"))

            return SwingCandleData(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=None,  # Alpha Vantage FX doesn't include volume
                spread=spread,
            )

        except Exception as e:
            logger.error(f"Failed to convert Alpha Vantage candle: {str(e)}")
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

        if timeframe == "D":
            # 1 candle per day, minus weekends
            days = time_diff.days
            return days - (days // 7 * 2)
        elif timeframe == "W":
            # 1 candle per week
            return time_diff.days // 7

        return 0
