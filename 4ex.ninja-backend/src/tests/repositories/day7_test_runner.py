"""
Day 7 Testing & Validation Suite Runner

This module provides a unified test runner for all Day 7 testing objectives:
- Task 1.5.25: Comprehensive repository tests with test database
- Task 1.5.26: Integration tests for database operations
- Task 1.5.27: Data consistency and constraint enforcement validation
- Task 1.5.28: Performance testing and load validation
"""

import asyncio
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Import all test suites
from .test_integration_suite import TestIntegrationSuite
from .test_database_integration import DatabaseIntegrationTestSuite
from .test_data_consistency import DataConsistencyTestSuite
from .test_performance_validation import PerformanceTestSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Day7TestSuiteRunner:
    """
    Unified test runner for all Day 7 testing and validation objectives.

    Coordinates execution of all test suites and provides comprehensive reporting.
    """

    def __init__(self):
        """Initialize Day 7 test suite runner."""
        self.test_suites = {
            "1.5.25_Repository_Tests": TestIntegrationSuite(),
            "1.5.26_Database_Integration": DatabaseIntegrationTestSuite(),
            "1.5.27_Data_Consistency": DataConsistencyTestSuite(),
            "1.5.28_Performance_Validation": PerformanceTestSuite(),
        }
        self.results = {}

    async def run_all_day7_tests(
        self, include_performance: bool = True
    ) -> Dict[str, Any]:
        """
        Run all Day 7 test objectives.

        Args:
            include_performance: Whether to include performance tests (can be slow)

        Returns:
            Comprehensive test results for all Day 7 objectives
        """
        overall_results = {
            "day": "Day 7",
            "objective": "Testing & Validation for Database Layer & Repository Pattern",
            "test_run_timestamp": datetime.utcnow().isoformat(),
            "overall_summary": {
                "total_test_suites": 0,
                "passed_test_suites": 0,
                "failed_test_suites": 0,
                "total_individual_tests": 0,
                "passed_individual_tests": 0,
                "failed_individual_tests": 0,
                "skipped_individual_tests": 0,
            },
            "test_suite_results": {},
            "completion_status": {
                "1.5.25_Repository_Tests": "NOT_STARTED",
                "1.5.26_Database_Integration": "NOT_STARTED",
                "1.5.27_Data_Consistency": "NOT_STARTED",
                "1.5.28_Performance_Validation": "NOT_STARTED",
            },
            "recommendations": [],
        }

        logger.info("Starting Day 7 Testing & Validation Suite")
        logger.info("=" * 60)

        # Task 1.5.25: Repository Tests
        logger.info("Running Task 1.5.25: Comprehensive Repository Tests")
        try:
            repo_results = await self.test_suites[
                "1.5.25_Repository_Tests"
            ].run_all_tests()
            overall_results["test_suite_results"][
                "1.5.25_Repository_Tests"
            ] = repo_results
            overall_results["completion_status"][
                "1.5.25_Repository_Tests"
            ] = "COMPLETED"

            # Update summary
            overall_results["overall_summary"]["total_test_suites"] += 1
            overall_results["overall_summary"][
                "total_individual_tests"
            ] += repo_results.get("total_tests", 0)
            overall_results["overall_summary"][
                "passed_individual_tests"
            ] += repo_results.get("passed_tests", 0)
            overall_results["overall_summary"][
                "failed_individual_tests"
            ] += repo_results.get("failed_tests", 0)
            overall_results["overall_summary"][
                "skipped_individual_tests"
            ] += repo_results.get("skipped_tests", 0)

            if repo_results.get("failed_tests", 0) == 0:
                overall_results["overall_summary"]["passed_test_suites"] += 1
            else:
                overall_results["overall_summary"]["failed_test_suites"] += 1

            logger.info(
                f"✅ Task 1.5.25 completed: {repo_results.get('passed_tests', 0)}/{repo_results.get('total_tests', 0)} tests passed"
            )

        except Exception as e:
            logger.error(f"❌ Task 1.5.25 failed: {str(e)}")
            overall_results["completion_status"]["1.5.25_Repository_Tests"] = "FAILED"
            overall_results["overall_summary"]["failed_test_suites"] += 1
            overall_results["test_suite_results"]["1.5.25_Repository_Tests"] = {
                "error": str(e)
            }

        # Task 1.5.26: Database Integration Tests
        logger.info("\nRunning Task 1.5.26: Database Integration Tests")
        try:
            db_results = await self.test_suites[
                "1.5.26_Database_Integration"
            ].run_all_integration_tests()
            overall_results["test_suite_results"][
                "1.5.26_Database_Integration"
            ] = db_results
            overall_results["completion_status"][
                "1.5.26_Database_Integration"
            ] = "COMPLETED"

            # Update summary
            overall_results["overall_summary"]["total_test_suites"] += 1
            overall_results["overall_summary"][
                "total_individual_tests"
            ] += db_results.get("total_tests", 0)
            overall_results["overall_summary"][
                "passed_individual_tests"
            ] += db_results.get("passed_tests", 0)
            overall_results["overall_summary"][
                "failed_individual_tests"
            ] += db_results.get("failed_tests", 0)

            if db_results.get("failed_tests", 0) == 0:
                overall_results["overall_summary"]["passed_test_suites"] += 1
            else:
                overall_results["overall_summary"]["failed_test_suites"] += 1

            logger.info(
                f"✅ Task 1.5.26 completed: {db_results.get('passed_tests', 0)}/{db_results.get('total_tests', 0)} tests passed"
            )

        except Exception as e:
            logger.error(f"❌ Task 1.5.26 failed: {str(e)}")
            overall_results["completion_status"][
                "1.5.26_Database_Integration"
            ] = "FAILED"
            overall_results["overall_summary"]["failed_test_suites"] += 1
            overall_results["test_suite_results"]["1.5.26_Database_Integration"] = {
                "error": str(e)
            }

        # Task 1.5.27: Data Consistency Validation
        logger.info("\nRunning Task 1.5.27: Data Consistency & Constraint Enforcement")
        try:
            consistency_results = await self.test_suites[
                "1.5.27_Data_Consistency"
            ].run_all_consistency_tests()
            overall_results["test_suite_results"][
                "1.5.27_Data_Consistency"
            ] = consistency_results
            overall_results["completion_status"][
                "1.5.27_Data_Consistency"
            ] = "COMPLETED"

            # Update summary
            overall_results["overall_summary"]["total_test_suites"] += 1
            overall_results["overall_summary"][
                "total_individual_tests"
            ] += consistency_results.get("total_tests", 0)
            overall_results["overall_summary"][
                "passed_individual_tests"
            ] += consistency_results.get("passed_tests", 0)
            overall_results["overall_summary"][
                "failed_individual_tests"
            ] += consistency_results.get("failed_tests", 0)

            if consistency_results.get("failed_tests", 0) == 0:
                overall_results["overall_summary"]["passed_test_suites"] += 1
            else:
                overall_results["overall_summary"]["failed_test_suites"] += 1

            logger.info(
                f"✅ Task 1.5.27 completed: {consistency_results.get('passed_tests', 0)}/{consistency_results.get('total_tests', 0)} tests passed"
            )

        except Exception as e:
            logger.error(f"❌ Task 1.5.27 failed: {str(e)}")
            overall_results["completion_status"]["1.5.27_Data_Consistency"] = "FAILED"
            overall_results["overall_summary"]["failed_test_suites"] += 1
            overall_results["test_suite_results"]["1.5.27_Data_Consistency"] = {
                "error": str(e)
            }

        # Task 1.5.28: Performance Validation (optional)
        if include_performance:
            logger.info("\nRunning Task 1.5.28: Performance Testing & Load Validation")
            try:
                perf_results = await self.test_suites[
                    "1.5.28_Performance_Validation"
                ].run_all_performance_tests()
                overall_results["test_suite_results"][
                    "1.5.28_Performance_Validation"
                ] = perf_results
                overall_results["completion_status"][
                    "1.5.28_Performance_Validation"
                ] = "COMPLETED"

                # Update summary
                overall_results["overall_summary"]["total_test_suites"] += 1
                overall_results["overall_summary"][
                    "total_individual_tests"
                ] += perf_results["summary"].get("total_tests", 0)
                overall_results["overall_summary"][
                    "passed_individual_tests"
                ] += perf_results["summary"].get("passed_tests", 0)
                overall_results["overall_summary"][
                    "failed_individual_tests"
                ] += perf_results["summary"].get("failed_tests", 0)

                if perf_results["summary"].get("failed_tests", 0) == 0:
                    overall_results["overall_summary"]["passed_test_suites"] += 1
                else:
                    overall_results["overall_summary"]["failed_test_suites"] += 1

                logger.info(
                    f"✅ Task 1.5.28 completed: {perf_results['summary'].get('passed_tests', 0)}/{perf_results['summary'].get('total_tests', 0)} tests passed"
                )

            except Exception as e:
                logger.error(f"❌ Task 1.5.28 failed: {str(e)}")
                overall_results["completion_status"][
                    "1.5.28_Performance_Validation"
                ] = "FAILED"
                overall_results["overall_summary"]["failed_test_suites"] += 1
                overall_results["test_suite_results"][
                    "1.5.28_Performance_Validation"
                ] = {"error": str(e)}
        else:
            logger.info("⏭️  Skipping Task 1.5.28: Performance tests (disabled)")
            overall_results["completion_status"][
                "1.5.28_Performance_Validation"
            ] = "SKIPPED"

        # Generate recommendations
        overall_results["recommendations"] = self._generate_recommendations(
            overall_results
        )

        return overall_results

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        # Overall success rate
        total_tests = results["overall_summary"]["total_individual_tests"]
        passed_tests = results["overall_summary"]["passed_individual_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        if success_rate >= 95:
            recommendations.append(
                "✅ Excellent test coverage and success rate. Repository layer is production-ready."
            )
        elif success_rate >= 85:
            recommendations.append(
                "⚠️ Good test coverage but some issues found. Review failed tests before production."
            )
        else:
            recommendations.append(
                "❌ Significant issues found. Address failed tests before proceeding."
            )

        # Database availability
        db_results = results["test_suite_results"].get(
            "1.5.26_Database_Integration", {}
        )
        if not db_results.get("database_available", True):
            recommendations.append(
                "🔧 Database not available for testing. Ensure MongoDB is running for full validation."
            )

        # Performance concerns
        perf_results = results["test_suite_results"].get(
            "1.5.28_Performance_Validation", {}
        )
        if perf_results and perf_results.get("summary", {}).get("performance_issues"):
            recommendations.append(
                "⚡ Performance issues detected. Consider optimization before production load."
            )

        # Data consistency
        consistency_results = results["test_suite_results"].get(
            "1.5.27_Data_Consistency", {}
        )
        if consistency_results and consistency_results.get("failed_tests", 0) > 0:
            recommendations.append(
                "🔒 Data consistency issues found. Review entity validation rules."
            )

        return recommendations

    def print_summary_report(self, results: Dict[str, Any]):
        """Print a formatted summary report."""
        print("\n" + "=" * 80)
        print("DAY 7 TESTING & VALIDATION SUMMARY REPORT")
        print("=" * 80)

        print(f"\n📊 OVERALL RESULTS:")
        print(
            f"   Test Suites: {results['overall_summary']['passed_test_suites']}/{results['overall_summary']['total_test_suites']} passed"
        )
        print(
            f"   Individual Tests: {results['overall_summary']['passed_individual_tests']}/{results['overall_summary']['total_individual_tests']} passed"
        )

        if results["overall_summary"]["skipped_individual_tests"] > 0:
            print(
                f"   Skipped Tests: {results['overall_summary']['skipped_individual_tests']}"
            )

        success_rate = (
            (
                results["overall_summary"]["passed_individual_tests"]
                / results["overall_summary"]["total_individual_tests"]
                * 100
            )
            if results["overall_summary"]["total_individual_tests"] > 0
            else 0
        )
        print(f"   Success Rate: {success_rate:.1f}%")

        print(f"\n📋 TASK COMPLETION STATUS:")
        for task, status in results["completion_status"].items():
            status_icon = {
                "COMPLETED": "✅",
                "FAILED": "❌",
                "SKIPPED": "⏭️",
                "NOT_STARTED": "⏸️",
            }
            print(f"   {status_icon.get(status, '❓')} {task}: {status}")

        print(f"\n💡 RECOMMENDATIONS:")
        for recommendation in results["recommendations"]:
            print(f"   {recommendation}")

        print(f"\n🕐 Test completed at: {results['test_run_timestamp']}")
        print("=" * 80)

    def save_results_to_file(
        self, results: Dict[str, Any], filename: Optional[str] = None
    ):
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"day7_test_results_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Test results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results to file: {e}")


async def main():
    """Main function for running Day 7 tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Day 7 Testing & Validation Suite")
    parser.add_argument(
        "--no-performance",
        action="store_true",
        help="Skip performance tests (faster execution)",
    )
    parser.add_argument(
        "--save-results", type=str, help="Save results to specified JSON file"
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Initialize and run test suite
    runner = Day7TestSuiteRunner()

    try:
        print("🚀 Starting Day 7 Testing & Validation Suite...")
        print(
            "   This will validate the Database Layer & Repository Pattern implementation"
        )

        include_performance = not args.no_performance
        if not include_performance:
            print("   (Performance tests disabled for faster execution)")

        results = await runner.run_all_day7_tests(
            include_performance=include_performance
        )

        # Print summary
        runner.print_summary_report(results)

        # Save results if requested
        if args.save_results:
            runner.save_results_to_file(results, args.save_results)

        # Exit with appropriate code
        if results["overall_summary"]["failed_test_suites"] == 0:
            print("\n🎉 All Day 7 objectives completed successfully!")
            sys.exit(0)
        else:
            print(
                f"\n⚠️  {results['overall_summary']['failed_test_suites']} test suite(s) had failures."
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
