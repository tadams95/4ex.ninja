#!/usr/bin/env python3
"""
Comprehensive Infrastructure Performance Test Runner

This script runs both Redis and Signal Delivery performance tests
as specified in Phase 1, Step 3 of the Emergency Validation plan.
"""

import asyncio
import json
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.validation.redis_performance_test import RedisPerformanceTest
from src.validation.signal_delivery_test import SignalDeliveryTest

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/infrastructure_test.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class InfrastructurePerformanceTestRunner:
    """
    Comprehensive infrastructure performance test runner.

    Executes both Redis and Signal Delivery tests and provides
    consolidated reporting as specified in Phase 1 Step 3.
    """

    def __init__(self):
        self.logger = logger
        self.test_start_time = None
        self.test_results = {}

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive infrastructure performance tests.

        Returns:
            Dict containing all test results and performance metrics
        """
        self.test_start_time = datetime.now()
        self.logger.info("Starting comprehensive infrastructure performance tests")

        test_results = {
            "test_metadata": {
                "start_time": self.test_start_time.isoformat(),
                "test_type": "infrastructure_performance",
                "phase": "Phase1_Step3",
                "version": "1.0.0",
            },
            "system_info": self.get_system_info(),
            "redis_performance": {},
            "signal_delivery": {},
            "infrastructure_validation": {},
            "performance_summary": {},
            "recommendations": [],
        }

        try:
            # Step 1: Redis Performance Testing
            self.logger.info("Phase 1/3: Running Redis Performance Tests")
            test_results["redis_performance"] = await self.run_redis_tests()

            # Step 2: Signal Delivery Testing
            self.logger.info("Phase 2/3: Running Signal Delivery Tests")
            test_results["signal_delivery"] = await self.run_signal_delivery_tests()

            # Step 3: Infrastructure Validation
            self.logger.info("Phase 3/3: Running Infrastructure Validation")
            test_results["infrastructure_validation"] = (
                self.validate_infrastructure_performance(
                    test_results["redis_performance"], test_results["signal_delivery"]
                )
            )

            # Step 4: Generate Performance Summary and Recommendations
            test_results["performance_summary"] = self.generate_performance_summary(
                test_results
            )
            test_results["recommendations"] = self.generate_recommendations(
                test_results
            )

            # Save comprehensive results
            self.save_comprehensive_results(test_results)

            # Mark test completion
            test_results["test_metadata"]["end_time"] = datetime.now().isoformat()
            test_results["test_metadata"]["duration_seconds"] = (
                datetime.now() - self.test_start_time
            ).total_seconds()

            self.logger.info("Comprehensive infrastructure performance tests completed")
            return test_results

        except Exception as e:
            self.logger.error(f"Infrastructure performance tests failed: {str(e)}")
            test_results["error"] = str(e)
            test_results["test_metadata"]["end_time"] = datetime.now().isoformat()
            return test_results

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for test context."""
        try:
            import psutil
            import platform
            import os

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_usage_percent": psutil.disk_usage("/").percent,
                "load_average": (
                    psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0]
                ),
                "environment_variables": {
                    "redis_configured": bool(os.getenv("REDIS_URL")),
                    "discord_webhook_configured": bool(
                        os.getenv("DISCORD_WEBHOOK_URL")
                    ),
                    "system_status_webhook": bool(
                        os.getenv("DISCORD_WEBHOOK_SYSTEM_STATUS")
                    ),
                },
            }
        except Exception as e:
            self.logger.warning(f"Could not gather complete system info: {str(e)}")
            return {"error": str(e)}

    async def run_redis_tests(self) -> Dict[str, Any]:
        """Run comprehensive Redis performance tests."""
        try:
            redis_tester = RedisPerformanceTest()
            results = redis_tester.run_comprehensive_test()

            # Add Phase 1 specific metrics
            results["phase1_validation"] = {
                "cache_hit_ratio_target": 0.90,  # 90% target from Phase 1
                "latency_target_ms": 100,  # <100ms target from Phase 1
                "uptime_target": 0.95,  # 95% target from Phase 1
                "validation_status": self.validate_redis_performance(results),
            }

            return results

        except Exception as e:
            self.logger.error(f"Redis performance tests failed: {str(e)}")
            return {"error": str(e)}

    async def run_signal_delivery_tests(self) -> Dict[str, Any]:
        """Run comprehensive signal delivery tests."""
        try:
            signal_tester = SignalDeliveryTest()
            results = await signal_tester.run_comprehensive_test()

            # Add Phase 1 specific metrics
            results["phase1_validation"] = {
                "end_to_end_target_ms": 2000,  # <2 seconds target from Phase 1
                "success_rate_target": 0.95,  # 95% target
                "validation_status": self.validate_signal_delivery_performance(results),
            }

            return results

        except Exception as e:
            self.logger.error(f"Signal delivery tests failed: {str(e)}")
            return {"error": str(e)}

    def validate_redis_performance(self, redis_results: Dict) -> str:
        """Validate Redis performance against Phase 1 targets."""
        if "error" in redis_results:
            return "ERROR"

        cache_efficiency = redis_results.get("cache_efficiency", {})
        basic_ops = redis_results.get("basic_operations", {})

        hit_ratio = cache_efficiency.get("hit_ratio", 0)
        avg_latency = basic_ops.get("avg_get_latency_ms", 1000)

        # Check against Phase 1 targets
        if hit_ratio >= 0.95 and avg_latency < 100:
            return "EXCELLENT"
        elif hit_ratio >= 0.90 and avg_latency < 100:
            return "GOOD"
        elif hit_ratio >= 0.85 and avg_latency < 500:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"

    def validate_signal_delivery_performance(self, signal_results: Dict) -> str:
        """Validate signal delivery performance against Phase 1 targets."""
        if "error" in signal_results:
            return "ERROR"

        end_to_end = signal_results.get("end_to_end_timing", {})
        discord_perf = signal_results.get("discord_delivery", {})

        total_latency = end_to_end.get("total_latency_ms", 10000)
        success_rate = end_to_end.get("success_rate", 0)

        # Check against Phase 1 targets
        if total_latency < 2000 and success_rate >= 0.98:
            return "EXCELLENT"
        elif total_latency < 2000 and success_rate >= 0.95:
            return "GOOD"
        elif total_latency < 5000 and success_rate >= 0.90:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"

    def validate_infrastructure_performance(
        self, redis_results: Dict, signal_results: Dict
    ) -> Dict:
        """
        Validate infrastructure performance against Phase 1 success criteria.
        """
        validation = {
            "redis_validation": {},
            "signal_delivery_validation": {},
            "overall_status": "UNKNOWN",
            "critical_issues": [],
            "performance_gaps": [],
            "optimization_effectiveness": "UNKNOWN",
        }

        # Redis Validation
        if "error" not in redis_results:
            cache_eff = redis_results.get("cache_efficiency", {})
            basic_ops = redis_results.get("basic_operations", {})

            validation["redis_validation"] = {
                "cache_hit_ratio": cache_eff.get("hit_ratio", 0),
                "target_hit_ratio": 0.90,
                "hit_ratio_met": cache_eff.get("hit_ratio", 0) >= 0.90,
                "average_latency_ms": basic_ops.get("avg_get_latency_ms", 1000),
                "target_latency_ms": 100,
                "latency_target_met": basic_ops.get("avg_get_latency_ms", 1000) < 100,
                "status": redis_results.get("phase1_validation", {}).get(
                    "validation_status", "UNKNOWN"
                ),
            }

        # Signal Delivery Validation
        if "error" not in signal_results:
            end_to_end = signal_results.get("end_to_end_timing", {})

            validation["signal_delivery_validation"] = {
                "total_latency_ms": end_to_end.get("total_latency_ms", 10000),
                "target_latency_ms": 2000,
                "latency_target_met": end_to_end.get("total_latency_ms", 10000) < 2000,
                "success_rate": end_to_end.get("success_rate", 0),
                "target_success_rate": 0.95,
                "success_rate_met": end_to_end.get("success_rate", 0) >= 0.95,
                "status": signal_results.get("phase1_validation", {}).get(
                    "validation_status", "UNKNOWN"
                ),
            }

        # Overall Status Assessment
        redis_status = validation["redis_validation"].get("status", "UNKNOWN")
        signal_status = validation["signal_delivery_validation"].get(
            "status", "UNKNOWN"
        )

        if redis_status in ["EXCELLENT", "GOOD"] and signal_status in [
            "EXCELLENT",
            "GOOD",
        ]:
            validation["overall_status"] = "PASSED"
            validation["optimization_effectiveness"] = "CONFIRMED"
        elif redis_status == "ACCEPTABLE" and signal_status == "ACCEPTABLE":
            validation["overall_status"] = "PASSED_WITH_WARNINGS"
            validation["optimization_effectiveness"] = "PARTIAL"
        else:
            validation["overall_status"] = "NEEDS_IMPROVEMENT"
            validation["optimization_effectiveness"] = "INSUFFICIENT"

        # Identify critical issues
        if not validation["redis_validation"].get("hit_ratio_met", False):
            validation["critical_issues"].append(
                "Redis cache hit ratio below 90% target"
            )

        if not validation["redis_validation"].get("latency_target_met", False):
            validation["critical_issues"].append("Redis latency exceeds 100ms target")

        if not validation["signal_delivery_validation"].get(
            "latency_target_met", False
        ):
            validation["critical_issues"].append(
                "Signal delivery latency exceeds 2-second target"
            )

        if not validation["signal_delivery_validation"].get("success_rate_met", False):
            validation["critical_issues"].append(
                "Signal delivery success rate below 95% target"
            )

        return validation

    def generate_performance_summary(self, test_results: Dict) -> Dict:
        """Generate comprehensive performance summary."""
        summary = {
            "test_completion_status": (
                "COMPLETED" if "error" not in test_results else "FAILED"
            ),
            "infrastructure_readiness": "UNKNOWN",
            "performance_score": 0,
            "key_metrics": {},
            "bottlenecks_identified": [],
            "optimization_opportunities": [],
        }

        try:
            redis_results = test_results.get("redis_performance", {})
            signal_results = test_results.get("signal_delivery", {})
            validation = test_results.get("infrastructure_validation", {})

            # Key Metrics Summary
            if "error" not in redis_results:
                cache_eff = redis_results.get("cache_efficiency", {})
                basic_ops = redis_results.get("basic_operations", {})

                summary["key_metrics"]["redis_cache_hit_ratio"] = cache_eff.get(
                    "hit_ratio", 0
                )
                summary["key_metrics"]["redis_avg_latency_ms"] = basic_ops.get(
                    "avg_get_latency_ms", 0
                )
                summary["key_metrics"]["redis_ops_per_second"] = basic_ops.get(
                    "get_operations_per_second", 0
                )

            if "error" not in signal_results:
                end_to_end = signal_results.get("end_to_end_timing", {})

                summary["key_metrics"]["signal_total_latency_ms"] = end_to_end.get(
                    "total_latency_ms", 0
                )
                summary["key_metrics"]["signal_success_rate"] = end_to_end.get(
                    "success_rate", 0
                )
                summary["key_metrics"]["discord_delivery_ms"] = end_to_end.get(
                    "discord_delivery_ms", 0
                )

            # Performance Score Calculation (0-100)
            score = 0

            # Redis scoring (40 points max)
            hit_ratio = summary["key_metrics"].get("redis_cache_hit_ratio", 0)
            redis_latency = summary["key_metrics"].get("redis_avg_latency_ms", 1000)

            score += min(40, hit_ratio * 40)  # Hit ratio contribution
            score += min(10, max(0, 10 - (redis_latency / 10)))  # Latency contribution

            # Signal delivery scoring (40 points max)
            signal_success = summary["key_metrics"].get("signal_success_rate", 0)
            signal_latency = summary["key_metrics"].get(
                "signal_total_latency_ms", 10000
            )

            score += min(30, signal_success * 30)  # Success rate contribution
            score += min(
                20, max(0, 20 - (signal_latency / 100))
            )  # Latency contribution

            summary["performance_score"] = min(100, max(0, score))

            # Infrastructure Readiness Assessment
            overall_status = validation.get("overall_status", "UNKNOWN")
            if overall_status == "PASSED":
                summary["infrastructure_readiness"] = "PRODUCTION_READY"
            elif overall_status == "PASSED_WITH_WARNINGS":
                summary["infrastructure_readiness"] = "ACCEPTABLE_WITH_MONITORING"
            else:
                summary["infrastructure_readiness"] = "NEEDS_IMPROVEMENT"

            # Identify bottlenecks
            if redis_latency > 100:
                summary["bottlenecks_identified"].append("Redis latency exceeds target")

            if hit_ratio < 0.90:
                summary["bottlenecks_identified"].append(
                    "Redis cache efficiency below target"
                )

            if summary["key_metrics"].get("signal_total_latency_ms", 0) > 2000:
                summary["bottlenecks_identified"].append(
                    "Signal delivery latency exceeds target"
                )

        except Exception as e:
            self.logger.error(f"Performance summary generation failed: {str(e)}")
            summary["error"] = str(e)

        return summary

    def generate_recommendations(self, test_results: Dict) -> list:
        """Generate actionable recommendations based on test results."""
        recommendations = []

        try:
            redis_results = test_results.get("redis_performance", {})
            signal_results = test_results.get("signal_delivery", {})
            validation = test_results.get("infrastructure_validation", {})
            summary = test_results.get("performance_summary", {})

            # Redis-specific recommendations
            if "error" not in redis_results:
                cache_eff = redis_results.get("cache_efficiency", {})
                basic_ops = redis_results.get("basic_operations", {})

                if cache_eff.get("hit_ratio", 0) < 0.90:
                    recommendations.append(
                        {
                            "category": "REDIS_OPTIMIZATION",
                            "priority": "HIGH",
                            "issue": "Cache hit ratio below 90% target",
                            "recommendation": "Review cache key TTL settings and cache warming strategies",
                            "impact": "Improved response times and reduced API calls",
                        }
                    )

                if basic_ops.get("avg_get_latency_ms", 1000) > 100:
                    recommendations.append(
                        {
                            "category": "REDIS_PERFORMANCE",
                            "priority": "HIGH",
                            "issue": "Redis latency exceeds 100ms target",
                            "recommendation": "Check Redis memory usage, network latency, and consider Redis optimization",
                            "impact": "Faster signal generation and delivery",
                        }
                    )

            # Signal delivery recommendations
            if "error" not in signal_results:
                end_to_end = signal_results.get("end_to_end_timing", {})

                if end_to_end.get("total_latency_ms", 10000) > 2000:
                    recommendations.append(
                        {
                            "category": "SIGNAL_DELIVERY",
                            "priority": "HIGH",
                            "issue": "End-to-end signal delivery exceeds 2-second target",
                            "recommendation": "Optimize signal generation pipeline and Discord webhook performance",
                            "impact": "Faster signal delivery to users",
                        }
                    )

                if end_to_end.get("success_rate", 0) < 0.95:
                    recommendations.append(
                        {
                            "category": "RELIABILITY",
                            "priority": "CRITICAL",
                            "issue": "Signal delivery success rate below 95%",
                            "recommendation": "Implement retry logic and error handling improvements",
                            "impact": "Improved signal delivery reliability",
                        }
                    )

            # Infrastructure optimization recommendations
            overall_status = validation.get("overall_status", "UNKNOWN")
            if overall_status == "NEEDS_IMPROVEMENT":
                recommendations.append(
                    {
                        "category": "INFRASTRUCTURE",
                        "priority": "HIGH",
                        "issue": "Infrastructure performance below Phase 1 targets",
                        "recommendation": "Review and implement optimization strategies before proceeding to Phase 2",
                        "impact": "System reliability and performance validation",
                    }
                )

            # Performance score based recommendations
            perf_score = summary.get("performance_score", 0)
            if perf_score < 70:
                recommendations.append(
                    {
                        "category": "GENERAL_OPTIMIZATION",
                        "priority": "MEDIUM",
                        "issue": f"Overall performance score is {perf_score:.1f}/100",
                        "recommendation": "Focus on highest-impact optimizations identified in test results",
                        "impact": "Overall system performance improvement",
                    }
                )

        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {str(e)}")
            recommendations.append(
                {
                    "category": "ERROR",
                    "priority": "HIGH",
                    "issue": "Failed to generate complete recommendations",
                    "recommendation": f"Review test results manually: {str(e)}",
                    "impact": "Unknown",
                }
            )

        return recommendations

    def save_comprehensive_results(self, results: Dict) -> None:
        """Save comprehensive test results."""
        try:
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"infrastructure_performance_test_{timestamp}.json"
            filepath = reports_dir / filename

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)

            # Also save a summary report
            summary_filename = f"infrastructure_test_summary_{timestamp}.json"
            summary_filepath = reports_dir / summary_filename

            summary_data = {
                "test_metadata": results.get("test_metadata", {}),
                "performance_summary": results.get("performance_summary", {}),
                "infrastructure_validation": results.get(
                    "infrastructure_validation", {}
                ),
                "recommendations": results.get("recommendations", []),
            }

            with open(summary_filepath, "w") as f:
                json.dump(summary_data, f, indent=2, default=str)

            self.logger.info(f"Comprehensive test results saved to {filepath}")
            self.logger.info(f"Test summary saved to {summary_filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save test results: {str(e)}")

    def print_test_summary(self, results: Dict) -> None:
        """Print formatted test summary to console."""
        print(f"\n{'='*80}")
        print("INFRASTRUCTURE PERFORMANCE TEST RESULTS - PHASE 1 STEP 3")
        print(f"{'='*80}")

        # Test metadata
        metadata = results.get("test_metadata", {})
        print(f"\nTest Start: {metadata.get('start_time', 'Unknown')}")
        print(f"Test Duration: {metadata.get('duration_seconds', 0):.1f} seconds")

        # Performance summary
        summary = results.get("performance_summary", {})
        print(f"\nPerformance Score: {summary.get('performance_score', 0):.1f}/100")
        print(
            f"Infrastructure Readiness: {summary.get('infrastructure_readiness', 'UNKNOWN')}"
        )

        # Key metrics
        metrics = summary.get("key_metrics", {})
        if metrics:
            print(f"\nKey Metrics:")
            print(
                f"  Redis Cache Hit Ratio: {metrics.get('redis_cache_hit_ratio', 0):.1%}"
            )
            print(
                f"  Redis Average Latency: {metrics.get('redis_avg_latency_ms', 0):.1f}ms"
            )
            print(
                f"  Signal Total Latency: {metrics.get('signal_total_latency_ms', 0):.1f}ms"
            )
            print(f"  Signal Success Rate: {metrics.get('signal_success_rate', 0):.1%}")

        # Validation status
        validation = results.get("infrastructure_validation", {})
        print(f"\nValidation Status: {validation.get('overall_status', 'UNKNOWN')}")

        critical_issues = validation.get("critical_issues", [])
        if critical_issues:
            print(f"\nCritical Issues:")
            for issue in critical_issues:
                print(f"  - {issue}")

        # Recommendations
        recommendations = results.get("recommendations", [])
        high_priority_recs = [r for r in recommendations if r.get("priority") == "HIGH"]
        if high_priority_recs:
            print(f"\nHigh Priority Recommendations:")
            for rec in high_priority_recs[:3]:  # Show top 3
                print(f"  - {rec.get('recommendation', 'Unknown')}")

        print(f"\n{'='*80}")


# CLI interface
async def main():
    """Run infrastructure performance tests from command line."""
    print("Starting Phase 1 Step 3: Infrastructure Performance Testing")
    print("This test validates Redis and Signal Delivery performance optimizations")
    print("-" * 60)

    runner = InfrastructurePerformanceTestRunner()

    try:
        results = await runner.run_comprehensive_tests()
        runner.print_test_summary(results)

        # Exit code based on results
        validation = results.get("infrastructure_validation", {})
        overall_status = validation.get("overall_status", "UNKNOWN")

        if overall_status == "PASSED":
            print("\n✅ Infrastructure performance tests PASSED")
            sys.exit(0)
        elif overall_status == "PASSED_WITH_WARNINGS":
            print("\n⚠️  Infrastructure performance tests PASSED WITH WARNINGS")
            sys.exit(0)
        else:
            print("\n❌ Infrastructure performance tests FAILED")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
