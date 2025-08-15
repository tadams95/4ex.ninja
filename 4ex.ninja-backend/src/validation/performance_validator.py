"""
Performance Validator

This module provides performance comparison and validation capabilities
to analyze the impact of infrastructure optimizations on trading performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class PerformanceValidator:
    """
    Performance validator for comparing historical and current results.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        # Load historical benchmarks if they exist
        self.historical_benchmarks = self.load_historical_benchmarks()

    def load_historical_benchmarks(self) -> Dict:
        """
        Load historical benchmark data for comparison.

        Returns:
            Dictionary of historical performance data
        """
        try:
            benchmark_file = self.reports_dir / "historical_benchmarks.json"

            if benchmark_file.exists():
                with open(benchmark_file, "r") as f:
                    benchmarks = json.load(f)
                self.logger.info(
                    f"Loaded historical benchmarks for {len(benchmarks)} strategies"
                )
                return benchmarks
            else:
                self.logger.warning("No historical benchmarks found")
                return {}

        except Exception as e:
            self.logger.error(f"Failed to load historical benchmarks: {str(e)}")
            return {}

    def save_historical_benchmarks(self, benchmarks: Dict) -> None:
        """
        Save historical benchmarks for future comparison.

        Args:
            benchmarks: Dictionary of benchmark data
        """
        try:
            benchmark_file = self.reports_dir / "historical_benchmarks.json"

            with open(benchmark_file, "w") as f:
                json.dump(benchmarks, f, indent=2, default=str)

            self.logger.info(
                f"Saved historical benchmarks for {len(benchmarks)} strategies"
            )

        except Exception as e:
            self.logger.error(f"Failed to save historical benchmarks: {str(e)}")

    def generate_comparison_report(
        self, historical_results: Dict, current_results: Dict
    ) -> Dict:
        """
        Compare pre/post optimization performance and identify gaps.

        Args:
            historical_results: Historical performance data
            current_results: Current validation results

        Returns:
            Comprehensive comparison analysis
        """
        comparison = {
            "performance_change": {},
            "risk_metrics_change": {},
            "infrastructure_improvements": {},
            "recommendations": [],
            "overall_assessment": "UNKNOWN",
            "critical_issues": [],
            "comparison_timestamp": datetime.now().isoformat(),
        }

        try:
            # Performance comparison
            if historical_results and current_results:
                comparison["performance_change"] = self._calculate_performance_changes(
                    historical_results, current_results
                )

                # Risk metrics comparison
                comparison["risk_metrics_change"] = self._calculate_risk_changes(
                    historical_results, current_results
                )

                # Generate actionable recommendations
                comparison["recommendations"] = self.generate_recommendations(
                    comparison
                )

                # Overall assessment
                comparison["overall_assessment"] = self._assess_overall_performance(
                    comparison
                )

                # Identify critical issues
                comparison["critical_issues"] = self._identify_critical_issues(
                    comparison
                )

            # Save comparison report
            self._save_comparison_report(comparison)

            return comparison

        except Exception as e:
            self.logger.error(f"Failed to generate comparison report: {str(e)}")
            comparison["error"] = str(e)
            return comparison

    def _calculate_performance_changes(self, historical: Dict, current: Dict) -> Dict:
        """Calculate performance metric changes."""
        changes = {}

        # Define metrics to compare
        metrics_to_compare = [
            "total_pips",
            "win_rate",
            "profit_factor",
            "max_drawdown",
            "sharpe_ratio",
            "total_trades",
        ]

        for strategy_key in current.keys():
            if strategy_key not in historical:
                continue

            hist_data = historical[strategy_key]
            curr_data = current[strategy_key]

            if "error" in hist_data or "error" in curr_data:
                continue

            strategy_changes = {}

            for metric in metrics_to_compare:
                if metric in hist_data and metric in curr_data:
                    hist_value = hist_data[metric]
                    curr_value = curr_data[metric]

                    if hist_value != 0:
                        pct_change = ((curr_value - hist_value) / abs(hist_value)) * 100
                    else:
                        pct_change = 0 if curr_value == 0 else float("inf")

                    strategy_changes[metric] = {
                        "historical": hist_value,
                        "current": curr_value,
                        "absolute_change": curr_value - hist_value,
                        "percentage_change": pct_change,
                    }

            changes[strategy_key] = strategy_changes

        return changes

    def _calculate_risk_changes(self, historical: Dict, current: Dict) -> Dict:
        """Calculate risk metric changes."""
        risk_changes = {}

        risk_metrics = ["max_drawdown", "sharpe_ratio", "worst_trade_pips"]

        for strategy_key in current.keys():
            if strategy_key not in historical:
                continue

            hist_data = historical[strategy_key]
            curr_data = current[strategy_key]

            if "error" in hist_data or "error" in curr_data:
                continue

            strategy_risk = {}

            for metric in risk_metrics:
                if metric in hist_data and metric in curr_data:
                    hist_value = hist_data[metric]
                    curr_value = curr_data[metric]

                    strategy_risk[metric] = {
                        "historical": hist_value,
                        "current": curr_value,
                        "risk_increased": self._is_risk_increased(
                            metric, hist_value, curr_value
                        ),
                    }

            risk_changes[strategy_key] = strategy_risk

        return risk_changes

    def _is_risk_increased(
        self, metric: str, historical: float, current: float
    ) -> bool:
        """Determine if risk has increased for a given metric."""
        if metric == "max_drawdown" or metric == "worst_trade_pips":
            return current > historical  # Higher is worse
        elif metric == "sharpe_ratio":
            return current < historical  # Lower is worse
        else:
            return False

    def _assess_overall_performance(self, comparison: Dict) -> str:
        """Assess overall performance based on comparison data."""
        performance_changes = comparison.get("performance_change", {})
        risk_changes = comparison.get("risk_metrics_change", {})

        if not performance_changes:
            return "INSUFFICIENT_DATA"

        # Count positive and negative changes
        positive_changes = 0
        negative_changes = 0
        total_strategies = 0

        for strategy_data in performance_changes.values():
            total_strategies += 1

            # Check key metrics
            if "total_pips" in strategy_data:
                if strategy_data["total_pips"]["percentage_change"] > 0:
                    positive_changes += 1
                else:
                    negative_changes += 1

        if total_strategies == 0:
            return "NO_DATA"

        positive_ratio = positive_changes / total_strategies

        if positive_ratio >= 0.7:
            return "IMPROVED"
        elif positive_ratio >= 0.4:
            return "MIXED"
        else:
            return "DEGRADED"

    def _identify_critical_issues(self, comparison: Dict) -> List[str]:
        """Identify critical performance issues."""
        issues = []

        performance_changes = comparison.get("performance_change", {})
        risk_changes = comparison.get("risk_metrics_change", {})

        # Check for critical performance degradation
        for strategy, changes in performance_changes.items():
            if "total_pips" in changes:
                pct_change = changes["total_pips"]["percentage_change"]
                if pct_change < -50:
                    issues.append(
                        f"CRITICAL: {strategy} total pips dropped by {pct_change:.1f}%"
                    )

            if "win_rate" in changes:
                pct_change = changes["win_rate"]["percentage_change"]
                if pct_change < -25:
                    issues.append(
                        f"WARNING: {strategy} win rate dropped by {pct_change:.1f}%"
                    )

        # Check for increased risk
        for strategy, risk_data in risk_changes.items():
            if "max_drawdown" in risk_data:
                if risk_data["max_drawdown"]["risk_increased"]:
                    historical = risk_data["max_drawdown"]["historical"]
                    current = risk_data["max_drawdown"]["current"]
                    increase = ((current - historical) / historical) * 100
                    if increase > 50:
                        issues.append(
                            f"CRITICAL: {strategy} max drawdown increased by {increase:.1f}%"
                        )

        return issues

    def generate_recommendations(self, comparison_data: Dict) -> List[str]:
        """
        Generate actionable recommendations based on analysis.

        Args:
            comparison_data: Performance comparison data

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        performance_changes = comparison_data.get("performance_change", {})
        risk_changes = comparison_data.get("risk_metrics_change", {})

        # Performance-based recommendations
        for strategy, changes in performance_changes.items():
            if "win_rate" in changes:
                pct_change = changes["win_rate"]["percentage_change"]
                if pct_change < -10:
                    recommendations.append(
                        f"INVESTIGATE: {strategy} win rate decreased by {pct_change:.1f}% - "
                        "review parameter changes and market conditions"
                    )

            if "profit_factor" in changes:
                pct_change = changes["profit_factor"]["percentage_change"]
                if pct_change < -20:
                    recommendations.append(
                        f"REVIEW: {strategy} profit factor declined by {pct_change:.1f}% - "
                        "consider reverting recent parameter changes"
                    )

        # Risk-based recommendations
        for strategy, risk_data in risk_changes.items():
            if (
                "max_drawdown" in risk_data
                and risk_data["max_drawdown"]["risk_increased"]
            ):
                recommendations.append(
                    f"RISK ALERT: {strategy} maximum drawdown increased - "
                    "implement stricter risk management"
                )

        # General recommendations
        overall_assessment = comparison_data.get("overall_assessment", "UNKNOWN")

        if overall_assessment == "DEGRADED":
            recommendations.append(
                "URGENT: Overall performance has degraded - conduct comprehensive review of all changes"
            )
        elif overall_assessment == "MIXED":
            recommendations.append(
                "REVIEW: Mixed performance results - analyze individual strategy changes"
            )

        return recommendations

    def validate_infrastructure_improvements(self, redis_metrics: Dict) -> Dict:
        """
        Validate that infrastructure optimizations are delivering expected benefits.

        Args:
            redis_metrics: Redis performance metrics

        Returns:
            Infrastructure validation results
        """
        validation_results = {
            "cache_performance": "UNKNOWN",
            "latency_improvements": "UNKNOWN",
            "reliability_score": 0.0,
            "optimization_effectiveness": "UNKNOWN",
            "recommendations": [],
        }

        try:
            # Validate cache performance
            cache_hit_ratio = redis_metrics.get("cache_hit_ratio", 0)
            if cache_hit_ratio > 0.95:
                validation_results["cache_performance"] = "EXCELLENT"
            elif cache_hit_ratio > 0.90:
                validation_results["cache_performance"] = "GOOD"
            elif cache_hit_ratio > 0.75:
                validation_results["cache_performance"] = "ACCEPTABLE"
            else:
                validation_results["cache_performance"] = "NEEDS_IMPROVEMENT"
                validation_results["recommendations"].append(
                    f"Cache hit ratio is {cache_hit_ratio:.1%} - investigate cache effectiveness"
                )

            # Validate latency improvements
            avg_latency = redis_metrics.get("average_latency_ms", 1000)
            if avg_latency < 50:
                validation_results["latency_improvements"] = "EXCELLENT"
            elif avg_latency < 100:
                validation_results["latency_improvements"] = "GOOD"
            elif avg_latency < 250:
                validation_results["latency_improvements"] = "ACCEPTABLE"
            else:
                validation_results["latency_improvements"] = "NEEDS_IMPROVEMENT"
                validation_results["recommendations"].append(
                    f"Average latency is {avg_latency:.1f}ms - investigate performance bottlenecks"
                )

            # Calculate reliability score
            uptime = redis_metrics.get("uptime_percentage", 0)
            error_rate = redis_metrics.get("error_rate", 1.0)

            reliability_score = (uptime / 100) * (1 - error_rate)
            validation_results["reliability_score"] = reliability_score

            if reliability_score < 0.95:
                validation_results["recommendations"].append(
                    f"Reliability score is {reliability_score:.1%} - improve error handling"
                )

            # Overall optimization effectiveness
            if (
                validation_results["cache_performance"] in ["EXCELLENT", "GOOD"]
                and validation_results["latency_improvements"] in ["EXCELLENT", "GOOD"]
                and reliability_score > 0.95
            ):
                validation_results["optimization_effectiveness"] = "SUCCESSFUL"
            elif (
                validation_results["cache_performance"] != "NEEDS_IMPROVEMENT"
                and validation_results["latency_improvements"] != "NEEDS_IMPROVEMENT"
            ):
                validation_results["optimization_effectiveness"] = "PARTIAL"
            else:
                validation_results["optimization_effectiveness"] = "INSUFFICIENT"

        except Exception as e:
            self.logger.error(f"Infrastructure validation failed: {str(e)}")
            validation_results["error"] = str(e)

        return validation_results

    def _save_comparison_report(self, comparison: Dict) -> None:
        """Save comparison report to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_comparison_{timestamp}.json"
            filepath = self.reports_dir / filename

            with open(filepath, "w") as f:
                json.dump(comparison, f, indent=2, default=str)

            self.logger.info(f"Comparison report saved to {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save comparison report: {str(e)}")

    def create_performance_dashboard(self, comparison_data: Dict) -> str:
        """
        Create a visual performance dashboard.

        Args:
            comparison_data: Performance comparison data

        Returns:
            Path to generated dashboard image
        """
        try:
            # Set up the plot
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(
                "Performance Validation Dashboard", fontsize=16, fontweight="bold"
            )

            performance_changes = comparison_data.get("performance_change", {})

            if not performance_changes:
                # Create placeholder plot
                axes[0, 0].text(
                    0.5,
                    0.5,
                    "No Data Available",
                    ha="center",
                    va="center",
                    transform=axes[0, 0].transAxes,
                )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = self.reports_dir / f"dashboard_{timestamp}.png"
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close()
                return str(filepath)

            # Extract data for visualization
            strategies = list(performance_changes.keys())
            pips_changes = []
            win_rate_changes = []
            drawdown_changes = []
            trade_count_changes = []

            for strategy in strategies:
                data = performance_changes[strategy]

                pips_changes.append(
                    data.get("total_pips", {}).get("percentage_change", 0)
                )
                win_rate_changes.append(
                    data.get("win_rate", {}).get("percentage_change", 0)
                )
                drawdown_changes.append(
                    data.get("max_drawdown", {}).get("percentage_change", 0)
                )
                trade_count_changes.append(
                    data.get("total_trades", {}).get("percentage_change", 0)
                )

            # Plot 1: Pips Performance Change
            bars1 = axes[0, 0].bar(
                range(len(strategies)),
                pips_changes,
                color=["green" if x > 0 else "red" for x in pips_changes],
            )
            axes[0, 0].set_title("Total Pips Change (%)")
            axes[0, 0].set_xticks(range(len(strategies)))
            axes[0, 0].set_xticklabels(strategies, rotation=45, ha="right")
            axes[0, 0].axhline(y=0, color="black", linestyle="-", alpha=0.3)
            axes[0, 0].grid(True, alpha=0.3)

            # Plot 2: Win Rate Change
            bars2 = axes[0, 1].bar(
                range(len(strategies)),
                win_rate_changes,
                color=["green" if x > 0 else "red" for x in win_rate_changes],
            )
            axes[0, 1].set_title("Win Rate Change (%)")
            axes[0, 1].set_xticks(range(len(strategies)))
            axes[0, 1].set_xticklabels(strategies, rotation=45, ha="right")
            axes[0, 1].axhline(y=0, color="black", linestyle="-", alpha=0.3)
            axes[0, 1].grid(True, alpha=0.3)

            # Plot 3: Drawdown Change (negative is good)
            bars3 = axes[1, 0].bar(
                range(len(strategies)),
                drawdown_changes,
                color=["red" if x > 0 else "green" for x in drawdown_changes],
            )
            axes[1, 0].set_title("Max Drawdown Change (% - Lower is Better)")
            axes[1, 0].set_xticks(range(len(strategies)))
            axes[1, 0].set_xticklabels(strategies, rotation=45, ha="right")
            axes[1, 0].axhline(y=0, color="black", linestyle="-", alpha=0.3)
            axes[1, 0].grid(True, alpha=0.3)

            # Plot 4: Trade Count Change
            bars4 = axes[1, 1].bar(
                range(len(strategies)),
                trade_count_changes,
                color=[
                    "blue" if abs(x) < 20 else "orange" for x in trade_count_changes
                ],
            )
            axes[1, 1].set_title("Trade Count Change (%)")
            axes[1, 1].set_xticks(range(len(strategies)))
            axes[1, 1].set_xticklabels(strategies, rotation=45, ha="right")
            axes[1, 1].axhline(y=0, color="black", linestyle="-", alpha=0.3)
            axes[1, 1].grid(True, alpha=0.3)

            plt.tight_layout()

            # Save dashboard
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.reports_dir / f"dashboard_{timestamp}.png"
            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close()

            self.logger.info(f"Performance dashboard saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Failed to create performance dashboard: {str(e)}")
            return ""


