#!/usr/bin/env python3
"""
Enhanced Daily Strategy Parameter Optimization Runner

This is the master optimization runner that executes all parameter optimization
experiments for the Enhanced Daily Strategy in sequence.

Optimization Pipeline:
1. EMA Period Optimization (baseline improvement)
2. RSI Threshold Optimization (signal quality improvement)
3. Session Timing Optimization (trade timing improvement)

Each optimization builds on the previous results to create the best possible
Enhanced Daily Strategy configuration.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json

# Add backend directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import optimization modules
try:
    from ema_period_optimization import EMAOptimizer
    from rsi_threshold_optimization import RSIOptimizer
    from session_timing_optimization import SessionTimingOptimizer
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all optimization modules are in the same directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MasterOptimizationRunner:
    """Master runner for all Enhanced Daily Strategy parameter optimizations."""

    def __init__(self, initial_balance: float = 100000):
        self.initial_balance = initial_balance
        self.target_pairs = ["USD_JPY", "GBP_JPY", "EUR_JPY", "AUD_JPY"]

        # Initialize optimizers
        self.ema_optimizer = EMAOptimizer(initial_balance)
        self.rsi_optimizer = RSIOptimizer(initial_balance)
        self.session_optimizer = SessionTimingOptimizer(initial_balance)

        # Store all optimization results
        self.all_results = {}

        # Current baseline performance (from Phase 1 results)
        self.baseline_performance = {
            "USD_JPY": {"win_rate": 57.69, "trades": 26, "return_pct": 0.23},
            "GBP_JPY": {"win_rate": 36.84, "trades": 38, "return_pct": -0.26},
            "EUR_JPY": {"win_rate": 0.0, "trades": 1, "return_pct": -0.01},
            "AUD_JPY": {"win_rate": 0.0, "trades": 0, "return_pct": 0.0},
        }

        # Optimization targets
        self.optimization_targets = {
            "USD_JPY": {
                "target_win_rate": 55.0,  # Maintain high performance
                "target_trades": 30,  # Slight increase in frequency
                "priority": "maintain_excellence",
            },
            "GBP_JPY": {
                "target_win_rate": 45.0,  # Major improvement from 36.84%
                "target_trades": 40,  # Maintain frequency
                "priority": "improve_performance",
            },
            "EUR_JPY": {
                "target_win_rate": 40.0,  # Establish decent performance
                "target_trades": 15,  # Generate meaningful signals
                "priority": "generate_signals",
            },
            "AUD_JPY": {
                "target_win_rate": 35.0,  # Conservative start
                "target_trades": 10,  # Enable any trading
                "priority": "enable_trading",
            },
        }

    def run_complete_optimization_pipeline(self) -> Dict:
        """Run the complete optimization pipeline for all parameters."""
        logger.info("=" * 80)
        logger.info("ENHANCED DAILY STRATEGY - COMPLETE PARAMETER OPTIMIZATION")
        logger.info("=" * 80)
        logger.info("Pipeline: EMA → RSI → Session Timing")
        logger.info(f"Target Pairs: {', '.join(self.target_pairs)}")
        logger.info(f"Starting Balance: ${self.initial_balance:,.2f}")
        logger.info("=" * 80)

        pipeline_start = datetime.now(timezone.utc)

        # Phase 1: EMA Period Optimization
        logger.info("\n🔧 PHASE 1: EMA PERIOD OPTIMIZATION")
        logger.info("-" * 50)
        ema_results = self._run_ema_optimization()

        # Phase 2: RSI Threshold Optimization
        logger.info("\n🎯 PHASE 2: RSI THRESHOLD OPTIMIZATION")
        logger.info("-" * 50)
        rsi_results = self._run_rsi_optimization()

        # Phase 3: Session Timing Optimization
        logger.info("\n⏰ PHASE 3: SESSION TIMING OPTIMIZATION")
        logger.info("-" * 50)
        session_results = self._run_session_optimization()

        # Compile final results
        pipeline_end = datetime.now(timezone.utc)
        pipeline_duration = (pipeline_end - pipeline_start).total_seconds()

        final_results = {
            "optimization_pipeline": {
                "start_time": pipeline_start.isoformat(),
                "end_time": pipeline_end.isoformat(),
                "duration_seconds": round(pipeline_duration, 2),
                "duration_minutes": round(pipeline_duration / 60, 2),
                "status": "completed",
            },
            "baseline_performance": self.baseline_performance,
            "optimization_targets": self.optimization_targets,
            "phase_1_ema_optimization": ema_results,
            "phase_2_rsi_optimization": rsi_results,
            "phase_3_session_optimization": session_results,
            "comprehensive_summary": self._generate_comprehensive_summary(
                ema_results, rsi_results, session_results
            ),
        }

        # Save comprehensive results
        output_file = self._save_comprehensive_results(final_results)

        # Print final summary
        self._print_optimization_summary(final_results)

        return final_results

    def _run_ema_optimization(self) -> Dict:
        """Run EMA period optimization with error handling."""
        try:
            logger.info("Starting EMA period optimization...")
            results = self.ema_optimizer.run_comprehensive_ema_optimization()

            # Log key findings
            for pair in self.target_pairs:
                if pair in results.get("detailed_results", {}):
                    pair_result = results["detailed_results"][pair]
                    if "error" not in pair_result and pair_result.get(
                        "best_parameters"
                    ):
                        best = pair_result["best_parameters"]
                        logger.info(
                            f"  ✅ {pair}: EMA {best['ema_fast']}/{best['ema_slow']} "
                            f"- {best['win_rate']}% win rate, {best['total_trades']} trades"
                        )
                    else:
                        logger.warning(f"  ❌ {pair}: EMA optimization failed")

            return results

        except Exception as e:
            logger.error(f"EMA optimization failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _run_rsi_optimization(self) -> Dict:
        """Run RSI threshold optimization with error handling."""
        try:
            logger.info("Starting RSI threshold optimization...")
            results = self.rsi_optimizer.run_comprehensive_rsi_optimization()

            # Log key findings
            for pair in self.target_pairs:
                if pair in results.get("detailed_results", {}):
                    pair_result = results["detailed_results"][pair]
                    if "error" not in pair_result and pair_result.get(
                        "best_parameters"
                    ):
                        best = pair_result["best_parameters"]
                        logger.info(
                            f"  ✅ {pair}: RSI {best['rsi_oversold']}/{best['rsi_overbought']} "
                            f"- {best['win_rate']}% win rate, {best['total_trades']} trades"
                        )
                    else:
                        logger.warning(f"  ❌ {pair}: RSI optimization failed")

            return results

        except Exception as e:
            logger.error(f"RSI optimization failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _run_session_optimization(self) -> Dict:
        """Run session timing optimization with error handling."""
        try:
            logger.info("Starting session timing optimization...")
            results = self.session_optimizer.run_comprehensive_session_optimization()

            # Log key findings
            for pair in self.target_pairs:
                if pair in results.get("detailed_results", {}):
                    pair_result = results["detailed_results"][pair]
                    if "error" not in pair_result and pair_result.get(
                        "best_session_config"
                    ):
                        best = pair_result["best_session_config"]
                        logger.info(
                            f"  ✅ {pair}: {best['session_name']} ({best['session_window']}) "
                            f"- {best['win_rate']}% win rate, {best['total_trades']} trades"
                        )
                    else:
                        logger.warning(f"  ❌ {pair}: Session optimization failed")

            return results

        except Exception as e:
            logger.error(f"Session optimization failed: {e}")
            return {"error": str(e), "status": "failed"}

    def _generate_comprehensive_summary(
        self, ema_results: Dict, rsi_results: Dict, session_results: Dict
    ) -> Dict:
        """Generate comprehensive summary of all optimizations."""
        summary = {
            "optimization_success_rate": {},
            "performance_improvements": {},
            "recommended_implementations": {},
            "overall_strategy_impact": {},
        }

        # Analyze success rates
        successful_optimizations = 0
        total_optimizations = 0

        for pair in self.target_pairs:
            pair_summary = {
                "baseline": self.baseline_performance.get(pair, {}),
                "target": self.optimization_targets.get(pair, {}),
                "optimized_parameters": {},
                "performance_improvements": {},
                "implementation_recommendation": "evaluate",
            }

            # Extract best parameters from each optimization
            total_optimizations += 3  # 3 optimization types per pair

            # EMA optimization results
            if (
                ema_results.get("detailed_results", {})
                .get(pair, {})
                .get("best_parameters")
            ):
                ema_best = ema_results["detailed_results"][pair]["best_parameters"]
                pair_summary["optimized_parameters"]["ema"] = {
                    "fast": ema_best["ema_fast"],
                    "slow": ema_best["ema_slow"],
                    "win_rate": ema_best["win_rate"],
                    "trades": ema_best["total_trades"],
                }
                successful_optimizations += 1

            # RSI optimization results
            if (
                rsi_results.get("detailed_results", {})
                .get(pair, {})
                .get("best_parameters")
            ):
                rsi_best = rsi_results["detailed_results"][pair]["best_parameters"]
                pair_summary["optimized_parameters"]["rsi"] = {
                    "oversold": rsi_best["rsi_oversold"],
                    "overbought": rsi_best["rsi_overbought"],
                    "neutral_range": rsi_best["rsi_neutral_range"],
                    "win_rate": rsi_best["win_rate"],
                    "trades": rsi_best["total_trades"],
                }
                successful_optimizations += 1

            # Session optimization results
            if (
                session_results.get("detailed_results", {})
                .get(pair, {})
                .get("best_session_config")
            ):
                session_best = session_results["detailed_results"][pair][
                    "best_session_config"
                ]
                pair_summary["optimized_parameters"]["session"] = {
                    "name": session_best["session_name"],
                    "window": session_best["session_window"],
                    "quality": session_best["session_quality"],
                    "win_rate": session_best["win_rate"],
                    "trades": session_best["total_trades"],
                }
                successful_optimizations += 1

            # Calculate performance improvements vs baseline
            baseline = self.baseline_performance.get(pair, {})
            baseline_win_rate = baseline.get("win_rate", 0)
            baseline_trades = baseline.get("trades", 0)

            # Find best optimization across all parameters
            best_win_rate = baseline_win_rate
            best_trades = baseline_trades
            best_optimization = "baseline"

            for opt_type, params in pair_summary["optimized_parameters"].items():
                if params["win_rate"] > best_win_rate:
                    best_win_rate = params["win_rate"]
                    best_trades = params["trades"]
                    best_optimization = opt_type

            if best_optimization != "baseline":
                pair_summary["performance_improvements"] = {
                    "best_optimization": best_optimization,
                    "win_rate_improvement": round(best_win_rate - baseline_win_rate, 2),
                    "trade_count_change": best_trades - baseline_trades,
                    "improvement_percentage": round(
                        (best_win_rate - baseline_win_rate)
                        / max(baseline_win_rate, 1)
                        * 100,
                        1,
                    ),
                }

                # Generate implementation recommendation
                if best_win_rate > baseline_win_rate + 5:
                    pair_summary["implementation_recommendation"] = (
                        "implement_immediately"
                    )
                elif best_win_rate > baseline_win_rate + 2:
                    pair_summary["implementation_recommendation"] = (
                        "implement_after_testing"
                    )
                elif best_trades > baseline_trades + 10:
                    pair_summary["implementation_recommendation"] = (
                        "consider_for_frequency"
                    )

            summary["performance_improvements"][pair] = pair_summary

        # Calculate overall metrics
        summary["optimization_success_rate"] = {
            "successful_optimizations": successful_optimizations,
            "total_optimizations": total_optimizations,
            "success_percentage": round(
                successful_optimizations / max(total_optimizations, 1) * 100, 1
            ),
        }

        # Generate overall strategy impact
        immediate_implementations = len(
            [
                p
                for p in summary["performance_improvements"].values()
                if p["implementation_recommendation"] == "implement_immediately"
            ]
        )

        summary["overall_strategy_impact"] = {
            "pairs_with_significant_improvement": immediate_implementations,
            "optimization_pipeline_effectiveness": (
                "high" if immediate_implementations >= 2 else "moderate"
            ),
            "recommended_next_steps": [
                "Implement optimized parameters for high-improvement pairs",
                "Run validation backtests with new parameters",
                "Begin live paper trading with optimized settings",
                "Monitor performance vs baseline for 2-4 weeks",
            ],
        }

        return summary

    def _save_comprehensive_results(self, results: Dict) -> str:
        """Save comprehensive optimization results."""
        try:
            output_dir = "/Users/tyrelle/Desktop/4ex.ninja/4ex.ninja-backend/enhanced_daily_strategy/parameter_optimization/optimization_results"
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_optimization_results_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Comprehensive optimization results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving comprehensive results: {e}")
            return ""

    def _print_optimization_summary(self, results: Dict):
        """Print comprehensive optimization summary."""
        print("\n" + "=" * 80)
        print("ENHANCED DAILY STRATEGY OPTIMIZATION - FINAL SUMMARY")
        print("=" * 80)

        summary = results.get("comprehensive_summary", {})

        # Success rate
        success = summary.get("optimization_success_rate", {})
        print(
            f"Optimization Success Rate: {success.get('successful_optimizations', 0)}/{success.get('total_optimizations', 0)} "
            f"({success.get('success_percentage', 0)}%)"
        )

        # Pair-by-pair improvements
        print("\nPAIR-BY-PAIR OPTIMIZATION RESULTS:")
        print("-" * 50)

        improvements = summary.get("performance_improvements", {})
        for pair, data in improvements.items():
            baseline = data.get("baseline", {})
            improvement = data.get("performance_improvements", {})
            recommendation = data.get("implementation_recommendation", "evaluate")

            print(f"\n{pair}:")
            print(
                f"  Baseline: {baseline.get('win_rate', 0):.1f}% win rate, {baseline.get('trades', 0)} trades"
            )

            if improvement:
                print(f"  Best Optimization: {improvement['best_optimization']}")
                print(
                    f"  Improvement: +{improvement['win_rate_improvement']:.1f}% win rate "
                    f"({improvement['improvement_percentage']:+.1f}%)"
                )
                print(f"  Trade Change: {improvement['trade_count_change']:+d} trades")

            print(f"  Recommendation: {recommendation.upper()}")

        # Overall impact
        impact = summary.get("overall_strategy_impact", {})
        print(f"\nOVERALL IMPACT:")
        print(
            f"  Pairs with Significant Improvement: {impact.get('pairs_with_significant_improvement', 0)}"
        )
        print(
            f"  Pipeline Effectiveness: {impact.get('optimization_pipeline_effectiveness', 'unknown').upper()}"
        )

        # Next steps
        next_steps = impact.get("recommended_next_steps", [])
        if next_steps:
            print(f"\nRECOMMENDED NEXT STEPS:")
            for i, step in enumerate(next_steps, 1):
                print(f"  {i}. {step}")

        print("=" * 80)
        print("Optimization pipeline completed successfully!")
        print("=" * 80)


def main():
    """Main execution function."""
    logger.info("Enhanced Daily Strategy - Master Parameter Optimization")

    # Initialize master runner
    runner = MasterOptimizationRunner(initial_balance=100000)

    # Run complete optimization pipeline
    results = runner.run_complete_optimization_pipeline()

    if results.get("optimization_pipeline", {}).get("status") == "completed":
        logger.info("Master optimization pipeline completed successfully!")
    else:
        logger.error("Master optimization pipeline failed to complete")


if __name__ == "__main__":
    main()
