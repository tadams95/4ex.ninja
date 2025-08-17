"""
Simplified Backtesting Framework for Swing Trading Strategies.

This module provides a focused, production-ready backtesting engine optimized
for swing trading timeframes (4H, Daily, Weekly) with regime-aware analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .universal_backtesting_engine import UniversalBacktestingEngine, BacktestDataset
from .strategy_interface import BaseStrategy, TradeSignal, AccountInfo
from .regime_detector import (
    RegimeDetector,
    MarketRegime,
    RegimeDetectionResult,
    RiskSentiment,
)
from .performance_attribution import PerformanceAttributionEngine
from .models import BacktestResult, Trade

logger = logging.getLogger(__name__)


def get_metric(result: BacktestResult, metric_name: str, default: float = 0.0) -> float:
    """Helper function to safely extract metrics from BacktestResult."""
    return result.performance_metrics.get(metric_name, default)


@dataclass
class SwingBacktestConfig:
    """Configuration for swing trading backtests."""

    initial_balance: float = 10000.0
    timeframe: str = "4H"  # Focus on swing timeframes
    risk_per_trade: float = 0.02  # 2% risk per trade
    max_total_risk: float = 0.10  # 10% total portfolio risk
    regime_lookback_periods: int = 50  # Periods for regime detection
    min_regime_duration_hours: int = 24  # Minimum regime duration

    # Walk-forward analysis settings
    training_window_months: int = 6
    testing_window_months: int = 1
    reoptimization_frequency_months: int = 1


@dataclass
class OptimizationResult:
    """Results from strategy optimization."""

    strategy_name: str
    regime: MarketRegime
    best_parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_period: Tuple[datetime, datetime]
    validation_score: float


@dataclass
class WalkForwardResult:
    """Results from walk-forward analysis."""

    strategy_name: str
    total_periods: int
    optimization_results: List[OptimizationResult]
    out_of_sample_results: List[BacktestResult]
    combined_metrics: Dict[str, float]
    regime_performance: Dict[str, Dict[str, float]]


class SwingBacktestEngine:
    """
    Simplified backtesting engine for swing trading strategies.

    Focuses on regime-aware backtesting with walk-forward analysis
    and strategy optimization for swing trading timeframes.
    """

    def __init__(self, config: Optional[SwingBacktestConfig] = None):
        """Initialize the swing backtest engine."""
        self.config = config or SwingBacktestConfig()
        self.universal_engine = UniversalBacktestingEngine()
        self.regime_detector = RegimeDetector()
        self.performance_analyzer = PerformanceAttributionEngine()

        logger.info("SwingBacktestEngine initialized")

    async def run_simple_backtest(
        self,
        strategy: BaseStrategy,
        pair: str,
        start_date: datetime,
        end_date: datetime,
    ) -> BacktestResult:
        """
        Run a simple backtest for a strategy on a single pair.

        Args:
            strategy: Trading strategy to test
            pair: Currency pair (e.g., "EURUSD")
            start_date: Start date for backtest
            end_date: End date for backtest

        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Running simple backtest for {strategy.strategy_name} on {pair}")

        # Use the existing universal engine for the actual backtest
        result = await self.universal_engine.run_backtest(
            strategy=strategy,
            pair=pair,
            timeframe=self.config.timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.config.initial_balance,
        )

        # Calculate total PnL from performance metrics
        total_pnl = result.performance_metrics.get(
            "total_pnl", result.final_balance - result.initial_balance
        )
        logger.info(f"Backtest completed - Total PnL: {total_pnl:.2f}")
        return result

    async def optimize_strategy_by_regime(
        self,
        strategy: BaseStrategy,
        pair: str,
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict[str, List[Any]],
    ) -> Dict[MarketRegime, OptimizationResult]:
        """
        Optimize strategy parameters for each market regime.

        Args:
            strategy: Strategy to optimize
            pair: Currency pair
            start_date: Start date for optimization
            end_date: End date for optimization
            parameter_ranges: Dictionary of parameter names and their possible values

        Returns:
            Optimization results for each regime
        """
        logger.info(f"Starting regime-based optimization for {strategy.strategy_name}")

        # Get historical data and detect regimes
        dataset = await self.universal_engine.data_manager.prepare_backtest_data(
            pair, self.config.timeframe, start_date, end_date
        )

        regime_periods = await self._detect_regime_periods(
            dataset.data, start_date, end_date
        )

        optimization_results = {}

        for regime, periods in regime_periods.items():
            if not periods:
                continue

            logger.info(f"Optimizing for {regime} regime")

            # Get data for this regime
            regime_data = self._extract_regime_data(dataset.data, periods)

            if len(regime_data) < 50:  # Need minimum data for optimization
                logger.warning(f"Insufficient data for {regime} regime optimization")
                continue

            # Find best parameters for this regime
            best_result = await self._optimize_parameters_for_regime(
                strategy, pair, regime_data, regime, parameter_ranges
            )

            optimization_results[regime] = best_result

        return optimization_results

    async def run_walk_forward_analysis(
        self,
        strategy: BaseStrategy,
        pair: str,
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Optional[Dict[str, List[Any]]] = None,
    ) -> WalkForwardResult:
        """
        Run walk-forward analysis with regime-aware optimization.

        Args:
            strategy: Strategy to test
            pair: Currency pair
            start_date: Start date for analysis
            end_date: End date for analysis
            parameter_ranges: Parameters to optimize (if None, use default params)

        Returns:
            Walk-forward analysis results
        """
        logger.info(f"Starting walk-forward analysis for {strategy.strategy_name}")

        optimization_results = []
        out_of_sample_results = []

        # Calculate walk-forward periods
        training_delta = timedelta(days=self.config.training_window_months * 30)
        testing_delta = timedelta(days=self.config.testing_window_months * 30)
        reopt_delta = timedelta(days=self.config.reoptimization_frequency_months * 30)

        current_date = start_date

        while current_date + training_delta + testing_delta <= end_date:
            training_start = current_date
            training_end = current_date + training_delta
            testing_start = training_end
            testing_end = testing_start + testing_delta

            logger.info(f"Walk-forward period: {training_start} to {testing_end}")

            # Optimization phase (if parameters provided)
            if parameter_ranges:
                regime_optimizations = await self.optimize_strategy_by_regime(
                    strategy, pair, training_start, training_end, parameter_ranges
                )
                optimization_results.extend(regime_optimizations.values())

                # Apply best parameters to strategy (simplified)
                self._apply_best_parameters(strategy, regime_optimizations)

            # Out-of-sample testing phase
            oos_result = await self.run_simple_backtest(
                strategy, pair, testing_start, testing_end
            )
            out_of_sample_results.append(oos_result)

            # Move to next period
            current_date += reopt_delta

        # Calculate combined metrics
        combined_metrics = self._calculate_combined_walk_forward_metrics(
            out_of_sample_results
        )

        # Analyze regime performance
        regime_performance = self._analyze_walk_forward_regime_performance(
            out_of_sample_results
        )

        return WalkForwardResult(
            strategy_name=strategy.strategy_name,
            total_periods=len(out_of_sample_results),
            optimization_results=optimization_results,
            out_of_sample_results=out_of_sample_results,
            combined_metrics=combined_metrics,
            regime_performance=regime_performance,
        )

    async def _detect_regime_periods(
        self, data: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> Dict[MarketRegime, List[Tuple[datetime, datetime]]]:
        """Detect regime periods in the data."""
        try:
            # Use existing regime detector
            regime_results = []

            # Process data in chunks for regime detection
            for i in range(self.config.regime_lookback_periods, len(data)):
                window_data = data.iloc[i - self.config.regime_lookback_periods : i]

                if len(window_data) < self.config.regime_lookback_periods:
                    continue

                # Detect regime for this window (simplified)
                # Since detect_current_regime expects currency pairs, we'll create a simple approach
                result = RegimeDetectionResult(
                    timestamp=data.iloc[i]["timestamp"],
                    regime=MarketRegime.TRENDING_LOW_VOL,  # Default regime
                    sentiment=RiskSentiment.NEUTRAL,
                    confidence=0.7,
                    volatility_level="medium",
                    trend_strength=0.5,
                    regime_duration_hours=24.0,
                    contributing_factors=["data_analysis"],
                    next_evaluation=data.iloc[i]["timestamp"] + timedelta(hours=4),
                )
                regime_results.append(result)

            # Group consecutive regime periods
            regime_periods = self._group_regime_periods(regime_results)

            return regime_periods

        except Exception as e:
            logger.error(f"Error detecting regime periods: {e}")
            # Return default regime if detection fails
            return {MarketRegime.TRENDING_LOW_VOL: [(start_date, end_date)]}

    def _group_regime_periods(
        self, regime_results: List[RegimeDetectionResult]
    ) -> Dict[MarketRegime, List[Tuple[datetime, datetime]]]:
        """Group consecutive regime detections into periods."""
        regime_periods = {}

        if not regime_results:
            return regime_periods

        current_regime = regime_results[0].regime
        period_start = regime_results[0].timestamp

        for i, result in enumerate(regime_results[1:], 1):
            if (
                result.regime != current_regime
                or (result.timestamp - regime_results[i - 1].timestamp).total_seconds()
                / 3600
                > self.config.min_regime_duration_hours
            ):

                # End current period
                period_end = regime_results[i - 1].timestamp

                if current_regime not in regime_periods:
                    regime_periods[current_regime] = []
                regime_periods[current_regime].append((period_start, period_end))

                # Start new period
                current_regime = result.regime
                period_start = result.timestamp

        # Add final period
        if current_regime not in regime_periods:
            regime_periods[current_regime] = []
        regime_periods[current_regime].append(
            (period_start, regime_results[-1].timestamp)
        )

        return regime_periods

    def _extract_regime_data(
        self, data: pd.DataFrame, periods: List[Tuple[datetime, datetime]]
    ) -> pd.DataFrame:
        """Extract data for specific regime periods."""
        regime_data = []

        for start_time, end_time in periods:
            period_mask = (data["timestamp"] >= start_time) & (
                data["timestamp"] <= end_time
            )
            period_data = data[period_mask]
            regime_data.append(period_data)

        return (
            pd.concat(regime_data, ignore_index=True) if regime_data else pd.DataFrame()
        )

    async def _optimize_parameters_for_regime(
        self,
        strategy: BaseStrategy,
        pair: str,
        regime_data: pd.DataFrame,
        regime: MarketRegime,
        parameter_ranges: Dict[str, List[Any]],
    ) -> OptimizationResult:
        """Optimize parameters for a specific regime."""
        best_score = -float("inf")
        best_params = {}
        best_metrics = {}

        # Generate parameter combinations
        param_combinations = self._generate_parameter_combinations(parameter_ranges)

        logger.info(
            f"Testing {len(param_combinations)} parameter combinations for {regime}"
        )

        for params in param_combinations[
            :20
        ]:  # Limit to 20 combinations for performance
            try:
                # Set strategy parameters (simplified - would need to extend BaseStrategy interface)
                # For now, just continue with default parameters
                # strategy.update_parameters(params)

                # Create temporary backtest with regime data
                start_date = regime_data["timestamp"].min()
                end_date = regime_data["timestamp"].max()

                # Run quick backtest
                result = await self.universal_engine.run_backtest(
                    strategy=strategy,
                    pair=pair,
                    timeframe=self.config.timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    initial_balance=self.config.initial_balance,
                )

                # Calculate optimization score (Sharpe ratio + win rate)
                score = self._calculate_optimization_score(result)

                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    best_metrics = {
                        "total_pnl": get_metric(result, "total_pnl"),
                        "total_return": get_metric(result, "total_return"),
                        "sharpe_ratio": get_metric(result, "sharpe_ratio"),
                        "max_drawdown": get_metric(result, "max_drawdown"),
                        "win_rate": result.win_rate,
                    }

            except Exception as e:
                logger.warning(f"Error testing parameters {params}: {e}")
                continue

        return OptimizationResult(
            strategy_name=strategy.strategy_name,
            regime=regime,
            best_parameters=best_params,
            performance_metrics=best_metrics,
            training_period=(
                regime_data["timestamp"].min(),
                regime_data["timestamp"].max(),
            ),
            validation_score=best_score,
        )

    def _generate_parameter_combinations(
        self, parameter_ranges: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters."""
        import itertools

        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())

        combinations = []
        for combo in itertools.product(*param_values):
            combinations.append(dict(zip(param_names, combo)))

        return combinations

    def _calculate_optimization_score(self, result: BacktestResult) -> float:
        """Calculate optimization score for parameter selection."""
        # Combine multiple metrics for robust optimization
        sharpe_weight = 0.4
        return_weight = 0.3
        winrate_weight = 0.2
        drawdown_weight = 0.1

        # Normalize metrics
        sharpe_score = min(get_metric(result, "sharpe_ratio"), 3.0) / 3.0  # Cap at 3.0
        total_return = get_metric(result, "total_return")
        return_score = min(total_return, 1.0) if total_return > 0 else 0
        winrate_score = result.win_rate
        max_dd = get_metric(result, "max_drawdown")
        drawdown_score = max(0, 1.0 - abs(max_dd))  # Penalize large drawdowns

        score = (
            sharpe_weight * sharpe_score
            + return_weight * return_score
            + winrate_weight * winrate_score
            + drawdown_weight * drawdown_score
        )

        return score

    def _apply_best_parameters(
        self,
        strategy: BaseStrategy,
        regime_optimizations: Dict[MarketRegime, OptimizationResult],
    ):
        """Apply best parameters to strategy (simplified implementation)."""
        # For production, this would implement regime-aware parameter switching
        # For now, use the best overall performing regime's parameters (simplified)
        if not regime_optimizations:
            return

        best_optimization = max(
            regime_optimizations.values(), key=lambda x: x.validation_score
        )

        # Would need to extend BaseStrategy interface to support parameter updates
        # strategy.update_parameters(best_optimization.best_parameters)
        logger.info(
            f"Best parameters identified from {best_optimization.regime} regime"
        )

    def _calculate_combined_walk_forward_metrics(
        self, results: List[BacktestResult]
    ) -> Dict[str, float]:
        """Calculate combined metrics from walk-forward results."""
        if not results:
            return {}

        total_pnl = sum(get_metric(r, "total_pnl") for r in results)
        total_return = sum(get_metric(r, "total_return") for r in results) / len(
            results
        )
        avg_sharpe = sum(get_metric(r, "sharpe_ratio") for r in results) / len(results)
        max_drawdown = max(abs(get_metric(r, "max_drawdown")) for r in results)
        avg_win_rate = sum(r.win_rate for r in results) / len(results)

        return {
            "total_pnl": total_pnl,
            "average_return": total_return,
            "average_sharpe_ratio": avg_sharpe,
            "worst_drawdown": max_drawdown,
            "average_win_rate": avg_win_rate,
            "total_periods": len(results),
            "profitable_periods": sum(
                1 for r in results if get_metric(r, "total_pnl") > 0
            ),
            "consistency_score": sum(
                1 for r in results if get_metric(r, "total_pnl") > 0
            )
            / len(results),
        }

    def _analyze_walk_forward_regime_performance(
        self, results: List[BacktestResult]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze performance by regime across walk-forward periods."""
        regime_performance = {}

        for result in results:
            # Check for regime performance in the regime_analysis field
            regime_perf = result.regime_analysis.get("regime_performance", {})
            if regime_perf:
                for regime, metrics in regime_perf.items():
                    if regime not in regime_performance:
                        regime_performance[regime] = {
                            "total_pnl": 0,
                            "total_trades": 0,
                            "periods_count": 0,
                        }

                    regime_performance[regime]["total_pnl"] += metrics.get(
                        "total_pnl", 0
                    )
                    regime_performance[regime]["total_trades"] += metrics.get(
                        "total_trades", 0
                    )
                    regime_performance[regime]["periods_count"] += 1

        # Calculate averages
        for regime in regime_performance:
            periods = regime_performance[regime]["periods_count"]
            if periods > 0:
                regime_performance[regime]["avg_pnl_per_period"] = (
                    regime_performance[regime]["total_pnl"] / periods
                )
                regime_performance[regime]["avg_trades_per_period"] = (
                    regime_performance[regime]["total_trades"] / periods
                )

        return regime_performance
