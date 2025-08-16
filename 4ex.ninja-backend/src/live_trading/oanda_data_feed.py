"""
OANDA Data Feed

Provides real-time and historical data from OANDA API in a format compatible
with our backtesting strategies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from api.oanda_api import OandaAPI
from config.settings import INSTRUMENTS, GRANULARITIES
from src.backtesting.strategy_interface import TradeSignal


class OandaDataFeed:
    """
    Real-time data feed from OANDA API that provides market data in a format
    compatible with backtesting strategies.
    """

    def __init__(self):
        """Initialize the OANDA data feed."""
        self.api = OandaAPI()
        self.supported_instruments = INSTRUMENTS
        self.supported_granularities = list(GRANULARITIES.keys())

    def get_latest_candles(
        self, instrument: str, granularity: str = "M5", count: int = 100
    ) -> pd.DataFrame:
        """
        Get the latest candlestick data for an instrument.

        Args:
            instrument: Trading instrument (e.g., 'EUR_USD')
            granularity: Timeframe ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D')
            count: Number of candles to retrieve

        Returns:
            DataFrame with OHLCV data compatible with strategies
        """
        try:
            # Get raw candle data from OANDA
            candles = self.api.get_candles(instrument, granularity, count=count)

            if not candles:
                print(f"No candle data received for {instrument}")
                return pd.DataFrame()

            # Convert to DataFrame format expected by strategies
            data = []
            for candle in candles:
                if candle.get("complete", True):  # Only use complete candles
                    mid = candle["mid"]
                    data.append(
                        {
                            "timestamp": pd.to_datetime(candle["time"]),
                            "open": float(mid["o"]),
                            "high": float(mid["h"]),
                            "low": float(mid["l"]),
                            "close": float(mid["c"]),
                            "volume": int(candle.get("volume", 0)),
                        }
                    )

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            print(f"Error getting latest candles for {instrument}: {e}")
            return pd.DataFrame()

    def get_current_price(self, instrument: str) -> Optional[float]:
        """
        Get the current market price for an instrument.

        Args:
            instrument: Trading instrument (e.g., 'EUR_USD')

        Returns:
            Current price or None if error
        """
        try:
            return self.api.get_current_price(instrument)
        except Exception as e:
            print(f"Error getting current price for {instrument}: {e}")
            return None

    def get_historical_data(
        self, instrument: str, granularity: str = "H1", days_back: int = 30
    ) -> pd.DataFrame:
        """
        Get historical candlestick data for backtesting or analysis.

        Args:
            instrument: Trading instrument
            granularity: Timeframe
            days_back: Number of days of history to retrieve

        Returns:
            DataFrame with historical OHLCV data
        """
        try:
            # Calculate start time
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)

            # Format times for OANDA API
            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

            # Get candles with time range
            candles = self.api.get_candles(
                instrument=instrument,
                granularity=granularity,
                start=start_str,
                end=end_str,
            )

            if not candles:
                return pd.DataFrame()

            # Convert to DataFrame
            data = []
            for candle in candles:
                if candle.get("complete", True):
                    mid = candle["mid"]
                    data.append(
                        {
                            "timestamp": pd.to_datetime(candle["time"]),
                            "open": float(mid["o"]),
                            "high": float(mid["h"]),
                            "low": float(mid["l"]),
                            "close": float(mid["c"]),
                            "volume": int(candle.get("volume", 0)),
                        }
                    )

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            print(f"Error getting historical data for {instrument}: {e}")
            return pd.DataFrame()

    def validate_instrument(self, instrument: str) -> bool:
        """
        Check if an instrument is supported for trading.

        Args:
            instrument: Trading instrument to validate

        Returns:
            True if instrument is supported
        """
        return instrument in self.supported_instruments

    def validate_granularity(self, granularity: str) -> bool:
        """
        Check if a granularity is supported.

        Args:
            granularity: Timeframe to validate

        Returns:
            True if granularity is supported
        """
        return granularity in self.supported_granularities

    def get_supported_instruments(self) -> List[str]:
        """Get list of supported trading instruments."""
        return self.supported_instruments.copy()

    def get_supported_granularities(self) -> List[str]:
        """Get list of supported timeframes."""
        return self.supported_granularities.copy()

    def test_connection(self) -> bool:
        """
        Test the connection to OANDA API.

        Returns:
            True if connection is successful
        """
        try:
            # Try to get account details as a connection test
            account = self.api.get_account_summary()
            return account is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


if __name__ == "__main__":
    # Test the data feed
    print("🧪 Testing OANDA Data Feed Connection...")

    feed = OandaDataFeed()

    # Test connection
    print("📡 Testing connection...")
    if feed.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        exit(1)

    # Test getting latest candles
    print("\n📊 Testing latest candles for EUR_USD...")
    df = feed.get_latest_candles("EUR_USD", "M5", count=20)

    if not df.empty:
        print(f"✅ Retrieved {len(df)} candles")
        print(f"📈 Latest price: {df['close'].iloc[-1]:.5f}")
        print(f"📅 Latest time: {df.index[-1]}")
        print("\n🔍 Sample data:")
        print(df.tail(3))
    else:
        print("❌ No candle data retrieved")

    # Test current price
    print(f"\n💰 Testing current price for EUR_USD...")
    current_price = feed.get_current_price("EUR_USD")
    if current_price:
        print(f"✅ Current price: {current_price:.5f}")
    else:
        print("❌ Could not get current price")

    print("\n🎯 OANDA Data Feed test completed!")
