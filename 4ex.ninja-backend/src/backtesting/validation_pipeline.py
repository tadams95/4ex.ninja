"""
Validation Pipeline for comprehensive strategy validation.

Integrates with existing Phase 2 infrastructure for automated testing
and strategy robustness analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import logging

from .universal_backtesting_engine import UniversalBacktestingEngine
from .strategies.strategy_registry import strategy_registry
from .strategy_interface import BaseStrategy
from .regime_detector import RegimeDetector, MarketRegime
from .models import BacktestResult, Trade

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for validation pipeline."""

    test_periods: List[Tuple[datetime, datetime]]
    currency_pairs: List[str] = field(default_factory=lambda: ["EURUSD", "GBPUSD"])
    timeframes: List[str] = field(default_factory=lambda: ["4H"])
    min_trades_threshold: int = 10
    max_drawdown_threshold: float = 0.20  # 20%
    min_win_rate_threshold: float = 0.30  # 30%
    min_profit_factor_threshold: float = 1.1


@dataclass
class ValidationMetrics:
    """Validation metrics for a strategy."""

    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    total_return: float
    sharpe_ratio: float
    calmar_ratio: float
    avg_trade_duration: float  # in hours
    regime_performance: Dict[str, Dict[str, float]]


@dataclass
class ValidationResult:
    """Result of strategy validation."""

    strategy_name: str
    validation_passed: bool
    metrics: ValidationMetrics
    failed_criteria: List[str]
    recommendations: List[str]
    detailed_results: Dict[str, Any]