def main():
    """Main function for performance validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Validation Analysis")
    parser.add_argument(
        "--current-results", help="Path to current validation results JSON"
    )
    parser.add_argument("--historical-results", help="Path to historical results JSON")
    parser.add_argument(
        "--dashboard", action="store_true", help="Generate performance dashboard"
    )

    args = parser.parse_args()

    validator = PerformanceValidator()

    if args.current_results:
        # Load current results
        with open(args.current_results, "r") as f:
            current_results = json.load(f)

        # Load historical results if provided
        historical_results = {}
        if args.historical_results:
            with open(args.historical_results, "r") as f:
                historical_results = json.load(f)
        else:
            historical_results = validator.historical_benchmarks

        # Generate comparison report
        comparison = validator.generate_comparison_report(
            historical_results, current_results
        )

        print("\n=== PERFORMANCE VALIDATION SUMMARY ===")
        print(f"Overall Assessment: {comparison['overall_assessment']}")

        if comparison.get("critical_issues"):
            print("\nCRITICAL ISSUES:")
            for issue in comparison["critical_issues"]:
                print(f"  - {issue}")

        if comparison.get("recommendations"):
            print("\nRECOMMENDATIONS:")
            for rec in comparison["recommendations"][:5]:  # Show first 5
                print(f"  - {rec}")

        # Generate dashboard if requested
        if args.dashboard:
            dashboard_path = validator.create_performance_dashboard(comparison)
            if dashboard_path:
                print(f"\nDashboard saved to: {dashboard_path}")

    else:
        print("Please provide --current-results path to validation results JSON")


if __name__ == "__main__":
    main()
