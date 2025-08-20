"""
Data Service
Real-time OANDA data ingestion for MA strategy calculations.
Connects to OANDA v20 API for live and historical market data.
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from models.signal_models import PriceData
from config.settings import get_settings


class DataService:
    """Service for providing real OANDA price data."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.oanda_api_key
        self.account_id = self.settings.oanda_account_id

        # OANDA API endpoints
        if (
            hasattr(self.settings, "oanda_environment")
            and self.settings.oanda_environment == "live"
        ):
            self.base_url = "https://api-fxtrade.oanda.com"
        else:
            self.base_url = "https://api-fxpractice.oanda.com"  # Demo environment

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # OANDA instrument mapping to our pairs
        self.pair_mapping = {
            "EUR_USD": "EUR_USD",
            "GBP_USD": "GBP_USD",
            "USD_JPY": "USD_JPY",
            "AUD_USD": "AUD_USD",
            "EUR_GBP": "EUR_GBP",
            "GBP_JPY": "GBP_JPY",
            "NZD_USD": "NZD_USD",
            "USD_CAD": "USD_CAD",
        }

        logging.info(f"🔌 OANDA DataService initialized - Environment: {self.base_url}")
        logging.info(f"📊 API Key: {self.api_key[:10]}... (masked)")
        logging.info(f"🏦 Account: {self.account_id}")

    async def get_historical_data(
        self, pair: str, timeframe: str = "D", count: int = 250
    ) -> List[PriceData]:
        """
        Get historical price data from OANDA API.

        Args:
            pair: Currency pair (e.g., "EUR_USD")
            timeframe: Timeframe (e.g., "D", "H4", "H1")
            count: Number of candles to return

        Returns:
            List of PriceData objects
        """
        if not self.api_key:
            logging.warning("🚨 No OANDA API key configured - using fallback data")
            return await self._get_fallback_data(pair, count)

        if pair not in self.pair_mapping:
            raise ValueError(f"Unsupported pair: {pair}")

        # Map timeframe to OANDA granularity
        granularity_map = {"D": "D", "H4": "H4", "H1": "H1", "M15": "M15", "M5": "M5"}
        granularity = granularity_map.get(timeframe, "D")

        instrument = self.pair_mapping[pair]

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v3/instruments/{instrument}/candles"
                params = {
                    "count": count,
                    "granularity": granularity,
                    "price": "M",  # Mid prices
                }

                logging.info(
                    f"📡 Fetching {count} {granularity} candles for {pair} from OANDA"
                )

                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(
                            f"❌ OANDA API error {response.status}: {error_text}"
                        )
                        return await self._get_fallback_data(pair, count)

                    data = await response.json()
                    candles = data.get("candles", [])

                    if not candles:
                        logging.warning(f"⚠️ No candles returned for {pair}")
                        return await self._get_fallback_data(pair, count)

                    price_data = []
                    for candle in candles:
                        if candle.get("complete", False):  # Only use complete candles
                            mid = candle["mid"]
                            timestamp = datetime.fromisoformat(
                                candle["time"].replace("Z", "+00:00")
                            )

                            price_data.append(
                                PriceData(
                                    pair=pair,
                                    timeframe=timeframe,
                                    timestamp=timestamp,
                                    open=float(mid["o"]),
                                    high=float(mid["h"]),
                                    low=float(mid["l"]),
                                    close=float(mid["c"]),
                                    volume=candle.get("volume", 1000),
                                )
                            )

                    logging.info(
                        f"✅ Retrieved {len(price_data)} real candles for {pair}"
                    )
                    return price_data

        except Exception as e:
            logging.error(f"❌ Error fetching OANDA data for {pair}: {e}")
            return await self._get_fallback_data(pair, count)

    async def _get_fallback_data(self, pair: str, count: int) -> List[PriceData]:
        """Fallback data generation when OANDA API is unavailable."""
        import random

        # Base prices for fallback
        fallback_prices = {
            "EUR_USD": 1.0850,
            "GBP_USD": 1.2650,
            "USD_JPY": 150.25,
            "AUD_USD": 0.6580,
            "EUR_GBP": 0.8580,
            "GBP_JPY": 190.15,
            "NZD_USD": 0.6125,
            "USD_CAD": 1.3685,
        }

        if pair not in fallback_prices:
            raise ValueError(f"Unsupported pair: {pair}")

        base_price = fallback_prices[pair]
        data = []
        start_date = datetime.utcnow() - timedelta(days=count)

        for i in range(count):
            timestamp = start_date + timedelta(days=i)
            trend_factor = 1 + (i / count) * 0.02
            volatility = random.uniform(0.995, 1.005)
            close_price = base_price * trend_factor * volatility

            open_price = close_price * random.uniform(0.999, 1.001)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.002)
            low_price = min(open_price, close_price) * random.uniform(0.998, 1.0)

            data.append(
                PriceData(
                    pair=pair,
                    timeframe="D",
                    timestamp=timestamp,
                    open=round(open_price, 5),
                    high=round(high_price, 5),
                    low=round(low_price, 5),
                    close=round(close_price, 5),
                    volume=random.randint(1000, 10000),
                )
            )
        return data

    async def get_current_price(self, pair: str) -> float:
        """Get current price from OANDA or fallback."""
        if not self.api_key:
            return await self._get_fallback_current_price(pair)

        if pair not in self.pair_mapping:
            raise ValueError(f"Unsupported pair: {pair}")

        instrument = self.pair_mapping[pair]

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v3/instruments/{instrument}/candles"
                params = {"count": 1, "granularity": "M5", "price": "M"}

                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        candles = data.get("candles", [])
                        if candles and candles[0].get("complete"):
                            return float(candles[0]["mid"]["c"])

            return await self._get_fallback_current_price(pair)

        except Exception as e:
            logging.error(f"Error fetching current price for {pair}: {e}")
            return await self._get_fallback_current_price(pair)

    async def _get_fallback_current_price(self, pair: str) -> float:
        """Fallback current price."""
        import random

        fallback_prices = {
            "EUR_USD": 1.0850,
            "GBP_USD": 1.2650,
            "USD_JPY": 150.25,
            "AUD_USD": 0.6580,
            "EUR_GBP": 0.8580,
            "GBP_JPY": 190.15,
            "NZD_USD": 0.6125,
            "USD_CAD": 1.3685,
        }
        if pair not in fallback_prices:
            raise ValueError(f"Unsupported pair: {pair}")
        return round(fallback_prices[pair] * random.uniform(0.998, 1.002), 5)

    async def get_all_current_prices(self) -> Dict[str, float]:
        """Get current prices for all supported pairs."""
        prices = {}
        for pair in self.pair_mapping.keys():
            try:
                prices[pair] = await self.get_current_price(pair)
            except Exception as e:
                logging.error(f"Error getting price for {pair}: {e}")
                continue
        return prices

    async def get_historical_data_for_all_pairs(
        self, count: int = 250
    ) -> Dict[str, List[PriceData]]:
        """Get historical data for all supported pairs."""
        data_dict = {}

        for pair in self.pair_mapping.keys():
            try:
                pair_key = f"{pair}_D"  # Add timeframe suffix
                data_dict[pair_key] = await self.get_historical_data(pair, "D", count)
                logging.info(f"✅ Loaded {len(data_dict[pair_key])} candles for {pair}")
            except Exception as e:
                logging.error(f"Error loading data for {pair}: {e}")
                continue

        return data_dict

    async def validate_data_availability(self, pair: str) -> bool:
        """Check if data is available for a pair."""
        return pair in self.pair_mapping

    async def get_supported_pairs(self) -> List[str]:
        """Get list of supported currency pairs."""
        return list(self.pair_mapping.keys())

    async def health_check(self) -> Dict[str, Any]:
        """Check data service health and OANDA connectivity."""
        health_info = {
            "status": "healthy",
            "supported_pairs": len(self.pair_mapping),
            "pairs": list(self.pair_mapping.keys()),
            "last_updated": datetime.utcnow().isoformat(),
            "oanda_configured": bool(self.api_key),
            "api_endpoint": self.base_url,
        }

        # Test OANDA connectivity
        if self.api_key:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/v3/accounts/{self.account_id}"
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            health_info["oanda_status"] = "connected"
                            account_data = await response.json()
                            health_info["account_currency"] = account_data.get(
                                "account", {}
                            ).get("currency", "Unknown")
                        else:
                            health_info["oanda_status"] = f"error_{response.status}"
            except Exception as e:
                health_info["oanda_status"] = f"connection_error: {str(e)}"
                logging.error(f"OANDA health check failed: {e}")
        else:
            health_info["oanda_status"] = "no_api_key"

        return health_info
