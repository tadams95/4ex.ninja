"""
Regime Performance Analyzer for Multi-Regime Strategy Optimization.

This module analyzes strategy performance across different market regimes,
providing insights for regime-specific parameter optimization.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from .regime_detector import MarketRegime

logger = logging.getLogger(__name__)


class RegimePerformanceAnalyzer:
    """
    Analyzes strategy performance across different market regimes.

    Provides regime-specific performance metrics and optimization insights
    for swing trading strategies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the regime performance analyzer."""
        self.config = config or self._get_default_config()
        logger.info("RegimePerformanceAnalyzer initialized successfully")

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "regime_analysis": {
                "min_trades_per_regime": 10,
                "confidence_threshold": 0.8,
                "regime_transition_window_hours": 24,
                "performance_attribution_window_days": 30,
            }
        }

    async def analyze_regime_performance(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[MarketRegime, Any]:
        """
        Analyze strategy performance across different market regimes.

        Args:
            strategy_results: DataFrame with strategy trades and returns
            market_data: Dictionary of market data by currency pair

        Returns:
            Dictionary of performance metrics by regime
        """
        try:
            logger.info("Starting regime performance analysis")

            # Classify trades by market regime
            regime_classified_trades = await self._classify_trades_by_regime(
                strategy_results, market_data
            )

            # Calculate performance metrics for each regime
            regime_performance = {}
            for regime in MarketRegime:
                if regime == MarketRegime.UNCERTAIN:
                    continue

                regime_trades = regime_classified_trades.get(regime, pd.DataFrame())
                if (
                    not regime_trades.empty
                    and len(regime_trades)
                    >= self.config["regime_analysis"]["min_trades_per_regime"]
                ):
                    performance_metrics = self._calculate_regime_performance_metrics(
                        regime_trades
                    )
                    regime_performance[regime] = performance_metrics
                else:
                    logger.warning(
                        f"Insufficient trades for {regime.value} regime analysis"
                    )

            logger.info(
                f"Regime performance analysis completed for {len(regime_performance)} regimes"
            )
            return regime_performance

        except Exception as e:
            logger.error(f"Error in regime performance analysis: {e}")
            return {}

    async def _classify_trades_by_regime(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[MarketRegime, pd.DataFrame]:
        """Classify trades by the market regime when they occurred."""
        try:
            regime_trades = {regime: pd.DataFrame() for regime in MarketRegime}

            if strategy_results.empty:
                return regime_trades

            # For each trade, determine the market regime at trade time
            for _, trade in strategy_results.iterrows():
                trade_time = trade["timestamp"]
                currency_pair = trade.get("currency_pair", "EURUSD")

                # Get market regime classification for this trade
                # This is a simplified implementation - in production would use regime detector
                regime = self._classify_trade_regime(
                    trade_time, currency_pair, market_data
                )

                # Add trade to appropriate regime bucket
                if regime in regime_trades:
                    regime_trades[regime] = pd.concat(
                        [regime_trades[regime], pd.DataFrame([trade])],
                        ignore_index=True,
                    )

            return regime_trades

        except Exception as e:
            logger.error(f"Error classifying trades by regime: {e}")
            return {regime: pd.DataFrame() for regime in MarketRegime}

    def _classify_trade_regime(
        self,
        trade_time: datetime,
        currency_pair: str,
        market_data: Dict[str, pd.DataFrame],
    ) -> MarketRegime:
        """
        Classify the market regime for a specific trade.

        This is a simplified implementation using basic market indicators.
        In production, this would integrate with the regime detector.
        """
        try:
            # Get market data around trade time
            if currency_pair not in market_data:
                return MarketRegime.UNCERTAIN

            pair_data = market_data[currency_pair]
            if pair_data.empty:
                return MarketRegime.UNCERTAIN

            # Find data point closest to trade time
            if "timestamp" in pair_data.columns:
                time_diff = abs(pair_data["timestamp"] - trade_time)
                closest_idx = time_diff.idxmin()

                # Calculate basic indicators for regime classification
                window_size = 20
                # Ensure closest_idx is integer for arithmetic operations
                closest_idx_int = (
                    int(closest_idx)
                    if isinstance(closest_idx, (int, np.integer))
                    else 0
                )
                start_idx = max(0, closest_idx_int - window_size)
                end_idx = min(len(pair_data), closest_idx_int + 1)

                data_window = pair_data.iloc[start_idx:end_idx]

                if len(data_window) < 10:
                    return MarketRegime.UNCERTAIN

                # Simple regime classification based on price action
                volatility = data_window["close"].pct_change().std()
                price_range = (
                    data_window["high"].max() - data_window["low"].min()
                ) / data_window["close"].mean()

                # Determine trend strength
                sma_short = data_window["close"].rolling(5).mean().iloc[-1]
                sma_long = data_window["close"].rolling(10).mean().iloc[-1]
                current_price = data_window["close"].iloc[-1]

                is_trending = abs((sma_short - sma_long) / current_price) > 0.001
                is_high_volatility = volatility > 0.01 or price_range > 0.02

                # Classify regime
                if is_trending:
                    return (
                        MarketRegime.TRENDING_HIGH_VOL
                        if is_high_volatility
                        else MarketRegime.TRENDING_LOW_VOL
                    )
                else:
                    return (
                        MarketRegime.RANGING_HIGH_VOL
                        if is_high_volatility
                        else MarketRegime.RANGING_LOW_VOL
                    )

            return MarketRegime.UNCERTAIN

        except Exception as e:
            logger.error(f"Error classifying trade regime: {e}")
            return MarketRegime.UNCERTAIN

    def _calculate_regime_performance_metrics(
        self, regime_trades: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a specific regime."""
        try:
            if regime_trades.empty:
                return self._get_zero_regime_metrics()

            # Basic performance calculations
            returns = (
                regime_trades["pnl_pct"].dropna()
                if "pnl_pct" in regime_trades.columns
                else pd.Series()
            )
            pnl = (
                regime_trades["pnl"].dropna()
                if "pnl" in regime_trades.columns
                else pd.Series()
            )

            if returns.empty and pnl.empty:
                return self._get_zero_regime_metrics()

            # Use returns if available, otherwise calculate from PnL
            if not returns.empty:
                try:
                    # Calculate cumulative return robustly
                    cumulative_return = (1 + returns).prod()
                    # Convert to standard Python float to avoid pandas scalar issues
                    total_return = float(str(cumulative_return)) - 1.0
                except (TypeError, ValueError, AttributeError):
                    total_return = 0.0
            elif not pnl.empty:
                total_return = float(
                    pnl.sum() / abs(pnl.iloc[0])
                    if len(pnl) > 0 and pnl.iloc[0] != 0
                    else 0
                )
            else:
                total_return = 0.0

            # Calculate volatility
            if not returns.empty:
                volatility = float(returns.std())
            else:
                volatility = 0.0

            # Win rate and profit factor
            winning_trades = (
                regime_trades[regime_trades["pnl"] > 0]
                if "pnl" in regime_trades.columns
                else pd.DataFrame()
            )
            losing_trades = (
                regime_trades[regime_trades["pnl"] < 0]
                if "pnl" in regime_trades.columns
                else pd.DataFrame()
            )

            win_rate = (
                float(len(winning_trades) / len(regime_trades))
                if len(regime_trades) > 0
                else 0.0
            )

            gross_profit = (
                float(winning_trades["pnl"].sum()) if not winning_trades.empty else 0.0
            )
            gross_loss = (
                float(abs(losing_trades["pnl"].sum()))
                if not losing_trades.empty
                else 1.0
            )
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

            # Sharpe ratio (simplified)
            risk_free_rate = 0.02 / 252  # Daily risk-free rate
            if not returns.empty and volatility > 0:
                excess_return = returns.mean() - risk_free_rate
                sharpe_ratio = float(excess_return / volatility * np.sqrt(252))
            else:
                sharpe_ratio = 0.0

            # Maximum drawdown
            if not returns.empty:
                cumulative_returns = (1 + returns).cumprod()
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = float(abs(drawdown.min()))
            else:
                max_drawdown = 0.0

            # Trading frequency and duration analysis
            trade_count = len(regime_trades)

            # Average trade duration if available
            if (
                "entry_time" in regime_trades.columns
                and "exit_time" in regime_trades.columns
            ):
                durations = pd.to_datetime(regime_trades["exit_time"]) - pd.to_datetime(
                    regime_trades["entry_time"]
                )
                avg_trade_duration_hours = float(
                    durations.mean().total_seconds() / 3600
                )
            else:
                avg_trade_duration_hours = 0.0

            return {
                "total_return": total_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "trade_count": trade_count,
                "avg_trade_duration_hours": avg_trade_duration_hours,
                "gross_profit": gross_profit,
                "gross_loss": gross_loss,
            }

        except Exception as e:
            logger.error(f"Error calculating regime performance metrics: {e}")
            return self._get_zero_regime_metrics()

    def _get_zero_regime_metrics(self) -> Dict[str, Any]:
        """Return zero metrics for error cases."""
        return {
            "total_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "trade_count": 0,
            "avg_trade_duration_hours": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
        }

    async def analyze_regime_transitions(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Analyze strategy performance during regime transitions.

        This helps identify if the strategy struggles during regime changes.
        """
        try:
            logger.info("Analyzing regime transition performance")

            # Identify regime transition periods
            transition_periods = self._identify_regime_transitions(market_data)

            # Filter trades that occurred during transitions
            transition_trades = self._filter_transition_trades(
                strategy_results, transition_periods
            )

            # Calculate transition performance metrics
            transition_performance = self._calculate_regime_performance_metrics(
                transition_trades
            )

            # Compare with overall performance
            overall_performance = self._calculate_regime_performance_metrics(
                strategy_results
            )

            return {
                "transition_performance": transition_performance,
                "overall_performance": overall_performance,
                "transition_periods_count": len(transition_periods),
                "transition_trades_count": len(transition_trades),
                "performance_impact": self._calculate_transition_impact(
                    transition_performance, overall_performance
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing regime transitions: {e}")
            return {}

    def _identify_regime_transitions(
        self, market_data: Dict[str, pd.DataFrame]
    ) -> List[tuple]:
        """Identify periods of regime transitions."""
        # Simplified implementation - in production would use regime detector
        # For now, return placeholder transition periods
        transitions = []

        try:
            for pair, data in market_data.items():
                if data.empty or "timestamp" not in data.columns:
                    continue

                # Look for high volatility periods as proxy for transitions
                if "close" in data.columns:
                    data["volatility"] = data["close"].pct_change().rolling(20).std()
                    high_vol_threshold = data["volatility"].quantile(0.9)

                    high_vol_periods = data[data["volatility"] > high_vol_threshold]
                    for _, period in high_vol_periods.iterrows():
                        start_time = period["timestamp"] - timedelta(hours=12)
                        end_time = period["timestamp"] + timedelta(hours=12)
                        transitions.append((start_time, end_time))

        except Exception as e:
            logger.error(f"Error identifying regime transitions: {e}")

        return transitions

    def _filter_transition_trades(
        self, strategy_results: pd.DataFrame, transition_periods: List[tuple]
    ) -> pd.DataFrame:
        """Filter trades that occurred during regime transitions."""
        if strategy_results.empty or not transition_periods:
            return pd.DataFrame()

        transition_trades = pd.DataFrame()

        try:
            for start_time, end_time in transition_periods:
                period_trades = strategy_results[
                    (strategy_results["timestamp"] >= start_time)
                    & (strategy_results["timestamp"] <= end_time)
                ]
                transition_trades = pd.concat(
                    [transition_trades, period_trades], ignore_index=True
                )

        except Exception as e:
            logger.error(f"Error filtering transition trades: {e}")

        return transition_trades

    def _calculate_transition_impact(
        self,
        transition_performance: Dict[str, Any],
        overall_performance: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate the impact of regime transitions on performance."""
        try:
            impact = {}

            for metric in ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]:
                if metric in transition_performance and metric in overall_performance:
                    overall_value = overall_performance[metric]
                    transition_value = transition_performance[metric]

                    if overall_value != 0:
                        impact[f"{metric}_impact"] = (
                            transition_value - overall_value
                        ) / overall_value
                    else:
                        impact[f"{metric}_impact"] = 0.0

            return impact

        except Exception as e:
            logger.error(f"Error calculating transition impact: {e}")
            return {}
