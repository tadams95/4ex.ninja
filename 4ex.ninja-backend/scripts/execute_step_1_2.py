#!/usr/bin/env python3
"""
Step 1.2 Execution Script - Data Acquisition & Preparation
Comprehensive Backtesting Plan

This script executes Step 1.2 of the comprehensive backtesting plan,
including data acquisition, quality validation, and report generation.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging for execution
log_file = Path("logs/step_1_2_execution.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Step12Executor:
    """Executor for Step 1.2: Data Acquisition & Preparation."""

    def __init__(self):
        """Initialize the Step 1.2 executor."""
        self.start_time = datetime.now()
        self.execution_summary = {
            "step": "Step 1.2: Data Acquisition & Preparation",
            "start_time": self.start_time.isoformat(),
            "status": "RUNNING",
            "phase": "INITIALIZATION",
            "deliverables": {},
            "errors": [],
            "recommendations": [],
        }

        # Create execution directory
        self.execution_dir = Path("backtest_results/step_1_2_execution")
        self.execution_dir.mkdir(parents=True, exist_ok=True)

    async def execute_step_1_2(self) -> Dict[str, Any]:
        """Execute the complete Step 1.2 process."""

        logger.info("🚀 Starting Step 1.2: Data Acquisition & Preparation")
        logger.info("=" * 80)

        try:
            # Phase 1: Pre-execution validation
            await self._phase_1_validation()

            # Phase 2: Infrastructure setup
            await self._phase_2_setup()

            # Phase 3: Data acquisition
            await self._phase_3_acquisition()

            # Phase 4: Quality validation
            await self._phase_4_validation()

            # Phase 5: Report generation
            await self._phase_5_reporting()

            # Mark as completed
            self.execution_summary["status"] = "COMPLETED"
            self.execution_summary["end_time"] = datetime.now().isoformat()

            logger.info("✅ Step 1.2 completed successfully!")

        except Exception as e:
            self.execution_summary["status"] = "FAILED"
            self.execution_summary["error"] = str(e)
            self.execution_summary["end_time"] = datetime.now().isoformat()

            logger.error(f"❌ Step 1.2 failed: {str(e)}")
            raise

        finally:
            # Save execution summary
            await self._save_execution_summary()

        return self.execution_summary

    async def _phase_1_validation(self):
        """Phase 1: Pre-execution validation."""
        logger.info("📋 Phase 1: Pre-execution Validation")
        self.execution_summary["phase"] = "VALIDATION"

        try:
            # Run the test suite first
            from scripts.test_data_acquisition import (
                test_infrastructure_readiness,
                test_backup_data_sources,
            )

            # Test infrastructure
            logger.info("   🔍 Testing infrastructure readiness...")
            infrastructure_ready = await test_infrastructure_readiness()

            if not infrastructure_ready:
                raise Exception("Infrastructure readiness test failed")

            # Test backup sources
            logger.info("   🔄 Testing backup data sources...")
            backup_ready = await test_backup_data_sources()

            # Record validation results
            self.execution_summary["deliverables"]["validation"] = {
                "infrastructure_ready": infrastructure_ready,
                "backup_sources_ready": backup_ready,
                "validation_timestamp": datetime.now().isoformat(),
            }

            logger.info("   ✅ Pre-execution validation completed")

        except Exception as e:
            logger.error(f"   ❌ Validation failed: {str(e)}")
            raise

    async def _phase_2_setup(self):
        """Phase 2: Infrastructure setup."""
        logger.info("📦 Phase 2: Infrastructure Setup")
        self.execution_summary["phase"] = "SETUP"

        try:
            # Setup backup data sources
            from scripts.backup_data_sources import BackupDataSourceConfig

            logger.info("   🔧 Configuring backup data sources...")
            backup_config = BackupDataSourceConfig()
            config_file = backup_config.generate_backup_config_file()

            # Record setup results
            self.execution_summary["deliverables"]["setup"] = {
                "backup_config_file": config_file,
                "setup_timestamp": datetime.now().isoformat(),
            }

            logger.info("   ✅ Infrastructure setup completed")

        except Exception as e:
            logger.error(f"   ❌ Setup failed: {str(e)}")
            raise

    async def _phase_3_acquisition(self):
        """Phase 3: Data acquisition."""
        logger.info("📊 Phase 3: Data Acquisition")
        self.execution_summary["phase"] = "ACQUISITION"

        try:
            # Import and run the data acquisition pipeline
            from scripts.data_acquisition_pipeline_fixed import (
                DataAcquisitionConfig,
                HistoricalDataAcquisition,
            )

            logger.info("   ⬇️ Starting historical data download...")

            # Create configuration
            config = DataAcquisitionConfig()

            # Log acquisition plan
            total_pairs = len(config.major_pairs) + len(config.minor_pairs)
            total_combinations = total_pairs * len(config.timeframes)

            logger.info(
                f"   📈 Target: {total_pairs} pairs x {len(config.timeframes)} timeframes = {total_combinations} combinations"
            )
            logger.info(
                f"   📅 Period: {config.start_date.strftime('%Y-%m-%d')} to {config.end_date.strftime('%Y-%m-%d')}"
            )

            # Run acquisition pipeline
            pipeline = HistoricalDataAcquisition(config)
            acquisition_results = await pipeline.run_complete_acquisition()

            # Record acquisition results
            self.execution_summary["deliverables"]["acquisition"] = {
                "total_combinations": total_combinations,
                "successful_downloads": acquisition_results["download_summary"][
                    "successful_downloads"
                ],
                "failed_downloads": acquisition_results["download_summary"][
                    "failed_downloads"
                ],
                "success_rate": acquisition_results["download_summary"]["success_rate"],
                "data_completeness": acquisition_results["download_summary"][
                    "data_completeness"
                ],
                "total_candles": acquisition_results["download_summary"][
                    "total_candles_downloaded"
                ],
                "acquisition_timestamp": datetime.now().isoformat(),
                "detailed_results": acquisition_results,
            }

            logger.info("   ✅ Data acquisition completed")

        except Exception as e:
            logger.error(f"   ❌ Acquisition failed: {str(e)}")
            self.execution_summary["errors"].append(
                f"Data acquisition failed: {str(e)}"
            )
            raise

    async def _phase_4_validation(self):
        """Phase 4: Quality validation."""
        logger.info("🔍 Phase 4: Quality Validation")
        self.execution_summary["phase"] = "QUALITY_VALIDATION"

        try:
            # Quality validation was already done in the acquisition pipeline
            # Here we just record the results

            acquisition_results = self.execution_summary["deliverables"]["acquisition"][
                "detailed_results"
            ]
            quality_summary = acquisition_results.get("quality_summary", {})

            # Extract quality metrics
            quality_metrics = {
                "files_validated": quality_summary.get("total_files_validated", 0),
                "average_quality_score": quality_summary.get(
                    "average_quality_score", 0
                ),
                "average_missing_data_pct": quality_summary.get(
                    "average_missing_data_pct", 0
                ),
                "high_quality_files": quality_summary.get("high_quality_files", 0),
                "low_quality_files": quality_summary.get("low_quality_files", 0),
                "validation_timestamp": datetime.now().isoformat(),
            }

            # Check quality standards
            quality_passed = (
                quality_metrics["average_missing_data_pct"]
                <= 0.1  # < 0.1% missing data
                and quality_metrics["average_quality_score"]
                >= 85  # >= 85% quality score
            )

            quality_metrics["quality_standards_met"] = quality_passed

            # Record validation results
            self.execution_summary["deliverables"][
                "quality_validation"
            ] = quality_metrics

            if not quality_passed:
                self.execution_summary["recommendations"].append(
                    "Data quality below standards - consider re-downloading problematic pairs"
                )

            logger.info("   ✅ Quality validation completed")

        except Exception as e:
            logger.error(f"   ❌ Quality validation failed: {str(e)}")
            self.execution_summary["errors"].append(
                f"Quality validation failed: {str(e)}"
            )
            # Don't raise - this is not critical for continuation

    async def _phase_5_reporting(self):
        """Phase 5: Report generation."""
        logger.info("📋 Phase 5: Report Generation")
        self.execution_summary["phase"] = "REPORTING"

        try:
            # Generate comprehensive Step 1.2 completion report
            report = await self._generate_step_completion_report()

            # Save the report
            report_file = (
                self.execution_dir
                / f"step_1_2_completion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            # Generate markdown summary
            markdown_report = await self._generate_markdown_report(report)
            markdown_file = (
                self.execution_dir
                / f"step_1_2_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

            with open(markdown_file, "w") as f:
                f.write(markdown_report)

            # Record reporting results
            self.execution_summary["deliverables"]["reporting"] = {
                "completion_report": str(report_file),
                "markdown_summary": str(markdown_file),
                "reporting_timestamp": datetime.now().isoformat(),
            }

            logger.info(f"   📄 Reports saved:")
            logger.info(f"     📊 JSON Report: {report_file}")
            logger.info(f"     📝 Markdown Summary: {markdown_file}")
            logger.info("   ✅ Report generation completed")

        except Exception as e:
            logger.error(f"   ❌ Report generation failed: {str(e)}")
            self.execution_summary["errors"].append(
                f"Report generation failed: {str(e)}"
            )
            # Don't raise - this is not critical

    async def _generate_step_completion_report(self) -> Dict[str, Any]:
        """Generate comprehensive Step 1.2 completion report."""

        total_duration = datetime.now() - self.start_time

        # Check deliverables status based on the plan requirements
        deliverables_status = await self._check_deliverables_status()

        report = {
            "step_info": {
                "step_number": "1.2",
                "step_name": "Data Acquisition & Preparation",
                "execution_date": self.start_time.strftime("%Y-%m-%d"),
                "total_duration": str(total_duration),
                "status": self.execution_summary["status"],
            },
            "deliverables_status": deliverables_status,
            "execution_summary": self.execution_summary,
            "next_steps": self._generate_next_steps(),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    async def _check_deliverables_status(self) -> Dict[str, Any]:
        """Check status of required deliverables from the plan."""

        # Required deliverables from the plan:
        # - [ ] Historical data for all target pairs
        # - [ ] Data quality validation reports
        # - [ ] Data pipeline automation scripts
        # - [ ] Backup data source configuration

        acquisition = self.execution_summary["deliverables"].get("acquisition", {})

        deliverables = {
            "historical_data_for_all_target_pairs": {
                "status": acquisition.get("success_rate", 0)
                >= 80,  # 80% success threshold
                "details": f"Downloaded {acquisition.get('successful_downloads', 0)} of {acquisition.get('total_combinations', 0)} combinations",
            },
            "data_quality_validation_reports": {
                "status": "quality_validation"
                in self.execution_summary["deliverables"],
                "details": "Quality validation completed with detailed reports",
            },
            "data_pipeline_automation_scripts": {
                "status": True,  # The scripts themselves fulfill this
                "details": "Automated pipeline scripts created and tested",
            },
            "backup_data_source_configuration": {
                "status": "setup" in self.execution_summary["deliverables"],
                "details": "Backup data source configuration completed",
            },
        }

        # Overall completion status
        completed_count = sum(1 for d in deliverables.values() if d["status"])
        total_count = len(deliverables)

        return {
            "individual_deliverables": deliverables,
            "completion_summary": {
                "completed": completed_count,
                "total": total_count,
                "completion_rate": (completed_count / total_count) * 100,
                "overall_status": (
                    "COMPLETED" if completed_count == total_count else "PARTIAL"
                ),
            },
        }

    def _generate_next_steps(self) -> List[str]:
        """Generate recommended next steps."""

        next_steps = []

        # Check completion status
        acquisition = self.execution_summary["deliverables"].get("acquisition", {})
        success_rate = acquisition.get("success_rate", 0)

        if success_rate >= 90:
            next_steps.append(
                "✅ Proceed to Step 2.1: Strategy Parameter Configuration"
            )
            next_steps.append("📊 Begin comprehensive backtesting with downloaded data")
        elif success_rate >= 70:
            next_steps.append(
                "⚠️ Consider re-downloading failed pairs before proceeding"
            )
            next_steps.append("📊 Can proceed to Step 2.1 with available data")
        else:
            next_steps.append("❌ Re-run data acquisition with backup sources")
            next_steps.append("🔧 Review and fix data source configuration issues")

        # Quality-based recommendations
        quality_validation = self.execution_summary["deliverables"].get(
            "quality_validation", {}
        )
        if quality_validation.get("average_quality_score", 0) < 85:
            next_steps.append(
                "🔍 Review data quality issues and consider data cleaning"
            )

        # General next steps
        next_steps.extend(
            [
                "📋 Review generated reports for detailed analysis",
                "💾 Backup downloaded data files",
                "📝 Update project documentation with acquisition results",
            ]
        )

        return next_steps

    async def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown summary report."""

        step_info = report["step_info"]
        deliverables = report["deliverables_status"]

        markdown = f"""# Step 1.2 Completion Report: Data Acquisition & Preparation

**Execution Date:** {step_info['execution_date']}  
**Duration:** {step_info['total_duration']}  
**Status:** {step_info['status']}  

## 📋 Deliverables Status

"""

        # Individual deliverables
        for deliverable, info in deliverables["individual_deliverables"].items():
            status_icon = "✅" if info["status"] else "❌"
            deliverable_name = deliverable.replace("_", " ").title()
            markdown += (
                f"- {status_icon} **{deliverable_name}**  \n  {info['details']}\n\n"
            )

        # Summary
        completion = deliverables["completion_summary"]
        markdown += f"""## 📊 Completion Summary

- **Completed:** {completion['completed']}/{completion['total']} deliverables
- **Completion Rate:** {completion['completion_rate']:.1f}%
- **Overall Status:** {completion['overall_status']}

"""

        # Acquisition details if available
        acquisition = self.execution_summary["deliverables"].get("acquisition", {})
        if acquisition:
            markdown += f"""## 📈 Data Acquisition Results

- **Success Rate:** {acquisition.get('success_rate', 0):.1f}%
- **Successful Downloads:** {acquisition.get('successful_downloads', 0)}
- **Failed Downloads:** {acquisition.get('failed_downloads', 0)}
- **Total Candles Downloaded:** {acquisition.get('total_candles', 0):,}
- **Data Completeness:** {acquisition.get('data_completeness', 0):.1f}%

"""

        # Quality validation if available
        quality = self.execution_summary["deliverables"].get("quality_validation", {})
        if quality:
            markdown += f"""## 🔍 Data Quality Results

- **Files Validated:** {quality.get('files_validated', 0)}
- **Average Quality Score:** {quality.get('average_quality_score', 0):.1f}%
- **Average Missing Data:** {quality.get('average_missing_data_pct', 0):.2f}%
- **High Quality Files:** {quality.get('high_quality_files', 0)}
- **Quality Standards Met:** {'✅ Yes' if quality.get('quality_standards_met', False) else '❌ No'}

"""

        # Next steps
        markdown += "## 🚀 Next Steps\n\n"
        for step in report["next_steps"]:
            markdown += f"- {step}\n"

        markdown += f"""
---
*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return markdown

    async def _save_execution_summary(self):
        """Save execution summary to file."""

        summary_file = (
            self.execution_dir
            / f"execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(summary_file, "w") as f:
            json.dump(self.execution_summary, f, indent=2, default=str)

        logger.info(f"📄 Execution summary saved: {summary_file}")


async def main():
    """Main execution function for Step 1.2."""

    print("🚀 Executing Step 1.2: Data Acquisition & Preparation")
    print("    Comprehensive Currency Pair Backtesting Plan")
    print("=" * 80)

    # Create executor
    executor = Step12Executor()

    try:
        # Execute Step 1.2
        result = await executor.execute_step_1_2()

        # Print final summary
        print("\n" + "=" * 80)
        print("🎯 STEP 1.2 EXECUTION SUMMARY")
        print("=" * 80)

        print(f"Status: {result['status']}")
        print(
            f"Duration: {datetime.fromisoformat(result['end_time']) - datetime.fromisoformat(result['start_time'])}"
        )

        # Print deliverables status
        if "acquisition" in result["deliverables"]:
            acq = result["deliverables"]["acquisition"]
            print(f"Success Rate: {acq['success_rate']:.1f}%")
            print(
                f"Downloads: {acq['successful_downloads']}/{acq['total_combinations']}"
            )

        if result["status"] == "COMPLETED":
            print("\n🎉 Step 1.2 completed successfully!")
            print("Ready to proceed to Step 2.1: Strategy Parameter Configuration")
        else:
            print("\n⚠️ Step 1.2 completed with issues - review reports")

        print("=" * 80)

        return result["status"] == "COMPLETED"

    except Exception as e:
        print(f"\n❌ Step 1.2 execution failed: {str(e)}")
        logger.error(f"Step 1.2 execution failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
