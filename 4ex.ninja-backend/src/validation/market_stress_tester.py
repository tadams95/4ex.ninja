"""
Market Condition Stress Testing Module
Phase 4.2 Implementation: Test strategy performance during various market conditions

This module implements comprehensive stress testing for forex trading strategies
during major market events and conditions as outlined in the Comprehensive Backtesting Plan.
"""

import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import numpy as np

# Local imports
from src.backtesting.swing_backtest_engine import SwingBacktestEngine
from src.core.models import BacktestResult
from src.strategies.ma_unified_strat import MAUnifiedStrategy

logger = logging.getLogger(__name__)


@dataclass
class StressEvent:
    """Define a major market stress event for testing"""

    name: str
    start_date: datetime
    end_date: datetime
    description: str
    expected_characteristics: List[str]
    affected_pairs: List[str]
    severity: str  # "low", "medium", "high", "extreme"


@dataclass
class StressTestResult:
    """Results from stress testing a strategy during a specific event"""

    strategy_name: str
    currency_pair: str
    event_name: str
    event_period: str

    # Performance metrics during stress
    stress_return: float
    stress_sharpe: float
    stress_max_drawdown: float
    stress_volatility: float
    stress_win_rate: float
    stress_total_trades: int

    # Comparison with normal periods
    normal_return: float
    normal_sharpe: float
    normal_max_drawdown: float
    normal_volatility: float
    normal_win_rate: float

    # Stress analysis metrics
    performance_degradation: float
    risk_increase: float
    regime_detection_effectiveness: float
    failure_modes: List[str]

    # Value at Risk metrics
    var_95_stress: float
    var_99_stress: float
    tail_risk_ratio: float

    # Recovery analysis
    recovery_time_days: Optional[int]
    post_stress_performance: float


