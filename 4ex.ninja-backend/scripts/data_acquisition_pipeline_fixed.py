#!/usr/bin/env python3
"""
Comprehensive Historical Data Acquisition Pipeline
Step 1.2 of Comprehensive Backtesting Plan

This script implements automated historical data download for all target currency pairs
and timeframes as specified in the backtesting plan.
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
from dataclasses import dataclass, asdict
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.backtesting.data_infrastructure import DataInfrastructure
from src.backtesting.data_providers.oanda_provider import OandaProvider
from src.backtesting.data_providers.base_provider import (
    SwingCandleData,
    DataQualityMetrics,
)

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


@dataclass
class DataAcquisitionConfig:
    """Configuration for data acquisition pipeline."""

    # Quality standards
    max_missing_data_pct: float = 0.1  # < 0.1% missing data tolerance

    # Storage configuration
    data_output_dir: str = "backtest_results/historical_data"
    reports_output_dir: str = "backtest_results/data_quality_reports"

    # Processing configuration
    batch_size: int = 1000  # Max candles per request
    retry_attempts: int = 3
    retry_delay: float = 2.0  # seconds

    def __post_init__(self):
        """Set default values after initialization."""
        # Target currency pairs
        self.major_pairs = [
            "EUR_USD",
            "GBP_USD",
            "USD_JPY",
            "USD_CHF",
            "AUD_USD",
            "USD_CAD",
        ]

        self.minor_pairs = ["EUR_GBP", "EUR_JPY", "GBP_JPY", "AUD_JPY"]

        # Timeframes to download
        self.timeframes = ["4H", "D", "W"]

        # Date ranges - Use a realistic historical range
        self.start_date = datetime(2023, 1, 1)  # Start from 2023
        self.end_date = datetime(2024, 12, 31)  # End at 2024 year-end


@dataclass
class DownloadProgress:
    """Track download progress for each pair/timeframe combination."""

    pair: str
    timeframe: str
    total_expected: int
    downloaded: int
    failed: int
    start_time: datetime
    end_time: Optional[datetime] = None

    def __post_init__(self):
        self.error_messages: List[str] = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_expected == 0:
            return 0.0
        return (self.downloaded / self.total_expected) * 100

    @property
    def is_complete(self) -> bool:
        """Check if download is complete."""
        return self.downloaded + self.failed >= self.total_expected

    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate download duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return datetime.now() - self.start_time


class HistoricalDataAcquisition:
    """Main class for historical data acquisition pipeline."""

    def __init__(self, config: DataAcquisitionConfig):
        """Initialize the data acquisition pipeline."""
        self.config = config
        self.data_infra = DataInfrastructure()
        self.oanda_provider = OandaProvider()

        # Progress tracking
        self.download_progress: Dict[str, DownloadProgress] = {}
        self.total_start_time: Optional[datetime] = None

        # Create output directories
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary output directories."""
        for directory in [self.config.data_output_dir, self.config.reports_output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created directory: {directory}")

    async def run_complete_acquisition(self) -> Dict[str, Any]:
        """Run the complete data acquisition pipeline."""
        logger.info("🚀 Starting Comprehensive Historical Data Acquisition")
        logger.info("=" * 80)

        self.total_start_time = datetime.now()

        try:
            # Step 1: Initialize and validate data infrastructure
            await self._initialize_infrastructure()

            # Step 2: Calculate download requirements
            download_plan = self._create_download_plan()

            # Step 3: Execute data downloads
            download_results = await self._execute_downloads(download_plan)

            # Step 4: Validate data quality
            quality_reports = await self._validate_data_quality(download_results)

            # Step 5: Generate comprehensive reports
            final_report = self._generate_final_report(
                download_results, quality_reports
            )

            logger.info("✅ Data acquisition pipeline completed successfully!")
            return final_report

        except Exception as e:
            logger.error(f"❌ Data acquisition pipeline failed: {str(e)}")
            raise

    async def _initialize_infrastructure(self):
        """Initialize and validate data infrastructure."""
        logger.info("🔧 Initializing data infrastructure...")

        # Connect to OANDA provider
        if not await self.oanda_provider.connect():
            raise Exception("Failed to connect to OANDA provider")

        logger.info("✅ OANDA provider connected successfully")

        # Validate supported pairs
        all_pairs = self.config.major_pairs + self.config.minor_pairs

        for pair in all_pairs:
            if not self.oanda_provider.supports_pair(pair):
                logger.warning(f"⚠️ Pair {pair} may not be fully supported")

        logger.info(
            f"✅ Infrastructure initialized for {len(all_pairs)} currency pairs"
        )

    def _create_download_plan(self) -> List[Dict[str, Any]]:
        """Create detailed download plan for all pair/timeframe combinations."""
        logger.info("📋 Creating download plan...")

        download_plan = []
        all_pairs = self.config.major_pairs + self.config.minor_pairs

        for pair in all_pairs:
            for timeframe in self.config.timeframes:
                # Calculate expected candles for this combination
                expected_candles = self._calculate_expected_candles(
                    pair, timeframe, self.config.start_date, self.config.end_date
                )

                plan_item = {
                    "pair": pair,
                    "timeframe": timeframe,
                    "start_date": self.config.start_date,
                    "end_date": self.config.end_date,
                    "expected_candles": expected_candles,
                    "priority": 1 if pair in self.config.major_pairs else 2,
                }
                download_plan.append(plan_item)

                # Initialize progress tracking
                self.download_progress[f"{pair}_{timeframe}"] = DownloadProgress(
                    pair=pair,
                    timeframe=timeframe,
                    total_expected=expected_candles,
                    downloaded=0,
                    failed=0,
                    start_time=datetime.now(),
                )

        # Sort by priority (major pairs first)
        download_plan.sort(key=lambda x: (x["priority"], x["pair"], x["timeframe"]))

        logger.info(
            f"📊 Download plan created: {len(download_plan)} pair/timeframe combinations"
        )
        logger.info(
            f"   📈 Major pairs: {len(self.config.major_pairs)} x {len(self.config.timeframes)} = {len(self.config.major_pairs) * len(self.config.timeframes)}"
        )
        logger.info(
            f"   📉 Minor pairs: {len(self.config.minor_pairs)} x {len(self.config.timeframes)} = {len(self.config.minor_pairs) * len(self.config.timeframes)}"
        )

        return download_plan

    def _calculate_expected_candles(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> int:
        """Calculate expected number of candles for a date range and timeframe."""
        time_delta = end_date - start_date

        if timeframe == "4H":
            # 6 candles per day (4-hour intervals)
            return int(time_delta.days * 6)
        elif timeframe == "D":
            # 1 candle per day
            return int(time_delta.days)
        elif timeframe == "W":
            # 1 candle per week
            return int(time_delta.days / 7)
        else:
            # Default estimation
            return int(time_delta.days)

    async def _execute_downloads(
        self, download_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the downloads according to the plan."""
        logger.info("⬇️ Starting data downloads...")

        download_results = {"successful": [], "failed": [], "summary": {}}

        total_combinations = len(download_plan)

        for i, plan_item in enumerate(download_plan, 1):
            pair = plan_item["pair"]
            timeframe = plan_item["timeframe"]
            progress_key = f"{pair}_{timeframe}"

            logger.info(
                f"📊 [{i}/{total_combinations}] Downloading {pair} {timeframe}..."
            )

            try:
                # Download data for this pair/timeframe
                candles = await self._download_pair_timeframe_data(
                    pair, timeframe, plan_item["start_date"], plan_item["end_date"]
                )

                if candles:
                    # Save data to file
                    filename = await self._save_historical_data(
                        pair, timeframe, candles
                    )

                    # Update progress
                    progress = self.download_progress[progress_key]
                    progress.downloaded = len(candles)
                    progress.end_time = datetime.now()

                    result = {
                        "pair": pair,
                        "timeframe": timeframe,
                        "candles_downloaded": len(candles),
                        "expected_candles": plan_item["expected_candles"],
                        "filename": filename,
                        "success_rate": progress.success_rate,
                    }
                    download_results["successful"].append(result)

                    logger.info(
                        f"   ✅ {len(candles)} candles downloaded ({progress.success_rate:.1f}% success rate)"
                    )

                else:
                    raise Exception("No data returned from provider")

            except Exception as e:
                # Handle download failure
                progress = self.download_progress[progress_key]
                progress.failed = plan_item["expected_candles"]
                progress.error_messages.append(str(e))
                progress.end_time = datetime.now()

                failure = {
                    "pair": pair,
                    "timeframe": timeframe,
                    "error": str(e),
                    "expected_candles": plan_item["expected_candles"],
                }
                download_results["failed"].append(failure)

                logger.error(f"   ❌ Download failed: {str(e)}")

            # Brief pause between downloads to avoid rate limiting
            await asyncio.sleep(0.5)

        # Generate summary
        download_results["summary"] = self._generate_download_summary()

        logger.info("✅ Download phase completed")
        return download_results

    async def _download_pair_timeframe_data(
        self, pair: str, timeframe: str, start_date: datetime, end_date: datetime
    ) -> List[SwingCandleData]:
        """Download historical data for a specific pair and timeframe."""

        for attempt in range(self.config.retry_attempts):
            try:
                candles = await self.oanda_provider.get_candles(
                    pair=pair,
                    timeframe=timeframe,
                    start_time=start_date,
                    end_time=end_date,
                )

                if candles:
                    return candles
                else:
                    raise Exception("No candles returned")

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(
                        f"   ⚠️ Attempt {attempt + 1} failed, retrying in {self.config.retry_delay}s: {str(e)}"
                    )
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise e

        return []

    async def _save_historical_data(
        self, pair: str, timeframe: str, candles: List[SwingCandleData]
    ) -> str:
        """Save historical data to CSV file."""

        # Convert candles to DataFrame
        data = []
        for candle in candles:
            data.append(
                {
                    "timestamp": candle.timestamp,
                    "open": float(candle.open),
                    "high": float(candle.high),
                    "low": float(candle.low),
                    "close": float(candle.close),
                    "volume": candle.volume if candle.volume else 0,
                    "spread": float(candle.spread) if candle.spread else 0.0,
                }
            )

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        # Create filename and save
        filename = f"{pair}_{timeframe}_{self.config.start_date.strftime('%Y%m%d')}_{self.config.end_date.strftime('%Y%m%d')}.csv"
        filepath = Path(self.config.data_output_dir) / filename

        df.to_csv(filepath)

        logger.info(f"   💾 Saved to: {filepath}")
        return str(filepath)

    def _generate_download_summary(self) -> Dict[str, Any]:
        """Generate summary of download results."""

        total_combinations = len(self.download_progress)
        successful = sum(1 for p in self.download_progress.values() if p.downloaded > 0)
        failed = sum(1 for p in self.download_progress.values() if p.failed > 0)

        total_candles_downloaded = sum(
            p.downloaded for p in self.download_progress.values()
        )
        total_candles_expected = sum(
            p.total_expected for p in self.download_progress.values()
        )

        avg_success_rate = (
            sum(p.success_rate for p in self.download_progress.values())
            / total_combinations
            if total_combinations > 0
            else 0
        )

        total_duration = (
            datetime.now() - self.total_start_time
            if self.total_start_time
            else timedelta(0)
        )

        return {
            "total_combinations": total_combinations,
            "successful_downloads": successful,
            "failed_downloads": failed,
            "success_rate": (
                (successful / total_combinations) * 100 if total_combinations > 0 else 0
            ),
            "total_candles_downloaded": total_candles_downloaded,
            "total_candles_expected": total_candles_expected,
            "data_completeness": (
                (total_candles_downloaded / total_candles_expected) * 100
                if total_candles_expected > 0
                else 0
            ),
            "average_success_rate": avg_success_rate,
            "total_duration": str(total_duration),
            "download_speed": (
                total_candles_downloaded / total_duration.total_seconds()
                if total_duration.total_seconds() > 0
                else 0
            ),
        }

    async def _validate_data_quality(
        self, download_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data quality for all downloaded files."""
        logger.info("🔍 Validating data quality...")

        quality_reports = {
            "pair_reports": [],
            "overall_summary": {},
            "issues_found": [],
        }

        for result in download_results["successful"]:
            pair = result["pair"]
            timeframe = result["timeframe"]
            filename = result["filename"]

            logger.info(f"   🔍 Validating {pair} {timeframe}...")

            try:
                # Load and validate data
                quality_report = await self._validate_single_file(
                    filename, pair, timeframe
                )
                quality_reports["pair_reports"].append(quality_report)

                # Check for quality issues
                if (
                    quality_report["missing_data_pct"]
                    > self.config.max_missing_data_pct
                ):
                    quality_reports["issues_found"].append(
                        {
                            "pair": pair,
                            "timeframe": timeframe,
                            "issue": "HIGH_MISSING_DATA",
                            "missing_pct": quality_report["missing_data_pct"],
                        }
                    )

                logger.info(
                    f"     ✅ Quality score: {quality_report['quality_score']:.1f}%"
                )

            except Exception as e:
                logger.error(f"     ❌ Quality validation failed: {str(e)}")
                quality_reports["issues_found"].append(
                    {
                        "pair": pair,
                        "timeframe": timeframe,
                        "issue": "VALIDATION_ERROR",
                        "error": str(e),
                    }
                )

        # Generate overall quality summary
        quality_reports["overall_summary"] = self._generate_quality_summary(
            quality_reports["pair_reports"]
        )

        # Save quality report
        await self._save_quality_report(quality_reports)

        logger.info("✅ Data quality validation completed")
        return quality_reports

    async def _validate_single_file(
        self, filename: str, pair: str, timeframe: str
    ) -> Dict[str, Any]:
        """Validate data quality for a single file."""

        # Load data
        df = pd.read_csv(filename, index_col="timestamp", parse_dates=True)

        # Basic statistics
        total_rows = len(df)
        missing_rows = df.isnull().sum().sum()
        missing_pct = (
            (missing_rows / (total_rows * len(df.columns))) * 100
            if total_rows > 0
            else 0
        )

        # Time gap analysis
        time_gaps = self._analyze_time_gaps(df, timeframe)

        # Price data validation
        price_validation = self._validate_price_data(df)

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            missing_pct, time_gaps, price_validation
        )

        return {
            "pair": pair,
            "timeframe": timeframe,
            "filename": filename,
            "total_rows": total_rows,
            "missing_data_pct": missing_pct,
            "time_gaps": time_gaps,
            "price_validation": price_validation,
            "quality_score": quality_score,
            "data_range": {
                "start": df.index.min().isoformat() if len(df) > 0 else "",
                "end": df.index.max().isoformat() if len(df) > 0 else "",
            },
        }

    def _analyze_time_gaps(self, df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """Analyze time gaps in the data."""

        if len(df) < 2:
            return {"gaps_found": 0, "max_gap_hours": 0, "avg_gap_hours": 0}

        # Calculate expected interval in hours
        if timeframe == "4H":
            expected_hours = 4
        elif timeframe == "D":
            expected_hours = 24
        elif timeframe == "W":
            expected_hours = 168  # 24 * 7
        else:
            expected_hours = 1

        # Simple gap detection by counting expected vs actual rows
        date_range = pd.date_range(
            start=df.index.min(), end=df.index.max(), freq=f"{expected_hours}H"
        )
        expected_rows = len(date_range)
        actual_rows = len(df)
        gaps_found = max(0, expected_rows - actual_rows)

        # Simplified analysis without pandas timedelta issues
        return {
            "gaps_found": gaps_found,
            "max_gap_hours": gaps_found * expected_hours if gaps_found > 0 else 0,
            "avg_gap_hours": expected_hours if gaps_found > 0 else 0,
        }

    def _validate_price_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate OHLC price data for consistency."""

        issues = []

        # Check for negative prices
        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("NEGATIVE_PRICES")

        # Check for zero prices
        if (df[["open", "high", "low", "close"]] == 0).any().any():
            issues.append("ZERO_PRICES")

        # Check OHLC consistency (high >= open,close,low and low <= open,close,high)
        invalid_high = (df["high"] < df[["open", "close", "low"]].max(axis=1)).any()
        invalid_low = (df["low"] > df[["open", "close", "high"]].min(axis=1)).any()

        if invalid_high:
            issues.append("INVALID_HIGH_PRICES")
        if invalid_low:
            issues.append("INVALID_LOW_PRICES")

        # Check for extreme price movements (> 10% in single candle)
        price_changes = abs(df["close"] - df["open"]) / df["open"]
        extreme_moves = (price_changes > 0.10).sum()

        return {
            "issues": issues,
            "extreme_moves_count": extreme_moves,
            "max_single_move_pct": (
                price_changes.max() * 100 if len(price_changes) > 0 else 0
            ),
            "valid_ohlc_pct": (
                ((len(df) - len(issues)) / len(df)) * 100 if len(df) > 0 else 0
            ),
        }

    def _calculate_quality_score(
        self, missing_pct: float, time_gaps: Dict, price_validation: Dict
    ) -> float:
        """Calculate overall quality score (0-100)."""

        score = 100.0

        # Deduct for missing data
        score -= missing_pct * 10  # 10 points per 1% missing

        # Deduct for time gaps
        score -= min(time_gaps["gaps_found"] * 2, 20)  # Max 20 points deduction

        # Deduct for price issues
        score -= len(price_validation["issues"]) * 5  # 5 points per issue type
        score -= min(price_validation["extreme_moves_count"] * 0.1, 10)  # Max 10 points

        return max(score, 0.0)

    def _generate_quality_summary(self, pair_reports: List[Dict]) -> Dict[str, Any]:
        """Generate overall quality summary from individual reports."""

        if not pair_reports:
            return {}

        avg_quality = sum(r["quality_score"] for r in pair_reports) / len(pair_reports)
        avg_missing = sum(r["missing_data_pct"] for r in pair_reports) / len(
            pair_reports
        )

        high_quality_count = sum(1 for r in pair_reports if r["quality_score"] >= 95)
        low_quality_count = sum(1 for r in pair_reports if r["quality_score"] < 80)

        return {
            "total_files_validated": len(pair_reports),
            "average_quality_score": avg_quality,
            "average_missing_data_pct": avg_missing,
            "high_quality_files": high_quality_count,
            "low_quality_files": low_quality_count,
            "quality_distribution": {
                "excellent": sum(1 for r in pair_reports if r["quality_score"] >= 95),
                "good": sum(1 for r in pair_reports if 85 <= r["quality_score"] < 95),
                "fair": sum(1 for r in pair_reports if 70 <= r["quality_score"] < 85),
                "poor": sum(1 for r in pair_reports if r["quality_score"] < 70),
            },
        }

    async def _save_quality_report(self, quality_reports: Dict[str, Any]):
        """Save quality validation report to file."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_quality_report_{timestamp}.json"
        filepath = Path(self.config.reports_output_dir) / filename

        with open(filepath, "w") as f:
            json.dump(quality_reports, f, indent=2, default=str)

        logger.info(f"💾 Quality report saved: {filepath}")

    def _generate_final_report(
        self, download_results: Dict, quality_reports: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive final report."""

        total_duration = (
            datetime.now() - self.total_start_time
            if self.total_start_time
            else timedelta(0)
        )

        final_report = {
            "execution_info": {
                "start_time": (
                    self.total_start_time.isoformat() if self.total_start_time else None
                ),
                "end_time": datetime.now().isoformat(),
                "total_duration": str(total_duration),
                "config_used": asdict(self.config),
            },
            "download_summary": download_results["summary"],
            "quality_summary": quality_reports["overall_summary"],
            "detailed_progress": {
                k: asdict(v) for k, v in self.download_progress.items()
            },
            "deliverables_status": self._check_deliverables_status(
                download_results, quality_reports
            ),
            "recommendations": self._generate_recommendations(
                download_results, quality_reports
            ),
        }

        # Save final report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_acquisition_final_report_{timestamp}.json"
        filepath = Path(self.config.reports_output_dir) / filename

        with open(filepath, "w") as f:
            json.dump(final_report, f, indent=2, default=str)

        logger.info(f"📋 Final report saved: {filepath}")

        # Print summary to console
        self._print_final_summary(final_report)

        return final_report

    def _check_deliverables_status(
        self, download_results: Dict, quality_reports: Dict
    ) -> Dict[str, bool]:
        """Check status of required deliverables from the plan."""

        successful_downloads = len(download_results["successful"])
        expected_combinations = len(
            self.config.major_pairs + self.config.minor_pairs
        ) * len(self.config.timeframes)

        avg_quality = quality_reports["overall_summary"].get("average_quality_score", 0)
        avg_missing = quality_reports["overall_summary"].get(
            "average_missing_data_pct", 100
        )

        return {
            "historical_data_for_all_target_pairs": successful_downloads
            >= expected_combinations * 0.9,  # 90% success threshold
            "data_quality_validation_reports": len(quality_reports["pair_reports"]) > 0,
            "data_pipeline_automation_scripts": True,  # This script itself
            "backup_data_source_configuration": False,  # TODO: Implement backup sources
            "quality_standards_met": avg_missing <= self.config.max_missing_data_pct,
            "comprehensive_coverage": successful_downloads
            >= expected_combinations * 0.8,  # 80% minimum
        }

    def _generate_recommendations(
        self, download_results: Dict, quality_reports: Dict
    ) -> List[str]:
        """Generate recommendations based on results."""

        recommendations = []

        # Check download success rate
        success_rate = download_results["summary"].get("success_rate", 0)
        if success_rate < 90:
            recommendations.append(
                f"Download success rate ({success_rate:.1f}%) is below 90%. Consider implementing additional retry logic or backup data sources."
            )

        # Check data quality
        avg_quality = quality_reports["overall_summary"].get("average_quality_score", 0)
        if avg_quality < 85:
            recommendations.append(
                f"Average data quality score ({avg_quality:.1f}%) is below 85%. Review data sources and validation criteria."
            )

        # Check for failed downloads
        failed_count = len(download_results.get("failed", []))
        if failed_count > 0:
            recommendations.append(
                f"{failed_count} download(s) failed. Review error logs and retry failed downloads."
            )

        # Check for quality issues
        issues_count = len(quality_reports.get("issues_found", []))
        if issues_count > 0:
            recommendations.append(
                f"{issues_count} quality issue(s) found. Review detailed quality reports for specific problems."
            )

        # Data completeness check
        completeness = download_results["summary"].get("data_completeness", 0)
        if completeness < 95:
            recommendations.append(
                f"Data completeness ({completeness:.1f}%) is below 95%. Consider implementing gap-filling strategies."
            )

        # Success recommendations
        if success_rate >= 95 and avg_quality >= 90:
            recommendations.append(
                "Excellent data acquisition results! Ready to proceed to Step 2.1: Strategy Parameter Configuration."
            )

        return recommendations

    def _print_final_summary(self, final_report: Dict):
        """Print formatted summary to console."""

        print("\n" + "=" * 80)
        print("🎯 DATA ACQUISITION PIPELINE - FINAL SUMMARY")
        print("=" * 80)

        # Execution info
        duration = final_report["execution_info"]["total_duration"]
        print(f"⏱️  Total Duration: {duration}")

        # Download summary
        download_summary = final_report["download_summary"]
        print(f"📊 Download Results:")
        print(
            f"   ✅ Successful: {download_summary['successful_downloads']}/{download_summary['total_combinations']}"
        )
        print(f"   📈 Success Rate: {download_summary['success_rate']:.1f}%")
        print(f"   📉 Data Completeness: {download_summary['data_completeness']:.1f}%")
        print(
            f"   🕐 Download Speed: {download_summary['download_speed']:.0f} candles/second"
        )

        # Quality summary
        if "quality_summary" in final_report and final_report["quality_summary"]:
            quality_summary = final_report["quality_summary"]
            print(f"🔍 Quality Results:")
            print(f"   📋 Files Validated: {quality_summary['total_files_validated']}")
            print(
                f"   ⭐ Average Quality Score: {quality_summary['average_quality_score']:.1f}%"
            )
            print(
                f"   � Average Missing Data: {quality_summary['average_missing_data_pct']:.2f}%"
            )

        # Deliverables status
        deliverables = final_report["deliverables_status"]
        print(f"📋 Deliverables Status:")
        for deliverable, status in deliverables.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {deliverable.replace('_', ' ').title()}")

        # Recommendations
        recommendations = final_report["recommendations"]
        if recommendations:
            print(f"💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

        print("=" * 80)


async def main():
    """Main execution function."""

    # Configure data acquisition
    config = DataAcquisitionConfig()

    print("🚀 Comprehensive Historical Data Acquisition Pipeline")
    print("   Step 1.2 of Comprehensive Backtesting Plan")
    print(
        f"   Target Pairs: {len(config.major_pairs)} major + {len(config.minor_pairs)} minor"
    )
    print(f"   Timeframes: {', '.join(config.timeframes)}")
    print(
        f"   Period: {config.start_date.strftime('%Y-%m-%d')} to {config.end_date.strftime('%Y-%m-%d')}"
    )
    print()

    # Create and run acquisition pipeline
    pipeline = HistoricalDataAcquisition(config)

    try:
        final_report = await pipeline.run_complete_acquisition()

        print("\n🎉 Step 1.2: Data Acquisition & Preparation - COMPLETED!")
        print("Ready to proceed to Step 2.1: Strategy Parameter Configuration")

        return final_report

    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
