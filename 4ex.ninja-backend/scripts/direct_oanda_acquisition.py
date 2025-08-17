#!/usr/bin/env python3
"""
Direct OANDA Data Acquisition Script
Step 1.2 - Working Implementation

This script bypasses the complex provider system and directly uses the OANDA API
to download historical data for all target currency pairs.
"""

import asyncio
import logging
import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.oanda_api import OandaAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/data_acquisition.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DirectDataAcquisition:
    """Direct OANDA data acquisition without complex provider layer."""

    def __init__(self):
        """Initialize the direct data acquisition."""
        self.oanda_api = OandaAPI()

        # Configuration
        self.major_pairs = [
            "EUR_USD",
            "GBP_USD",
            "USD_JPY",
            "USD_CHF",
            "AUD_USD",
            "USD_CAD",
        ]

        self.minor_pairs = ["EUR_GBP", "EUR_JPY", "GBP_JPY", "AUD_JPY"]

        self.timeframes = ["H4", "D", "W"]

        # Date range - use realistic historical range
        self.start_date = datetime(2023, 1, 1)
        self.end_date = datetime(2024, 12, 31)

        # Output directories
        self.data_dir = Path("backtest_results/historical_data")
        self.reports_dir = Path("backtest_results/data_quality_reports")

        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Progress tracking
        self.download_results = []

    async def run_acquisition(self) -> Dict[str, Any]:
        """Run the complete data acquisition process."""

        logger.info("🚀 Starting Direct OANDA Data Acquisition")
        logger.info("=" * 80)

        start_time = datetime.now()

        # Test connection first
        if not await self._test_connection():
            raise Exception("OANDA API connection failed")

        # Create download plan
        download_plan = self._create_download_plan()
        total_combinations = len(download_plan)

        logger.info(f"📋 Download plan created: {total_combinations} combinations")
        logger.info(
            f"   📈 Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"
        )

        # Execute downloads
        successful_downloads = 0
        failed_downloads = 0
        total_candles = 0

        for i, plan_item in enumerate(download_plan, 1):
            pair = plan_item["pair"]
            timeframe = plan_item["timeframe"]

            logger.info(
                f"📊 [{i}/{total_combinations}] Downloading {pair} {timeframe}..."
            )

            try:
                # Download data
                candles = await self._download_data(pair, timeframe)

                if candles and len(candles) > 0:
                    # Save to CSV
                    filename = await self._save_data(pair, timeframe, candles)

                    successful_downloads += 1
                    total_candles += len(candles)

                    self.download_results.append(
                        {
                            "pair": pair,
                            "timeframe": timeframe,
                            "candles": len(candles),
                            "filename": filename,
                            "status": "success",
                        }
                    )

                    logger.info(
                        f"   ✅ Success: {len(candles)} candles saved to {filename}"
                    )

                else:
                    failed_downloads += 1
                    self.download_results.append(
                        {
                            "pair": pair,
                            "timeframe": timeframe,
                            "candles": 0,
                            "filename": None,
                            "status": "failed",
                            "error": "No candles returned",
                        }
                    )
                    logger.error(f"   ❌ Failed: No candles returned")

            except Exception as e:
                failed_downloads += 1
                self.download_results.append(
                    {
                        "pair": pair,
                        "timeframe": timeframe,
                        "candles": 0,
                        "filename": None,
                        "status": "failed",
                        "error": str(e),
                    }
                )
                logger.error(f"   ❌ Failed: {str(e)}")

            # Small delay between requests
            await asyncio.sleep(0.1)

        # Generate final report
        end_time = datetime.now()
        duration = end_time - start_time

        success_rate = (
            (successful_downloads / total_combinations) * 100
            if total_combinations > 0
            else 0
        )

        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": str(duration),
            "total_combinations": total_combinations,
            "successful_downloads": successful_downloads,
            "failed_downloads": failed_downloads,
            "success_rate": success_rate,
            "total_candles": total_candles,
            "download_results": self.download_results,
        }

        # Save summary report
        report_file = (
            self.reports_dir
            / f"direct_acquisition_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info("=" * 80)
        logger.info("🎯 DIRECT DATA ACQUISITION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")
        logger.info(f"✅ Successful: {successful_downloads}/{total_combinations}")
        logger.info(f"📈 Total Candles: {total_candles:,}")
        logger.info(f"📄 Report saved: {report_file}")
        logger.info("=" * 80)

        return summary

    async def _test_connection(self) -> bool:
        """Test OANDA API connection."""
        try:
            # Test with a simple account details call
            account_details = self.oanda_api.get_account_details()
            if account_details:
                logger.info(
                    f"✅ OANDA connection successful - Account: {account_details.get('id', 'Unknown')}"
                )
                return True
            else:
                logger.error("❌ OANDA connection failed - No account details")
                return False
        except Exception as e:
            logger.error(f"❌ OANDA connection failed: {str(e)}")
            return False

    def _create_download_plan(self) -> List[Dict[str, Any]]:
        """Create download plan for all pairs and timeframes."""
        plan = []

        all_pairs = self.major_pairs + self.minor_pairs

        for pair in all_pairs:
            for timeframe in self.timeframes:
                plan.append(
                    {
                        "pair": pair,
                        "timeframe": timeframe,
                        "start_date": self.start_date,
                        "end_date": self.end_date,
                    }
                )

        return plan

    async def _download_data(self, pair: str, timeframe: str) -> List[Dict[str, Any]]:
        """Download historical data for a specific pair and timeframe."""

        start_str = self.start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_str = self.end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        try:
            # Call OANDA API directly with proper keyword arguments
            candles = self.oanda_api.get_candles(
                instrument=pair, granularity=timeframe, start=start_str, end=end_str
            )

            if candles:
                # Convert to our format
                processed_candles = []
                for candle in candles:
                    processed_candles.append(
                        {
                            "timestamp": candle.get("time", ""),
                            "open": float(candle.get("mid", {}).get("o", 0)),
                            "high": float(candle.get("mid", {}).get("h", 0)),
                            "low": float(candle.get("mid", {}).get("l", 0)),
                            "close": float(candle.get("mid", {}).get("c", 0)),
                            "volume": candle.get("volume", 0),
                        }
                    )

                return processed_candles
            else:
                return []

        except Exception as e:
            logger.error(f"Error downloading {pair} {timeframe}: {str(e)}")
            return []

    async def _save_data(
        self, pair: str, timeframe: str, candles: List[Dict[str, Any]]
    ) -> str:
        """Save candle data to CSV file."""

        # Convert to DataFrame
        df = pd.DataFrame(candles)

        # Parse timestamps
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        # Create filename
        filename = f"{pair}_{timeframe}_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.csv"
        filepath = self.data_dir / filename

        # Save to CSV
        df.to_csv(filepath)

        return str(filepath)


async def main():
    """Main execution function."""

    print("🚀 Direct OANDA Data Acquisition")
    print("=" * 60)

    try:
        # Create and run acquisition
        acquisition = DirectDataAcquisition()
        result = await acquisition.run_acquisition()

        # Check success
        if result["success_rate"] >= 80:
            print("🎉 Data acquisition completed successfully!")
            return True
        else:
            print("⚠️ Data acquisition completed with low success rate")
            return False

    except Exception as e:
        print(f"❌ Data acquisition failed: {str(e)}")
        logger.error(f"Data acquisition failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
