#!/usr/bin/env python3
"""
Historical Data Fetcher for 4ex.ninja
Fetches 5 years of H4 OANDA data and saves to JSON files
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from services.data_service import DataService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalDataFetcher:
    def __init__(self):
        self.data_service = DataService()
        self.output_dir = "backtest_data/historical_data"
        self.pairs = [
            "EUR_USD",
            "GBP_USD",
            "USD_JPY",
            "USD_CHF",
            "USD_CAD",
            "AUD_USD",
            "EUR_GBP",
            "EUR_JPY",
            "GBP_JPY",
            "AUD_JPY",
        ]
        self.backtest_years = 5

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    async def fetch_pair_data(self, pair: str) -> Dict[str, Any]:
        """Fetch historical data for a single currency pair"""
        try:
            logger.info(
                f"📊 Fetching {self.backtest_years} years of H4 data for {pair}..."
            )

            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=self.backtest_years * 365)

            # Calculate expected periods (H4 = 6 candles per day)
            expected_periods = self.backtest_years * 365 * 6

            logger.info(
                f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )
            logger.info(f"   Expected candles: ~{expected_periods}")

            # Fetch historical data using the main method (which will use chunked automatically)
            historical_data = await self.data_service.get_historical_data(
                pair=pair, timeframe="H4", count=expected_periods
            )

            if not historical_data:
                logger.error(f"❌ No data received for {pair}")
                return {"pair": pair, "data": [], "error": "No data received"}

            logger.info(f"✅ {pair}: Fetched {len(historical_data)} H4 candles")

            # Convert data to serializable format
            serializable_data = []
            for candle in historical_data:
                serializable_data.append(
                    {
                        "timestamp": candle.timestamp.isoformat(),
                        "open": float(candle.open),
                        "high": float(candle.high),
                        "low": float(candle.low),
                        "close": float(candle.close),
                        "volume": int(candle.volume) if candle.volume else 0,
                    }
                )

            return {
                "pair": pair,
                "timeframe": "H4",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "candle_count": len(serializable_data),
                "data": serializable_data,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error fetching data for {pair}: {str(e)}")
            return {"pair": pair, "data": [], "error": str(e)}

    async def save_pair_data(self, pair_data: Dict[str, Any]) -> None:
        """Save pair data to JSON file"""
        try:
            pair = pair_data["pair"]
            filename = f"{pair}_H4_{self.backtest_years}Y.json"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(pair_data, f, indent=2)

            logger.info(f"💾 Saved {pair} data to {filename}")

        except Exception as e:
            logger.error(
                f"❌ Error saving data for {pair_data.get('pair', 'unknown')}: {str(e)}"
            )

    async def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all historical data for all pairs"""
        logger.info(f"🚀 Starting historical data fetch for {len(self.pairs)} pairs")
        logger.info(f"📅 Fetching {self.backtest_years} years of H4 data")
        logger.info(f"📁 Output directory: {self.output_dir}")

        summary = {
            "fetch_started": datetime.now(timezone.utc).isoformat(),
            "pairs_requested": self.pairs,
            "timeframe": "H4",
            "years": self.backtest_years,
            "results": {},
        }

        # Fetch data for each pair sequentially to avoid rate limits
        for i, pair in enumerate(self.pairs, 1):
            logger.info(f"[{i}/{len(self.pairs)}] Processing {pair}...")

            pair_data = await self.fetch_pair_data(pair)
            await self.save_pair_data(pair_data)

            # Update summary
            summary["results"][pair] = {
                "success": "error" not in pair_data,
                "candle_count": pair_data.get("candle_count", 0),
                "error": pair_data.get("error"),
            }

            # Small delay to be respectful to API
            if i < len(self.pairs):
                await asyncio.sleep(1)

        summary["fetch_completed"] = datetime.now(timezone.utc).isoformat()

        # Save summary
        summary_file = os.path.join(self.output_dir, "fetch_summary.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📋 Fetch summary saved to fetch_summary.json")

        return summary

    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print fetch results summary"""
        print("\n" + "=" * 60)
        print("📊 HISTORICAL DATA FETCH SUMMARY")
        print("=" * 60)

        total_pairs = len(summary["pairs_requested"])
        successful = sum(
            1 for result in summary["results"].values() if result["success"]
        )
        failed = total_pairs - successful

        print(f"Pairs Requested: {total_pairs}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Timeframe: {summary['timeframe']}")
        print(f"Years: {summary['years']}")

        print("\n📈 PAIR RESULTS:")
        for pair, result in summary["results"].items():
            status = "✅" if result["success"] else "❌"
            candles = result["candle_count"]
            error = f" ({result['error']})" if result.get("error") else ""
            print(f"  {status} {pair}: {candles:,} candles{error}")

        total_candles = sum(
            result["candle_count"] for result in summary["results"].values()
        )
        print(f"\n📊 Total Candles Fetched: {total_candles:,}")

        if successful == total_pairs:
            print("🎉 All data fetched successfully!")
        elif successful > 0:
            print(f"⚠️ Partial success - {failed} pairs failed")
        else:
            print("❌ All fetches failed")

        print("=" * 60)


async def main():
    """Main execution function"""
    fetcher = HistoricalDataFetcher()

    try:
        summary = await fetcher.fetch_all_data()
        fetcher.print_summary(summary)

    except Exception as e:
        logger.error(f"❌ Fatal error during data fetch: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
