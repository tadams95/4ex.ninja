"""
Data Service
Provides price data for MA strategy calculations.
For production, this would connect to OANDA or other data providers.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from models.signal_models import PriceData


class DataService:
    """Service for providing price data."""

    def __init__(self):
        # Sample base prices for testing
        self.base_prices = {
            "EUR_USD": 1.0850,
            "GBP_USD": 1.2650,
            "USD_JPY": 150.25,
            "AUD_USD": 0.6580,
            "EUR_GBP": 0.8580,
            "GBP_JPY": 190.15,
            "NZD_USD": 0.6125,
            "USD_CAD": 1.3685,
        }

    async def get_historical_data(
        self, pair: str, timeframe: str = "D", count: int = 250
    ) -> List[PriceData]:
        """
        Get historical price data for a pair.

        Args:
            pair: Currency pair (e.g., "EUR_USD")
            timeframe: Timeframe (e.g., "D")
            count: Number of candles to return

        Returns:
            List of PriceData objects
        """
        if pair not in self.base_prices:
            raise ValueError(f"Unsupported pair: {pair}")

        base_price = self.base_prices[pair]
        data = []

        # Generate historical data (simplified for testing)
        start_date = datetime.utcnow() - timedelta(days=count)

        for i in range(count):
            timestamp = start_date + timedelta(days=i)

            # Simulate price movement with some trend and volatility
            trend_factor = 1 + (i / count) * 0.02  # Small upward trend
            volatility = random.uniform(0.995, 1.005)  # ±0.5% daily volatility

            close_price = base_price * trend_factor * volatility

            # Generate OHLC from close price
            open_price = close_price * random.uniform(0.999, 1.001)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.002)
            low_price = min(open_price, close_price) * random.uniform(0.998, 1.0)

            price_data = PriceData(
                pair=pair,
                timeframe=timeframe,
                timestamp=timestamp,
                open=round(open_price, 5),
                high=round(high_price, 5),
                low=round(low_price, 5),
                close=round(close_price, 5),
                volume=random.randint(1000, 10000),
            )

            data.append(price_data)

        return data

    async def get_current_price(self, pair: str) -> float:
        """Get current price for a pair."""
        if pair not in self.base_prices:
            raise ValueError(f"Unsupported pair: {pair}")

        base_price = self.base_prices[pair]
        # Add some random variation
        current_price = base_price * random.uniform(0.998, 1.002)
        return round(current_price, 5)

    async def get_all_current_prices(self) -> Dict[str, float]:
        """Get current prices for all supported pairs."""
        prices = {}
        for pair in self.base_prices.keys():
            prices[pair] = await self.get_current_price(pair)
        return prices

    async def get_historical_data_for_all_pairs(
        self, count: int = 250
    ) -> Dict[str, List[PriceData]]:
        """Get historical data for all supported pairs."""
        data_dict = {}

        for pair in self.base_prices.keys():
            pair_key = f"{pair}_D"  # Add timeframe suffix
            data_dict[pair_key] = await self.get_historical_data(pair, "D", count)

        return data_dict

    async def validate_data_availability(self, pair: str) -> bool:
        """Check if data is available for a pair."""
        return pair in self.base_prices

    async def get_supported_pairs(self) -> List[str]:
        """Get list of supported currency pairs."""
        return list(self.base_prices.keys())

    async def health_check(self) -> Dict[str, Any]:
        """Check data service health."""
        return {
            "status": "healthy",
            "supported_pairs": len(self.base_prices),
            "pairs": list(self.base_prices.keys()),
            "last_updated": datetime.utcnow().isoformat(),
        }