class MarketStressTester:
    """
    Comprehensive market stress testing engine for forex strategies

    Tests strategy performance during major market events and conditions:
    - COVID-19 Market Crash (2020)
    - Inflation & Rate Hikes (2022)
    - Market Recovery (2023-2024)
    - Brexit Volatility (GBP pairs)
    - Central Bank Policy Changes
    - Economic Data Releases
    """

    def __init__(self, backtest_engine: SwingBacktestEngine):
        self.engine = backtest_engine
        self.stress_events = self._define_stress_events()
        self.results_cache = {}

    def _define_stress_events(self) -> List[StressEvent]:
        """Define major market stress events for testing"""
        return [
            StressEvent(
                name="COVID_CRASH_2020",
                start_date=datetime(2020, 2, 20),
                end_date=datetime(2020, 4, 30),
                description="COVID-19 pandemic market crash and initial recovery",
                expected_characteristics=[
                    "extreme_volatility",
                    "liquidity_crisis",
                    "flight_to_safety",
                    "central_bank_intervention",
                    "correlation_breakdown",
                ],
                affected_pairs=[
                    "EUR_USD",
                    "GBP_USD",
                    "USD_JPY",
                    "USD_CHF",
                    "AUD_USD",
                    "USD_CAD",
                ],
                severity="extreme",
            ),
            StressEvent(
                name="INFLATION_RATES_2022",
                start_date=datetime(2022, 1, 1),
                end_date=datetime(2022, 12, 31),
                description="Inflation surge and aggressive rate hiking cycle",
                expected_characteristics=[
                    "high_volatility",
                    "rate_uncertainty",
                    "dollar_strength",
                    "commodity_impact",
                    "policy_divergence",
                ],
                affected_pairs=[
                    "EUR_USD",
                    "GBP_USD",
                    "USD_JPY",
                    "USD_CHF",
                    "AUD_USD",
                    "USD_CAD",
                ],
                severity="high",
            ),
            StressEvent(
                name="MARKET_RECOVERY_2023",
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2024, 6, 30),
                description="Market recovery and normalization period",
                expected_characteristics=[
                    "decreasing_volatility",
                    "trend_resumption",
                    "policy_clarity",
                    "economic_stabilization",
                    "correlation_normalization",
                ],
                affected_pairs=[
                    "EUR_USD",
                    "GBP_USD",
                    "USD_JPY",
                    "USD_CHF",
                    "AUD_USD",
                    "USD_CAD",
                ],
                severity="medium",
            ),
            StressEvent(
                name="BREXIT_VOLATILITY",
                start_date=datetime(2020, 12, 1),
                end_date=datetime(2021, 3, 31),
                description="Brexit implementation and trade deal uncertainty",
                expected_characteristics=[
                    "gbp_specific_volatility",
                    "political_uncertainty",
                    "trade_disruption",
                    "policy_divergence",
                    "correlation_changes",
                ],
                affected_pairs=["GBP_USD", "EUR_GBP", "GBP_JPY"],
                severity="high",
            ),
            StressEvent(
                name="ECB_POLICY_SHIFT_2022",
                start_date=datetime(2022, 7, 1),
                end_date=datetime(2022, 12, 31),
                description="ECB policy normalization and rate liftoff",
                expected_characteristics=[
                    "eur_volatility",
                    "policy_surprise",
                    "yield_differential_changes",
                    "inflation_expectations",
                    "cross_currency_impact",
                ],
                affected_pairs=["EUR_USD", "EUR_GBP", "EUR_JPY"],
                severity="medium",
            ),
            StressEvent(
                name="BOJ_INTERVENTION_2022",
                start_date=datetime(2022, 9, 1),
                end_date=datetime(2022, 11, 30),
                description="Bank of Japan FX intervention period",
                expected_characteristics=[
                    "jpy_volatility",
                    "intervention_risk",
                    "carry_trade_unwind",
                    "yield_curve_control",
                    "policy_divergence",
                ],
                affected_pairs=["USD_JPY", "EUR_JPY", "GBP_JPY", "AUD_JPY"],
                severity="high",
            ),
        ]

    async def run_comprehensive_stress_test(
        self, strategy_configs: List[Dict[str, Any]], currency_pairs: List[str]
    ) -> Dict[str, List[StressTestResult]]:
        """
        Run comprehensive stress testing across all events and strategies

        Args:
            strategy_configs: List of strategy configurations to test
            currency_pairs: List of currency pairs to analyze

        Returns:
            Dictionary mapping event names to stress test results
        """
        logger.info("🔥 Starting Comprehensive Market Stress Testing")
        logger.info(
            f"Testing {len(strategy_configs)} strategies across {len(currency_pairs)} pairs"
        )
        logger.info(f"Analyzing {len(self.stress_events)} major market events")

        all_results = {}

        for event in self.stress_events:
            logger.info(f"\n📊 Testing Event: {event.name}")
            logger.info(
                f"Period: {event.start_date.strftime('%Y-%m-%d')} to {event.end_date.strftime('%Y-%m-%d')}"
            )
            logger.info(f"Severity: {event.severity.upper()}")

            event_results = []

            # Filter pairs relevant to this event
            relevant_pairs = [
                pair for pair in currency_pairs if pair in event.affected_pairs
            ]

            for pair in relevant_pairs:
                for config in strategy_configs:
                    try:
                        result = await self._test_strategy_during_event(
                            config, pair, event
                        )
                        if result:
                            event_results.append(result)
                            logger.info(f"✅ Completed {config['name']} on {pair}")
                    except Exception as e:
                        logger.error(
                            f"❌ Failed testing {config['name']} on {pair}: {e}"
                        )

            all_results[event.name] = event_results
            logger.info(
                f"📈 Event {event.name}: {len(event_results)} results generated"
            )

        # Generate comprehensive stress test report
        await self._generate_stress_test_report(all_results)

        logger.info("🎉 Comprehensive Stress Testing Complete!")
        return all_results

    async def _test_strategy_during_event(
        self, strategy_config: Dict[str, Any], currency_pair: str, event: StressEvent
    ) -> Optional[StressTestResult]:
        """Test a specific strategy during a stress event"""

        try:
            # Create strategy instance
            strategy = MAUnifiedStrategy(**strategy_config["parameters"])

            # Define stress period
            stress_start = event.start_date
            stress_end = event.end_date

            # Define comparison periods (before and after the event)
            pre_stress_start = stress_start - timedelta(days=365)
            pre_stress_end = stress_start - timedelta(days=1)

            post_stress_start = stress_end + timedelta(days=1)
            post_stress_end = stress_end + timedelta(days=365)

            # Run backtests for all periods
            stress_result = await self.engine.run_simple_backtest(
                strategy, currency_pair, stress_start, stress_end
            )

            normal_result = await self.engine.run_simple_backtest(
                strategy, currency_pair, pre_stress_start, pre_stress_end
            )

            recovery_result = await self.engine.run_simple_backtest(
                strategy, currency_pair, post_stress_start, post_stress_end
            )

            # Calculate stress metrics
            stress_metrics = self._calculate_stress_metrics(
                stress_result, normal_result, recovery_result, event
            )

            # Analyze failure modes
            failure_modes = self._identify_failure_modes(stress_result, event)

            # Calculate Value at Risk
            var_metrics = self._calculate_var_metrics(stress_result)

            # Analyze recovery
            recovery_metrics = self._analyze_recovery(stress_result, recovery_result)

            return StressTestResult(
                strategy_name=strategy_config["name"],
                currency_pair=currency_pair,
                event_name=event.name,
                event_period=f"{stress_start.strftime('%Y-%m-%d')} to {stress_end.strftime('%Y-%m-%d')}",
                # Stress performance
                stress_return=stress_result.performance_metrics.total_return,
                stress_sharpe=stress_result.performance_metrics.sharpe_ratio,
                stress_max_drawdown=stress_result.performance_metrics.max_drawdown,
                stress_volatility=stress_result.performance_metrics.volatility,
                stress_win_rate=stress_result.trade_statistics.win_rate,
                stress_total_trades=stress_result.trade_statistics.total_trades,
                # Normal performance
                normal_return=normal_result.performance_metrics.total_return,
                normal_sharpe=normal_result.performance_metrics.sharpe_ratio,
                normal_max_drawdown=normal_result.performance_metrics.max_drawdown,
                normal_volatility=normal_result.performance_metrics.volatility,
                normal_win_rate=normal_result.trade_statistics.win_rate,
                # Stress analysis
                performance_degradation=stress_metrics["performance_degradation"],
                risk_increase=stress_metrics["risk_increase"],
                regime_detection_effectiveness=stress_metrics["regime_effectiveness"],
                failure_modes=failure_modes,
                # VaR metrics
                var_95_stress=var_metrics["var_95"],
                var_99_stress=var_metrics["var_99"],
                tail_risk_ratio=var_metrics["tail_risk_ratio"],
                # Recovery analysis
                recovery_time_days=recovery_metrics["recovery_time_days"],
                post_stress_performance=recovery_result.performance_metrics.total_return,
            )

        except Exception as e:
            logger.error(
                f"Error testing {strategy_config['name']} on {currency_pair} during {event.name}: {e}"
            )
            return None

    def _calculate_stress_metrics(
        self,
        stress_result: BacktestResult,
        normal_result: BacktestResult,
        recovery_result: BacktestResult,
        event: StressEvent,
    ) -> Dict[str, float]:
        """Calculate stress-specific performance metrics"""

        # Performance degradation
        perf_degradation = 1.0 - (
            stress_result.performance_metrics.total_return
            / max(normal_result.performance_metrics.total_return, 0.01)
        )

        # Risk increase (volatility ratio)
        risk_increase = stress_result.performance_metrics.volatility / max(
            normal_result.performance_metrics.volatility, 0.01
        )

        # Regime detection effectiveness (simplified)
        # Higher regime performance variance indicates better detection
        regime_performance = stress_result.regime_analysis.get("regime_performance", {})
        regime_returns = [data.get("return", 0) for data in regime_performance.values()]
        regime_effectiveness = (
            np.std(regime_returns) if len(regime_returns) > 1 else 0.0
        )

        return {
            "performance_degradation": max(perf_degradation, -1.0),  # Cap at -100%
            "risk_increase": risk_increase,
            "regime_effectiveness": regime_effectiveness,
        }

    def _identify_failure_modes(
        self, stress_result: BacktestResult, event: StressEvent
    ) -> List[str]:
        """Identify specific failure modes during stress periods"""

        failure_modes = []

        # Check for excessive drawdown
        if stress_result.performance_metrics.max_drawdown > 0.3:
            failure_modes.append("excessive_drawdown")

        # Check for consecutive losses
        if stress_result.trade_statistics.consecutive_losses > 5:
            failure_modes.append("extended_losing_streak")

        # Check for low win rate
        if stress_result.trade_statistics.win_rate < 0.3:
            failure_modes.append("low_win_rate")

        # Check for negative returns
        if stress_result.performance_metrics.total_return < -0.1:
            failure_modes.append("significant_losses")

        # Check for high volatility
        if stress_result.performance_metrics.volatility > 0.4:
            failure_modes.append("excessive_volatility")

        # Event-specific failure modes
        if event.severity == "extreme":
            if stress_result.performance_metrics.sharpe_ratio < 0:
                failure_modes.append("negative_risk_adjusted_return")

        return failure_modes

    def _calculate_var_metrics(self, result: BacktestResult) -> Dict[str, float]:
        """Calculate Value at Risk metrics from backtest results"""

        # Extract trade returns if available
        trade_returns = []
        if hasattr(result, "trade_details"):
            for trade in result.trade_details:
                if hasattr(trade, "return_pct"):
                    trade_returns.append(trade.return_pct)

        if not trade_returns:
            # Use performance metrics as proxy
            return {
                "var_95": (
                    result.performance_metrics.var_95
                    if hasattr(result.performance_metrics, "var_95")
                    else 0.05
                ),
                "var_99": (
                    result.performance_metrics.var_95 * 1.5
                    if hasattr(result.performance_metrics, "var_95")
                    else 0.075
                ),
                "tail_risk_ratio": 1.5,
            }

        # Calculate VaR
        trade_returns = np.array(trade_returns)
        var_95 = np.percentile(trade_returns, 5)
        var_99 = np.percentile(trade_returns, 1)

        # Tail risk ratio (ratio of extreme losses to VaR)
        extreme_losses = trade_returns[trade_returns < var_99]
        tail_risk_ratio = (
            abs(np.mean(extreme_losses) / var_99)
            if len(extreme_losses) > 0 and var_99 != 0
            else 1.0
        )

        return {
            "var_95": abs(var_95),
            "var_99": abs(var_99),
            "tail_risk_ratio": tail_risk_ratio,
        }

    def _analyze_recovery(
        self, stress_result: BacktestResult, recovery_result: BacktestResult
    ) -> Dict[str, Any]:
        """Analyze recovery characteristics after stress events"""

        # Simplified recovery analysis
        # In a real implementation, you'd analyze the recovery trajectory day by day

        recovery_time_days = None
        if (
            stress_result.performance_metrics.total_return < 0
            and recovery_result.performance_metrics.total_return > 0
        ):
            # Estimate recovery time (simplified)
            recovery_time_days = 90  # Assume 3 months average recovery

        return {
            "recovery_time_days": recovery_time_days,
            "recovery_strength": recovery_result.performance_metrics.total_return,
        }

    async def _generate_stress_test_report(
        self, all_results: Dict[str, List[StressTestResult]]
    ):
        """Generate comprehensive stress test analysis report"""

        report_path = f"/Users/tyrelle/Desktop/4ex.ninja/docs/Backtest_Reviews/MARKET_STRESS_TEST_ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_path, "w") as f:
            f.write("# 🔥 MARKET CONDITION STRESS TEST ANALYSIS\n")
            f.write("## Phase 4.2: Advanced Analysis & Optimization\n\n")
            f.write(
                f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"**Analysis Type:** Comprehensive Market Stress Testing\n")
            f.write(f"**Events Analyzed:** {len(all_results)}\n\n")

            # Executive Summary
            f.write("## 🎯 EXECUTIVE SUMMARY\n\n")
            total_tests = sum(len(results) for results in all_results.values())
            f.write(f"**Total Stress Tests Executed:** {total_tests}\n")

            # Calculate overall stress resilience
            all_stress_results = [
                result for results in all_results.values() for result in results
            ]
            if all_stress_results:
                avg_degradation = np.mean(
                    [r.performance_degradation for r in all_stress_results]
                )
                avg_risk_increase = np.mean(
                    [r.risk_increase for r in all_stress_results]
                )

                resilience_score = max(
                    0, 1 - (avg_degradation + (avg_risk_increase - 1) * 0.5)
                )
                f.write(
                    f"**Overall Stress Resilience Score:** {resilience_score:.3f}/1.000\n"
                )
                f.write(f"**Average Performance Degradation:** {avg_degradation:.1%}\n")
                f.write(f"**Average Risk Increase:** {avg_risk_increase:.2f}x\n\n")

            # Detailed analysis by event
            for event_name, results in all_results.items():
                if not results:
                    continue

                f.write(f"## 📊 {event_name.replace('_', ' ').title()} Analysis\n\n")
                f.write(f"**Tests Completed:** {len(results)}\n")

                # Event statistics
                event_degradations = [r.performance_degradation for r in results]
                event_risk_increases = [r.risk_increase for r in results]
                failure_counts = {}

                for result in results:
                    for failure in result.failure_modes:
                        failure_counts[failure] = failure_counts.get(failure, 0) + 1

                f.write(
                    f"**Average Performance Degradation:** {np.mean(event_degradations):.1%}\n"
                )
                f.write(
                    f"**Average Risk Increase:** {np.mean(event_risk_increases):.2f}x\n"
                )
                f.write(
                    f"**Strategies with Significant Losses:** {len([r for r in results if r.stress_return < -0.1])}\n\n"
                )

                # Top performing strategies for this event
                f.write("### 🏆 Best Performing Strategies\n\n")
                best_strategies = sorted(
                    results, key=lambda x: x.stress_return, reverse=True
                )[:5]

                f.write(
                    "| Rank | Strategy | Pair | Stress Return | Degradation | Risk Increase |\n"
                )
                f.write(
                    "|------|----------|------|---------------|-------------|---------------|\n"
                )

                for i, result in enumerate(best_strategies, 1):
                    f.write(
                        f"| {i} | {result.strategy_name} | {result.currency_pair} | "
                        f"{result.stress_return:.1%} | {result.performance_degradation:.1%} | "
                        f"{result.risk_increase:.2f}x |\n"
                    )

                f.write("\n")

                # Common failure modes
                if failure_counts:
                    f.write("### ⚠️ Common Failure Modes\n\n")
                    sorted_failures = sorted(
                        failure_counts.items(), key=lambda x: x[1], reverse=True
                    )
                    for failure, count in sorted_failures:
                        percentage = count / len(results) * 100
                        f.write(
                            f"- **{failure.replace('_', ' ').title()}:** {count} strategies ({percentage:.1f}%)\n"
                        )
                    f.write("\n")

        logger.info(f"📄 Stress test report generated: {report_path}")


