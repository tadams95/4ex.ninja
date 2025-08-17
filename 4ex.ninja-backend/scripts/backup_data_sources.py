"""
Backup Data Source Configuration
Step 1.2 of Comprehensive Backtesting Plan

This module provides backup data source configuration and fallback mechanisms
for historical data acquisition when primary OANDA source fails.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class BackupDataSourceConfig:
    """Configuration and management for backup data sources."""

    def __init__(self):
        """Initialize backup data source configuration."""
        self.backup_sources = self._initialize_backup_sources()
        self.fallback_data_dir = "backtest_results/fallback_data"
        Path(self.fallback_data_dir).mkdir(parents=True, exist_ok=True)

    def _initialize_backup_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available backup data sources."""
        return {
            "alpha_vantage": {
                "name": "Alpha Vantage",
                "priority": 2,
                "available": False,
                "api_key_required": True,
                "rate_limit": "5 calls per minute",
                "supported_pairs": ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF"],
                "supported_timeframes": ["D"],  # Daily only for free tier
                "config": {
                    "base_url": "https://www.alphavantage.co/query",
                    "function": "FX_DAILY",
                },
            },
            "yahoo_finance": {
                "name": "Yahoo Finance",
                "priority": 3,
                "available": True,
                "api_key_required": False,
                "rate_limit": "Reasonable usage",
                "supported_pairs": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
                "supported_timeframes": ["D"],
                "config": {
                    "base_url": "https://finance.yahoo.com",
                    "library": "yfinance",
                },
            },
            "local_csv": {
                "name": "Local CSV Files",
                "priority": 4,
                "available": True,
                "api_key_required": False,
                "rate_limit": "None",
                "supported_pairs": ["ALL"],
                "supported_timeframes": ["4H", "D", "W"],
                "config": {"data_directory": "data/historical_backup", "format": "csv"},
            },
            "synthetic_data": {
                "name": "Synthetic Data Generator",
                "priority": 5,
                "available": True,
                "api_key_required": False,
                "rate_limit": "None",
                "supported_pairs": ["ALL"],
                "supported_timeframes": ["ALL"],
                "config": {
                    "method": "geometric_brownian_motion",
                    "volatility": 0.15,
                    "drift": 0.02,
                },
            },
        }

    def get_available_sources(self, pair: str, timeframe: str) -> List[Dict[str, Any]]:
        """Get available backup sources for a specific pair and timeframe."""
        available = []

        for source_id, source_config in self.backup_sources.items():
            if self._is_source_compatible(source_config, pair, timeframe):
                available.append(
                    {
                        "id": source_id,
                        "name": source_config["name"],
                        "priority": source_config["priority"],
                        "config": source_config,
                    }
                )

        # Sort by priority
        available.sort(key=lambda x: x["priority"])
        return available

    def _is_source_compatible(
        self, source_config: Dict, pair: str, timeframe: str
    ) -> bool:
        """Check if a source is compatible with the requested pair and timeframe."""
        if not source_config.get("available", False):
            return False

        # Check pair support
        supported_pairs = source_config.get("supported_pairs", [])
        if "ALL" not in supported_pairs and pair not in supported_pairs:
            return False

        # Check timeframe support
        supported_timeframes = source_config.get("supported_timeframes", [])
        if "ALL" not in supported_timeframes and timeframe not in supported_timeframes:
            return False

        return True

    async def test_backup_sources(self) -> Dict[str, Any]:
        """Test availability of backup data sources."""
        logger.info("🔍 Testing backup data sources...")

        test_results = {}

        for source_id, source_config in self.backup_sources.items():
            logger.info(f"   📡 Testing {source_config['name']}...")

            try:
                if source_id == "alpha_vantage":
                    result = await self._test_alpha_vantage()
                elif source_id == "yahoo_finance":
                    result = await self._test_yahoo_finance()
                elif source_id == "local_csv":
                    result = await self._test_local_csv()
                elif source_id == "synthetic_data":
                    result = await self._test_synthetic_data()
                else:
                    result = {"available": False, "error": "Unknown source"}

                test_results[source_id] = result

                if result["available"]:
                    logger.info(f"     ✅ {source_config['name']} available")
                else:
                    logger.warning(
                        f"     ❌ {source_config['name']} unavailable: {result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                test_results[source_id] = {"available": False, "error": str(e)}
                logger.error(f"     ❌ {source_config['name']} test failed: {str(e)}")

        # Update availability status
        self._update_source_availability(test_results)

        return test_results

    async def _test_alpha_vantage(self) -> Dict[str, Any]:
        """Test Alpha Vantage API availability."""
        try:
            # Check if API key is configured
            api_key = self._get_alpha_vantage_key()
            if not api_key:
                return {"available": False, "error": "API key not configured"}

            # TODO: Implement actual API test
            # For now, assume available if key exists
            return {"available": True, "test_performed": "API key check"}

        except Exception as e:
            return {"available": False, "error": str(e)}

    async def _test_yahoo_finance(self) -> Dict[str, Any]:
        """Test Yahoo Finance data availability."""
        try:
            # Try importing yfinance
            import yfinance as yf

            # Quick test with a simple request
            ticker = yf.Ticker("EURUSD=X")
            hist = ticker.history(period="5d")

            if not hist.empty:
                return {
                    "available": True,
                    "test_performed": "Successfully fetched EUR/USD data",
                }
            else:
                return {"available": False, "error": "No data returned"}

        except ImportError:
            return {"available": False, "error": "yfinance library not installed"}
        except Exception as e:
            return {"available": False, "error": str(e)}

    async def _test_local_csv(self) -> Dict[str, Any]:
        """Test local CSV data availability."""
        try:
            data_dir = Path(
                self.backup_sources["local_csv"]["config"]["data_directory"]
            )

            if not data_dir.exists():
                data_dir.mkdir(parents=True, exist_ok=True)
                return {"available": True, "test_performed": "Created data directory"}

            # Check if any CSV files exist
            csv_files = list(data_dir.glob("*.csv"))

            return {
                "available": True,
                "test_performed": f"Found {len(csv_files)} CSV files in backup directory",
            }

        except Exception as e:
            return {"available": False, "error": str(e)}

    async def _test_synthetic_data(self) -> Dict[str, Any]:
        """Test synthetic data generation capability."""
        try:
            # Test generating a small sample
            import numpy as np

            # Simple test of random generation
            np.random.seed(42)
            test_data = np.random.normal(0, 1, 100)

            return {
                "available": True,
                "test_performed": f"Generated {len(test_data)} synthetic data points",
            }

        except Exception as e:
            return {"available": False, "error": str(e)}

    def _get_alpha_vantage_key(self) -> Optional[str]:
        """Get Alpha Vantage API key from configuration."""
        # Try multiple sources for API key
        import os

        # Environment variable
        key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if key:
            return key

        # Config file
        try:
            config_path = Path("config/api_keys.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    return config.get("alpha_vantage_api_key")
        except:
            pass

        return None

    def _update_source_availability(self, test_results: Dict[str, Any]):
        """Update source availability based on test results."""
        for source_id, result in test_results.items():
            if source_id in self.backup_sources:
                self.backup_sources[source_id]["available"] = result["available"]

    def generate_backup_config_file(self) -> str:
        """Generate backup data source configuration file."""
        config_data = {
            "backup_sources": self.backup_sources,
            "generated_at": datetime.now().isoformat(),
            "configuration_notes": {
                "alpha_vantage": "Requires API key in environment variable ALPHA_VANTAGE_API_KEY",
                "yahoo_finance": "Requires yfinance library: pip install yfinance",
                "local_csv": "Place CSV files in data/historical_backup directory",
                "synthetic_data": "Always available for testing purposes",
            },
        }

        config_file = Path("config/backup_data_sources.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2, default=str)

        logger.info(f"📄 Backup configuration saved: {config_file}")
        return str(config_file)


class BackupDataProvider:
    """Provider for backup data sources when primary source fails."""

    def __init__(self, config: BackupDataSourceConfig):
        """Initialize backup data provider."""
        self.config = config

    async def get_backup_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get historical data from backup sources."""
        logger.info(f"🔄 Attempting backup data acquisition for {pair} {timeframe}")

        available_sources = self.config.get_available_sources(pair, timeframe)

        for source in available_sources:
            source_id = source["id"]
            logger.info(f"   📡 Trying {source['name']}...")

            try:
                if source_id == "yahoo_finance":
                    data = await self._get_yahoo_data(
                        pair, timeframe, start_date, end_date
                    )
                elif source_id == "local_csv":
                    data = await self._get_local_csv_data(
                        pair, timeframe, start_date, end_date
                    )
                elif source_id == "synthetic_data":
                    data = await self._get_synthetic_data(
                        pair, timeframe, start_date, end_date
                    )
                else:
                    continue

                if data is not None and not data.empty:
                    logger.info(
                        f"   ✅ Successfully obtained {len(data)} records from {source['name']}"
                    )
                    return data

            except Exception as e:
                logger.warning(f"   ❌ {source['name']} failed: {str(e)}")
                continue

        logger.error(f"❌ All backup sources failed for {pair} {timeframe}")
        return None

    async def _get_yahoo_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get data from Yahoo Finance."""
        try:
            import yfinance as yf

            # Convert pair format for Yahoo
            yahoo_symbol = self._convert_pair_to_yahoo_format(pair)

            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                return None

            # Convert to our standard format
            data = pd.DataFrame(
                {
                    "open": hist["Open"],
                    "high": hist["High"],
                    "low": hist["Low"],
                    "close": hist["Close"],
                    "volume": hist["Volume"],
                }
            )

            return data

        except Exception as e:
            logger.error(f"Yahoo Finance error: {str(e)}")
            return None

    async def _get_local_csv_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get data from local CSV files."""
        try:
            data_dir = Path(
                self.config.backup_sources["local_csv"]["config"]["data_directory"]
            )
            csv_file = data_dir / f"{pair}_{timeframe}.csv"

            if not csv_file.exists():
                return None

            data = pd.read_csv(csv_file, index_col=0, parse_dates=True)

            # Filter by date range
            mask = (data.index >= start_date) & (data.index <= end_date)
            filtered_data = data[mask]

            return filtered_data if not filtered_data.empty else None

        except Exception as e:
            logger.error(f"Local CSV error: {str(e)}")
            return None

    async def _get_synthetic_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Generate synthetic data for testing."""
        try:
            import numpy as np

            # Calculate time parameters
            if timeframe == "4H":
                freq = "4H"
                periods_per_day = 6
            elif timeframe == "D":
                freq = "D"
                periods_per_day = 1
            elif timeframe == "W":
                freq = "W"
                periods_per_day = 1 / 7
            else:
                freq = "H"
                periods_per_day = 24

            # Generate date range
            date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

            if len(date_range) == 0:
                return None

            # Synthetic price parameters
            initial_price = 1.1000  # EUR/USD base
            volatility = 0.15
            drift = 0.02

            # Generate price series using geometric Brownian motion
            np.random.seed(hash(pair) % 2**32)  # Deterministic but pair-specific

            dt = 1.0 / (periods_per_day * 365)  # Time step in years
            n_steps = len(date_range)

            # Generate random shocks
            shocks = np.random.normal(0, 1, n_steps)

            # Geometric Brownian motion
            returns = (drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(
                dt
            ) * shocks

            # Generate price series
            prices = [initial_price]
            for ret in returns[1:]:
                prices.append(prices[-1] * np.exp(ret))

            # Generate OHLC data
            data = []
            for i, price in enumerate(prices):
                # Add some intraday variation
                daily_range = price * 0.01 * np.random.uniform(0.5, 2.0)  # 0.5-2% range

                high = price + daily_range * np.random.uniform(0.2, 0.8)
                low = price - daily_range * np.random.uniform(0.2, 0.8)
                open_price = price + daily_range * np.random.uniform(-0.3, 0.3)
                close_price = price

                data.append(
                    {
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close_price,
                        "volume": np.random.randint(1000, 10000),
                    }
                )

            df = pd.DataFrame(data, index=date_range)

            logger.info(
                f"Generated {len(df)} synthetic data points for {pair} {timeframe}"
            )
            return df

        except Exception as e:
            logger.error(f"Synthetic data generation error: {str(e)}")
            return None

    def _convert_pair_to_yahoo_format(self, pair: str) -> str:
        """Convert currency pair to Yahoo Finance format."""
        conversions = {
            "EUR_USD": "EURUSD=X",
            "GBP_USD": "GBPUSD=X",
            "USD_JPY": "USDJPY=X",
            "USD_CHF": "USDCHF=X",
            "AUD_USD": "AUDUSD=X",
            "USD_CAD": "USDCAD=X",
        }

        return conversions.get(pair, f"{pair.replace('_', '')}=X")


async def main():
    """Test backup data source configuration."""
    print("🔧 Testing Backup Data Source Configuration")
    print("=" * 60)

    # Initialize configuration
    config = BackupDataSourceConfig()

    # Test all backup sources
    test_results = await config.test_backup_sources()

    # Generate configuration file
    config_file = config.generate_backup_config_file()

    # Test backup data provider
    provider = BackupDataProvider(config)

    # Test getting backup data
    test_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    print("\n📊 Testing backup data retrieval...")
    backup_data = await provider.get_backup_data("EUR_USD", "D", test_date, end_date)

    if backup_data is not None:
        print(
            f"✅ Successfully retrieved {len(backup_data)} records from backup sources"
        )
    else:
        print("❌ No backup data available")

    print(f"\n📄 Configuration saved to: {config_file}")
    print("🎉 Backup data source configuration completed!")


if __name__ == "__main__":
    asyncio.run(main())