class ValidationPipeline:
    """
    Comprehensive validation pipeline for strategy testing.

    Integrates with existing Phase 2 infrastructure for robust
    strategy validation across multiple market conditions.
    """

    def __init__(self):
        """Initialize validation pipeline."""
        self.engine = UniversalBacktestingEngine()
        self.regime_detector = RegimeDetector()

    async def validate_strategy(
        self,
        strategy_name: str,
        strategy_config: Dict[str, Any],
        validation_config: Optional[ValidationConfig] = None,
    ) -> ValidationResult:
        """
        Run comprehensive validation for a strategy.

        Args:
            strategy_name: Name of strategy to validate
            strategy_config: Strategy configuration
            validation_config: Validation configuration

        Returns:
            ValidationResult with comprehensive analysis
        """
        if validation_config is None:
            validation_config = self._get_default_validation_config()

        logger.info(f"Starting validation for strategy: {strategy_name}")

        try:
            # Create strategy instance
            strategy = strategy_registry.get_strategy(strategy_name, strategy_config)

            # Run backtests across test periods and pairs
            all_results = []
            for start_date, end_date in validation_config.test_periods:
                for pair in validation_config.currency_pairs:
                    for timeframe in validation_config.timeframes:
                        try:
                            result = await self.engine.run_backtest(
                                strategy=strategy,
                                pair=pair,
                                timeframe=timeframe,
                                start_date=start_date,
                                end_date=end_date,
                            )
                            all_results.append(
                                {
                                    "result": result,
                                    "pair": pair,
                                    "timeframe": timeframe,
                                    "period": (start_date, end_date),
                                }
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed backtest for {pair} {timeframe}: {e}"
                            )
                            continue

            if not all_results:
                return ValidationResult(
                    strategy_name=strategy_name,
                    validation_passed=False,
                    metrics=ValidationMetrics(
                        total_trades=0,
                        win_rate=0,
                        profit_factor=0,
                        max_drawdown=0,
                        total_return=0,
                        sharpe_ratio=0,
                        calmar_ratio=0,
                        avg_trade_duration=0,
                        regime_performance={},
                    ),
                    failed_criteria=["No successful backtests"],
                    recommendations=[
                        "Check strategy implementation and data availability"
                    ],
                    detailed_results={},
                )

            # Calculate comprehensive metrics
            metrics = self._calculate_validation_metrics(all_results)

            # Check validation criteria
            validation_passed, failed_criteria = self._check_validation_criteria(
                metrics, validation_config
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, failed_criteria)

            # Prepare detailed results
            detailed_results = self._prepare_detailed_results(all_results, metrics)

            return ValidationResult(
                strategy_name=strategy_name,
                validation_passed=validation_passed,
                metrics=metrics,
                failed_criteria=failed_criteria,
                recommendations=recommendations,
                detailed_results=detailed_results,
            )

        except Exception as e:
            logger.error(f"Validation failed for {strategy_name}: {e}")
            raise

    def _get_default_validation_config(self) -> ValidationConfig:
        """Get default validation configuration."""

        # Define test periods (last 2 years in 6-month chunks)
        end_date = datetime.now()
        test_periods = []

        for i in range(4):  # 4 periods of 6 months
            period_end = end_date - timedelta(days=i * 180)
            period_start = period_end - timedelta(days=180)
            test_periods.append((period_start, period_end))

        return ValidationConfig(test_periods=test_periods)

    def _calculate_validation_metrics(
        self, results: List[Dict[str, Any]]
    ) -> ValidationMetrics:
        """Calculate comprehensive validation metrics."""

        # Combine all trades
        all_trades = []
        total_return = 0
        returns_by_period = []

        for result_data in results:
            result = result_data["result"]
            all_trades.extend(result.trades)

            # Calculate period return
            period_pnl = sum(trade.pnl for trade in result.trades)
            total_return += period_pnl
            returns_by_period.append(period_pnl)

        if not all_trades:
            return ValidationMetrics(
                total_trades=0,
                win_rate=0,
                profit_factor=0,
                max_drawdown=0,
                total_return=0,
                sharpe_ratio=0,
                calmar_ratio=0,
                avg_trade_duration=0,
                regime_performance={},
            )

        # Basic metrics
        total_trades = len(all_trades)
        winning_trades = [t for t in all_trades if t.pnl > 0]
        losing_trades = [t for t in all_trades if t.pnl < 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Drawdown calculation
        max_drawdown = self._calculate_max_drawdown(all_trades)

        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(returns_by_period)
        calmar_ratio = abs(total_return / max_drawdown) if max_drawdown != 0 else 0

        # Trade duration
        trade_durations = []
        for trade in all_trades:
            if trade.entry_time and trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                trade_durations.append(duration)

        avg_trade_duration = (
            sum(trade_durations) / len(trade_durations) if trade_durations else 0
        )

        # Regime performance analysis
        regime_performance = self._analyze_regime_performance(results)

        return ValidationMetrics(
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            calmar_ratio=calmar_ratio,
            avg_trade_duration=avg_trade_duration,
            regime_performance=regime_performance,
        )

    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """Calculate maximum drawdown."""

        if not trades:
            return 0.0

        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min)

        # Calculate running equity curve
        running_balance = 10000  # Starting balance
        peak_balance = running_balance
        max_drawdown = 0

        for trade in sorted_trades:
            trade_pnl = trade.pnl or 0.0  # Handle None values
            running_balance += trade_pnl

            if running_balance > peak_balance:
                peak_balance = running_balance

            drawdown = (peak_balance - running_balance) / peak_balance
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio."""

        if len(returns) < 2:
            return 0

        import numpy as np

        returns_array = np.array(returns)
        excess_returns = returns_array  # Assuming risk-free rate = 0

        if np.std(excess_returns) == 0:
            return 0

        return float(np.mean(excess_returns) / np.std(excess_returns))

    def _analyze_regime_performance(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze performance by market regime."""

        regime_trades = {}

        for result_data in results:
            result = result_data["result"]

            # Group trades by regime (simplified - could be enhanced)
            for trade in result.trades:
                regime = "unknown"  # Would need regime detection per trade

                if regime not in regime_trades:
                    regime_trades[regime] = []
                regime_trades[regime].append(trade)

        regime_performance = {}
        for regime, trades in regime_trades.items():
            if trades:
                total_pnl = sum(t.pnl for t in trades)
                win_rate = len([t for t in trades if t.pnl > 0]) / len(trades)

                regime_performance[regime] = {
                    "total_trades": len(trades),
                    "total_pnl": total_pnl,
                    "win_rate": win_rate,
                }

        return regime_performance

    def _check_validation_criteria(
        self, metrics: ValidationMetrics, config: ValidationConfig
    ) -> Tuple[bool, List[str]]:
        """Check if strategy meets validation criteria."""

        failed_criteria = []

        if metrics.total_trades < config.min_trades_threshold:
            failed_criteria.append(
                f"Insufficient trades: {metrics.total_trades} < {config.min_trades_threshold}"
            )

        if metrics.max_drawdown > config.max_drawdown_threshold:
            failed_criteria.append(
                f"Excessive drawdown: {metrics.max_drawdown:.2%} > {config.max_drawdown_threshold:.2%}"
            )

        if metrics.win_rate < config.min_win_rate_threshold:
            failed_criteria.append(
                f"Low win rate: {metrics.win_rate:.2%} < {config.min_win_rate_threshold:.2%}"
            )

        if metrics.profit_factor < config.min_profit_factor_threshold:
            failed_criteria.append(
                f"Low profit factor: {metrics.profit_factor:.2f} < {config.min_profit_factor_threshold:.2f}"
            )

        validation_passed = len(failed_criteria) == 0

        return validation_passed, failed_criteria

    def _generate_recommendations(
        self, metrics: ValidationMetrics, failed_criteria: List[str]
    ) -> List[str]:
        """Generate optimization recommendations."""

        recommendations = []

        if metrics.total_trades < 50:
            recommendations.append(
                "Consider adjusting signal sensitivity to generate more trades"
            )

        if metrics.max_drawdown > 0.15:
            recommendations.append(
                "Implement stricter risk management or position sizing"
            )

        if metrics.win_rate < 0.4:
            recommendations.append("Review entry criteria and signal quality")

        if metrics.profit_factor < 1.3:
            recommendations.append("Optimize stop-loss and take-profit levels")

        if metrics.sharpe_ratio < 0.5:
            recommendations.append(
                "Strategy produces inconsistent returns - consider smoothing techniques"
            )

        return recommendations

    def _prepare_detailed_results(
        self, results: List[Dict[str, Any]], metrics: ValidationMetrics
    ) -> Dict[str, Any]:
        """Prepare detailed results summary."""

        return {
            "summary": {
                "total_backtests": len(results),
                "successful_backtests": len([r for r in results if r["result"].trades]),
                "total_trades": metrics.total_trades,
                "average_trades_per_backtest": (
                    metrics.total_trades / len(results) if results else 0
                ),
            },
            "by_pair": self._summarize_by_pair(results),
            "by_timeframe": self._summarize_by_timeframe(results),
            "by_period": self._summarize_by_period(results),
        }

    def _summarize_by_pair(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Summarize results by currency pair."""

        by_pair = {}
        for result_data in results:
            pair = result_data["pair"]
            result = result_data["result"]

            if pair not in by_pair:
                by_pair[pair] = {"trades": 0, "pnl": 0}

            by_pair[pair]["trades"] += len(result.trades)
            by_pair[pair]["pnl"] += sum(t.pnl for t in result.trades)

        return by_pair

    def _summarize_by_timeframe(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Summarize results by timeframe."""

        by_timeframe = {}
        for result_data in results:
            timeframe = result_data["timeframe"]
            result = result_data["result"]

            if timeframe not in by_timeframe:
                by_timeframe[timeframe] = {"trades": 0, "pnl": 0}

            by_timeframe[timeframe]["trades"] += len(result.trades)
            by_timeframe[timeframe]["pnl"] += sum(t.pnl for t in result.trades)

        return by_timeframe

    def _summarize_by_period(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Summarize results by time period."""

        by_period = {}
        for result_data in results:
            period_key = f"{result_data['period'][0].strftime('%Y-%m')} to {result_data['period'][1].strftime('%Y-%m')}"
            result = result_data["result"]

            if period_key not in by_period:
                by_period[period_key] = {"trades": 0, "pnl": 0}

            by_period[period_key]["trades"] += len(result.trades)
            by_period[period_key]["pnl"] += sum(t.pnl for t in result.trades)

        return by_period


# Global validation pipeline instance
validation_pipeline = ValidationPipeline()