# Example usage and configuration
STRESS_TEST_CONFIGS = [
    {
        "name": "conservative_conservative_weekly",
        "parameters": {
            "fast_ma_period": 50,
            "slow_ma_period": 200,
            "timeframe": "W",
            "risk_per_trade": 0.01,
            "reward_ratio": 2.0,
        },
    },
    {
        "name": "moderate_conservative_daily",
        "parameters": {
            "fast_ma_period": 20,
            "slow_ma_period": 50,
            "timeframe": "D",
            "risk_per_trade": 0.02,
            "reward_ratio": 1.5,
        },
    },
    {
        "name": "aggressive_moderate_4h",
        "parameters": {
            "fast_ma_period": 10,
            "slow_ma_period": 21,
            "timeframe": "4H",
            "risk_per_trade": 0.03,
            "reward_ratio": 1.0,
        },
    },
]

CURRENCY_PAIRS = [
    "EUR_USD",
    "GBP_USD",
    "USD_JPY",
    "USD_CHF",
    "AUD_USD",
    "USD_CAD",
    "EUR_GBP",
    "EUR_JPY",
    "GBP_JPY",
]


async def main():
    """Main function to run stress testing"""

    # Initialize backtesting engine
    engine = SwingBacktestEngine()

    # Create stress tester
    stress_tester = MarketStressTester(engine)

    # Run comprehensive stress testing
    results = await stress_tester.run_comprehensive_stress_test(
        STRESS_TEST_CONFIGS, CURRENCY_PAIRS
    )

    print("✅ Stress testing completed successfully!")
    print(f"📊 Generated {sum(len(r) for r in results.values())} stress test results")

    return results


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
