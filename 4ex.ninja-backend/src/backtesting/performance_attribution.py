"""
Performance Attribution Analysis Engine for Multi-Regime Strategy Optimization.

This module provides comprehensive performance attribution analysis across different
market regimes, enabling strategy optimization and parameter tuning for swing trading.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

from .regime_detector import RegimeDetector, MarketRegime, RegimeDetectionResult
from .regime_performance_analyzer import RegimePerformanceAnalyzer
from .factor_analysis import FactorAnalyzer
from .economic_impact_analyzer import EconomicEventAnalyzer
from .session_performance_analyzer import SessionPerformanceAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Core performance metrics for attribution analysis."""

    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float
    trades_count: int


@dataclass
class AttributionResult:
    """Performance attribution analysis result."""

    timestamp: datetime
    overall_performance: PerformanceMetrics
    regime_attribution: Dict[MarketRegime, PerformanceMetrics]
    factor_attribution: Dict[str, float]
    economic_impact: Dict[str, float]
    session_attribution: Dict[str, PerformanceMetrics]
    optimization_recommendations: List[str]


class PerformanceAttributionEngine:
    """
    Main performance attribution engine for multi-regime analysis.

    Coordinates performance analysis across different market regimes and provides
    optimization insights for swing trading strategies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the performance attribution engine."""
        self.config = config or self._get_default_config()

        # Initialize analysis components
        self.regime_detector = RegimeDetector()
        self.regime_analyzer = RegimePerformanceAnalyzer(self.config)
        self.factor_analyzer = FactorAnalyzer(self.config)
        self.economic_analyzer = EconomicEventAnalyzer(self.config)
        self.session_analyzer = SessionPerformanceAnalyzer(self.config)

        logger.info("PerformanceAttributionEngine initialized successfully")

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration for performance attribution."""
        return {
            "performance_attribution": {
                "risk_free_rate": 0.02,  # 2% annual risk-free rate
                "target_return": 0.15,  # 15% target annual return
                "confidence_level": 0.95,
                "attribution_lookback_days": 252,  # 1 year
                "min_regime_trades": 10,
                "regime_stability_threshold": 0.8,
            },
            "optimization": {
                "parameter_ranges": {
                    "ma_short": [5, 10, 15, 20],
                    "ma_long": [20, 30, 50, 100],
                    "risk_per_trade": [0.01, 0.02, 0.03],
                },
                "walk_forward_periods": 12,  # months
                "out_of_sample_ratio": 0.2,
            },
        }

    async def analyze_performance(
        self,
        strategy_results: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AttributionResult:
        """
        Perform comprehensive performance attribution analysis.

        Args:
            strategy_results: DataFrame with strategy trades and returns
            market_data: Dictionary of market data by currency pair
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            AttributionResult with comprehensive performance breakdown
        """
        try:
            logger.info("Starting performance attribution analysis")

            # Set date range if not provided
            if start_date is None:
                start_date = strategy_results["timestamp"].min()
            if end_date is None:
                end_date = strategy_results["timestamp"].max()

            # Ensure dates are datetime objects
            if start_date is None:
                start_date = datetime.now() - timedelta(days=365)
            if end_date is None:
                end_date = datetime.now()

            # Filter data to date range
            filtered_results = self._filter_data_by_date(
                strategy_results, start_date, end_date
            )

            # Calculate overall performance metrics
            overall_performance = self._calculate_overall_performance(filtered_results)

            # Run parallel attribution analysis
            attribution_tasks = [
                self.regime_analyzer.analyze_regime_performance(
                    filtered_results, market_data
                ),
                self.factor_analyzer.analyze_factor_attribution(
                    filtered_results, market_data
                ),
                self.economic_analyzer.analyze_economic_impact(
                    filtered_results, market_data
                ),
                self.session_analyzer.analyze_session_performance(
                    filtered_results, market_data
                ),
            ]

            results = await asyncio.gather(*attribution_tasks)
            (
                regime_attribution,
                factor_attribution,
                economic_impact,
                session_attribution,
            ) = results

            # Generate optimization recommendations
            optimization_recommendations = self._generate_optimization_recommendations(
                overall_performance,
                regime_attribution,
                factor_attribution,
                economic_impact,
                session_attribution,
            )

            # Create attribution result
            attribution_result = AttributionResult(
                timestamp=datetime.now(),
                overall_performance=overall_performance,
                regime_attribution=regime_attribution,
                factor_attribution=factor_attribution,
                economic_impact=economic_impact,
                session_attribution=session_attribution,
                optimization_recommendations=optimization_recommendations,
            )

            logger.info("Performance attribution analysis completed successfully")
            return attribution_result

        except Exception as e:
            logger.error(f"Error in performance attribution analysis: {e}")
            raise

    def _filter_data_by_date(
        self, data: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Filter DataFrame by date range."""
        return data[
            (data["timestamp"] >= start_date) & (data["timestamp"] <= end_date)
        ].copy()

    def _calculate_overall_performance(
        self, strategy_results: pd.DataFrame
    ) -> PerformanceMetrics:
        """Calculate overall performance metrics."""
        try:
            if strategy_results.empty:
                return self._get_zero_performance_metrics()

            # Calculate returns
            returns = strategy_results["pnl_pct"].dropna()
            if returns.empty:
                return self._get_zero_performance_metrics()

            # Basic calculations - use simple math to avoid pandas type issues
            if len(returns) > 0:
                returns_product = 1.0
                for ret in returns:
                    returns_product *= 1 + ret
                total_return = returns_product - 1.0

                trading_days = len(returns)
                if trading_days > 0:
                    annualized_return = (1 + total_return) ** (252 / trading_days) - 1
                else:
                    annualized_return = 0.0

                volatility = float(returns.std() * np.sqrt(252))
            else:
                total_return = 0.0
                annualized_return = 0.0
                volatility = 0.0

            # Risk metrics
            risk_free_rate = self.config["performance_attribution"]["risk_free_rate"]
            excess_returns = returns - risk_free_rate / 252
            sharpe_ratio = (
                excess_returns.mean() / returns.std() * np.sqrt(252)
                if returns.std() > 0
                else 0
            )

            # Drawdown calculation
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = abs(drawdown.min())

            # Trade statistics
            winning_trades = strategy_results[strategy_results["pnl"] > 0]
            losing_trades = strategy_results[strategy_results["pnl"] < 0]

            win_rate = (
                len(winning_trades) / len(strategy_results)
                if len(strategy_results) > 0
                else 0
            )

            gross_profit = (
                winning_trades["pnl"].sum() if not winning_trades.empty else 0
            )
            gross_loss = (
                abs(losing_trades["pnl"].sum()) if not losing_trades.empty else 1
            )
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

            # Calmar and Sortino ratios
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0

            downside_returns = returns[returns < 0]
            downside_deviation = (
                downside_returns.std() * np.sqrt(252)
                if not downside_returns.empty
                else 0.01
            )
            sortino_ratio = (
                (annualized_return - risk_free_rate) / downside_deviation
                if downside_deviation > 0
                else 0
            )

            return PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                trades_count=len(strategy_results),
            )

        except Exception as e:
            logger.error(f"Error calculating overall performance: {e}")
            return self._get_zero_performance_metrics()

    def _get_zero_performance_metrics(self) -> PerformanceMetrics:
        """Return zero performance metrics for error cases."""
        return PerformanceMetrics(
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            calmar_ratio=0.0,
            sortino_ratio=0.0,
            trades_count=0,
        )

    def _generate_optimization_recommendations(
        self,
        overall_performance: PerformanceMetrics,
        regime_attribution: Dict[MarketRegime, PerformanceMetrics],
        factor_attribution: Dict[str, float],
        economic_impact: Dict[str, float],
        session_attribution: Dict[str, PerformanceMetrics],
    ) -> List[str]:
        """Generate optimization recommendations based on attribution analysis."""
        recommendations = []

        try:
            # Overall performance recommendations
            if overall_performance.sharpe_ratio < 1.0:
                recommendations.append(
                    "Consider improving risk-adjusted returns (Sharpe ratio < 1.0)"
                )

            if overall_performance.max_drawdown > 0.15:
                recommendations.append(
                    "Reduce maximum drawdown through better risk management"
                )

            if overall_performance.win_rate < 0.4:
                recommendations.append(
                    "Improve trade selection criteria to increase win rate"
                )

            # Regime-specific recommendations
            best_regime = None
            worst_regime = None
            best_sharpe = -999
            worst_sharpe = 999

            for regime, metrics in regime_attribution.items():
                if metrics.sharpe_ratio > best_sharpe:
                    best_sharpe = metrics.sharpe_ratio
                    best_regime = regime
                if metrics.sharpe_ratio < worst_sharpe:
                    worst_sharpe = metrics.sharpe_ratio
                    worst_regime = regime

            if best_regime and worst_regime:
                recommendations.append(
                    f"Strategy performs best in {best_regime.value} conditions"
                )
                recommendations.append(
                    f"Consider reducing exposure during {worst_regime.value} conditions"
                )

            # Factor attribution recommendations
            if factor_attribution:
                dominant_factor = max(
                    factor_attribution.items(), key=lambda x: abs(x[1])
                )
                if abs(dominant_factor[1]) > 0.3:
                    recommendations.append(
                        f"Strategy heavily influenced by {dominant_factor[0]} factor"
                    )

            # Economic impact recommendations
            if economic_impact:
                high_impact_events = [
                    event
                    for event, impact in economic_impact.items()
                    if abs(impact) > 0.1
                ]
                if high_impact_events:
                    recommendations.append(
                        f"High impact from economic events: {', '.join(high_impact_events)}"
                    )

            # Session performance recommendations
            if session_attribution:
                session_performances = [
                    (session, metrics.sharpe_ratio)
                    for session, metrics in session_attribution.items()
                ]
                best_session = max(session_performances, key=lambda x: x[1])
                if best_session[1] > 1.5:
                    recommendations.append(
                        f"Consider focusing trading during {best_session[0]} session"
                    )

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            recommendations.append(
                "Unable to generate specific recommendations due to analysis error"
            )

        return recommendations

    async def run_multi_regime_backtest(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Run multi-regime backtesting with regime-aware parameter optimization.

        This is a simplified framework for regime-aware backtesting.
        """
        try:
            logger.info("Starting multi-regime backtesting")

            # Detect regimes across the date range
            regime_periods = await self._detect_regime_periods(
                market_data, start_date, end_date
            )

            # Run backtest for each regime with optimized parameters
            regime_results = {}
            for regime, periods in regime_periods.items():
                regime_performance = await self._backtest_regime_periods(
                    strategy_config, market_data, periods, regime
                )
                regime_results[regime] = regime_performance

            # Aggregate results
            aggregate_results = self._aggregate_regime_results(regime_results)

            logger.info("Multi-regime backtesting completed")
            return {
                "regime_results": regime_results,
                "aggregate_performance": aggregate_results,
                "regime_periods": regime_periods,
            }

        except Exception as e:
            logger.error(f"Error in multi-regime backtesting: {e}")
            raise

    async def _detect_regime_periods(
        self,
        market_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[MarketRegime, List[Tuple[datetime, datetime]]]:
        """Detect regime periods within the date range."""
        # This is a simplified implementation
        # In production, this would use the regime detector with historical data
        regime_periods = {
            MarketRegime.TRENDING_HIGH_VOL: [],
            MarketRegime.TRENDING_LOW_VOL: [],
            MarketRegime.RANGING_HIGH_VOL: [],
            MarketRegime.RANGING_LOW_VOL: [],
        }

        # For now, return equal periods for each regime as placeholder
        total_days = (end_date - start_date).days
        period_length = total_days // 4

        current_date = start_date
        for regime in regime_periods.keys():
            period_end = current_date + timedelta(days=period_length)
            regime_periods[regime].append((current_date, period_end))
            current_date = period_end

        return regime_periods

    async def _backtest_regime_periods(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, pd.DataFrame],
        periods: List[Tuple[datetime, datetime]],
        regime: MarketRegime,
    ) -> PerformanceMetrics:
        """Backtest strategy for specific regime periods."""
        # This is a placeholder for regime-specific backtesting
        # In production, this would integrate with the actual backtesting engine

        # Return placeholder performance metrics
        return PerformanceMetrics(
            total_return=0.1,
            annualized_return=0.12,
            volatility=0.15,
            sharpe_ratio=0.8,
            max_drawdown=0.05,
            win_rate=0.55,
            profit_factor=1.2,
            calmar_ratio=2.4,
            sortino_ratio=1.1,
            trades_count=50,
        )

    def _aggregate_regime_results(
        self, regime_results: Dict[MarketRegime, PerformanceMetrics]
    ) -> PerformanceMetrics:
        """Aggregate performance across all regimes."""
        if not regime_results:
            return self._get_zero_performance_metrics()

        # Simple aggregation - in production this would be weighted by time periods
        total_return = sum(
            metrics.total_return for metrics in regime_results.values()
        ) / len(regime_results)
        annualized_return = sum(
            metrics.annualized_return for metrics in regime_results.values()
        ) / len(regime_results)
        volatility = sum(
            metrics.volatility for metrics in regime_results.values()
        ) / len(regime_results)
        sharpe_ratio = sum(
            metrics.sharpe_ratio for metrics in regime_results.values()
        ) / len(regime_results)
        max_drawdown = max(metrics.max_drawdown for metrics in regime_results.values())
        win_rate = sum(metrics.win_rate for metrics in regime_results.values()) / len(
            regime_results
        )
        profit_factor = sum(
            metrics.profit_factor for metrics in regime_results.values()
        ) / len(regime_results)
        calmar_ratio = sum(
            metrics.calmar_ratio for metrics in regime_results.values()
        ) / len(regime_results)
        sortino_ratio = sum(
            metrics.sortino_ratio for metrics in regime_results.values()
        ) / len(regime_results)
        trades_count = sum(metrics.trades_count for metrics in regime_results.values())

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            trades_count=trades_count,
        )
