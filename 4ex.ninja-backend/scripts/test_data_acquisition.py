#!/usr/bin/env python3
"""
Data Acquisition Pipeline Test Script
Step 1.2 of Comprehensive Backtesting Plan

This script tests the data acquisition pipeline with a smaller subset
of data to validate functionality before running the full pipeline.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.data_acquisition_pipeline_fixed import (
    DataAcquisitionConfig,
    HistoricalDataAcquisition,
)
from scripts.backup_data_sources import BackupDataSourceConfig, BackupDataProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestDataAcquisitionConfig(DataAcquisitionConfig):
    """Test configuration with smaller dataset for validation."""

    def __post_init__(self):
        """Set test-specific configuration."""
        # Test with fewer pairs and shorter timeframe
        self.major_pairs = ["EUR_USD", "GBP_USD"]  # Only 2 major pairs for testing
        self.minor_pairs = ["EUR_GBP"]  # Only 1 minor pair for testing

        # Test with one timeframe
        self.timeframes = ["D"]  # Daily only for faster testing

        # Test with recent data (last 30 days)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

        # Test directories
        self.data_output_dir = "backtest_results/test_historical_data"
        self.reports_output_dir = "backtest_results/test_data_quality_reports"


async def test_data_acquisition_pipeline():
    """Test the data acquisition pipeline with a small dataset."""

    print("🧪 Testing Data Acquisition Pipeline")
    print("=" * 60)
    print("This test validates the pipeline with a small dataset:")
    print("   📊 Pairs: EUR/USD, GBP/USD, EUR/GBP")
    print("   📅 Timeframe: Daily")
    print("   📆 Period: Last 30 days")
    print()

    try:
        # Create test configuration
        config = TestDataAcquisitionConfig()

        # Create and run acquisition pipeline
        pipeline = HistoricalDataAcquisition(config)

        logger.info("🚀 Starting test data acquisition...")
        final_report = await pipeline.run_complete_acquisition()

        # Analyze results
        download_summary = final_report["download_summary"]
        success_rate = download_summary.get("success_rate", 0)

        print(f"\n📊 Test Results:")
        print(f"   ✅ Success Rate: {success_rate:.1f}%")
        print(f"   📈 Total Downloads: {download_summary['successful_downloads']}")
        print(f"   📉 Failed Downloads: {download_summary['failed_downloads']}")
        print(f"   🕐 Duration: {download_summary['total_duration']}")

        # Check if test was successful
        if success_rate >= 50:  # Lower threshold for testing
            print("\n🎉 Test PASSED - Pipeline is functional!")
            return True
        else:
            print("\n❌ Test FAILED - Pipeline needs attention")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        print(f"\n❌ Test FAILED - Error: {str(e)}")
        return False


async def test_backup_data_sources():
    """Test backup data source configuration."""

    print("\n🔧 Testing Backup Data Sources")
    print("=" * 60)

    try:
        # Initialize backup configuration
        config = BackupDataSourceConfig()

        # Test backup sources
        test_results = await config.test_backup_sources()

        # Count available sources
        available_count = sum(
            1 for result in test_results.values() if result["available"]
        )
        total_count = len(test_results)

        print(f"\n📊 Backup Source Test Results:")
        print(f"   📡 Available Sources: {available_count}/{total_count}")

        for source_id, result in test_results.items():
            status = "✅" if result["available"] else "❌"
            source_name = config.backup_sources[source_id]["name"]
            print(f"   {status} {source_name}")

        # Test backup data provider
        if available_count > 0:
            provider = BackupDataProvider(config)

            # Test getting sample data
            test_date = datetime.now() - timedelta(days=7)
            backup_data = await provider.get_backup_data(
                "EUR_USD", "D", test_date, datetime.now()
            )

            if backup_data is not None:
                print(f"   📊 Sample backup data: {len(backup_data)} records retrieved")
            else:
                print("   ⚠️ No backup data available for test")

        # Generate configuration file
        config_file = config.generate_backup_config_file()
        print(f"   📄 Configuration saved: {config_file}")

        return available_count > 0

    except Exception as e:
        logger.error(f"❌ Backup test failed: {str(e)}")
        print(f"❌ Backup test failed: {str(e)}")
        return False


async def test_infrastructure_readiness():
    """Test overall infrastructure readiness for Step 1.2."""

    print("\n🔍 Testing Infrastructure Readiness")
    print("=" * 60)

    readiness_checks = {
        "OANDA Provider": False,
        "Data Infrastructure": False,
        "Output Directories": False,
        "Logging System": False,
    }

    try:
        # Test OANDA provider import
        from src.backtesting.data_providers.oanda_provider import OandaProvider

        provider = OandaProvider()
        readiness_checks["OANDA Provider"] = True
        print("   ✅ OANDA Provider - Import successful")

        # Test data infrastructure import
        from src.backtesting.data_infrastructure import DataInfrastructure

        data_infra = DataInfrastructure()
        readiness_checks["Data Infrastructure"] = True
        print("   ✅ Data Infrastructure - Import successful")

        # Test output directories
        test_dirs = ["backtest_results", "logs"]
        for dir_name in test_dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        readiness_checks["Output Directories"] = True
        print("   ✅ Output Directories - Created successfully")

        # Test logging
        logger.info("Testing logging system")
        readiness_checks["Logging System"] = True
        print("   ✅ Logging System - Working correctly")

    except Exception as e:
        print(f"   ❌ Infrastructure test failed: {str(e)}")

    # Overall readiness assessment
    passed_checks = sum(readiness_checks.values())
    total_checks = len(readiness_checks)

    print(
        f"\n📊 Infrastructure Readiness: {passed_checks}/{total_checks} checks passed"
    )

    for check_name, passed in readiness_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")

    return passed_checks == total_checks


async def main():
    """Run comprehensive testing for Step 1.2."""

    print("🚀 Step 1.2: Data Acquisition & Preparation - TEST SUITE")
    print("=" * 80)
    print("This test suite validates the data acquisition pipeline before")
    print("running the full historical data download.")
    print()

    test_results = {}

    # Test 1: Infrastructure readiness
    test_results["infrastructure"] = await test_infrastructure_readiness()

    # Test 2: Backup data sources
    test_results["backup_sources"] = await test_backup_data_sources()

    # Test 3: Data acquisition pipeline (if infrastructure is ready)
    if test_results["infrastructure"]:
        test_results["pipeline"] = await test_data_acquisition_pipeline()
    else:
        print("\n⚠️ Skipping pipeline test due to infrastructure issues")
        test_results["pipeline"] = False

    # Final assessment
    print("\n" + "=" * 80)
    print("📋 FINAL TEST RESULTS")
    print("=" * 80)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name.replace('_', ' ').title()}")

    print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Ready for full data acquisition!")
        print("\nNext steps:")
        print("   1. Run: python scripts/data_acquisition_pipeline_fixed.py")
        print("   2. Monitor progress in logs/data_acquisition.log")
        print("   3. Review reports in backtest_results/data_quality_reports/")
    else:
        print("⚠️ SOME TESTS FAILED - Review issues before proceeding")

        if not test_results["infrastructure"]:
            print("\n🔧 Infrastructure Issues:")
            print("   - Check OANDA API configuration")
            print("   - Verify Python package dependencies")
            print("   - Ensure proper file permissions")

        if not test_results["backup_sources"]:
            print("\n🔄 Backup Source Issues:")
            print("   - Install optional dependencies: pip install yfinance")
            print("   - Configure API keys for external sources")

        if not test_results["pipeline"]:
            print("\n📊 Pipeline Issues:")
            print("   - Check network connectivity")
            print("   - Verify OANDA API credentials")
            print("   - Review error logs for details")

    print("=" * 80)

    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
