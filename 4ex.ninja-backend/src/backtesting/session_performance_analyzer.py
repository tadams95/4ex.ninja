"""
Session Performance Analyzer for Trading Time Optimization.

This module analyzes strategy performance across different trading sessions
to optimize trading times and session-based parameter adjustments.
"""

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class SessionPerformanceAnalyzer:
    """
    Analyzes strategy performance across different trading sessions.

    Provides insights into optimal trading times and session-based
    performance characteristics for swing trading strategies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the session performance analyzer."""
        self.config = config or self._get_default_config()
        logger.info("SessionPerformanceAnalyzer initialized successfully")

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "session_analysis": {
                "sessions": {
                    "Asian": {
                        "start_hour": 21,  # 9 PM UTC (6 AM JST)
                        "end_hour": 6,  # 6 AM UTC (3 PM JST)
                        "timezone": "Asia/Tokyo",
                        "major_pairs": ["USDJPY", "AUDJPY", "NZDJPY", "GBPJPY"],
                    },
                    "European": {
                        "start_hour": 7,  # 7 AM UTC (8 AM CET)
                        "end_hour": 16,  # 4 PM UTC (5 PM CET)
                        "timezone": "Europe/London",
                        "major_pairs": ["EURUSD", "GBPUSD", "EURGBP", "EURJPY"],
                    },
                    "American": {
                        "start_hour": 13,  # 1 PM UTC (8 AM EST)
                        "end_hour": 22,  # 10 PM UTC (5 PM EST)
                        "timezone": "America/New_York",
                        "major_pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD"],
                    },
                    "London_NY_Overlap": {
                        "start_hour": 13,  # 1 PM UTC
                        "end_hour": 16,  # 4 PM UTC
                        "timezone": "UTC",
                        "major_pairs": ["EURUSD", "GBPUSD", "USDJPY"],
                    },
                },
                "weekend_gap_analysis": True,
                "session_transition_analysis": True,
            }
        }

    async def analyze_session_performance(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Analyze strategy performance across different trading sessions.

        Args:
            strategy_results: DataFrame with strategy trades and returns
            market_data: Dictionary of market data by currency pair

        Returns:
            Dictionary of session performance metrics
        """
        try:
            logger.info("Starting session performance analysis")

            if strategy_results.empty:
                return {}

            session_performance = {}

            # Analyze performance for each trading session
            for session_name, session_config in self.config["session_analysis"][
                "sessions"
            ].items():
                session_trades = self._filter_trades_by_session(
                    strategy_results, session_config
                )

                if not session_trades.empty:
                    performance_metrics = self._calculate_session_performance(
                        session_trades, session_name
                    )
                    session_performance[session_name] = performance_metrics
                else:
                    logger.warning(f"No trades found for {session_name} session")

            # Analyze session transitions
            if self.config["session_analysis"]["session_transition_analysis"]:
                transition_analysis = await self._analyze_session_transitions(
                    strategy_results, market_data
                )
                session_performance["session_transitions"] = transition_analysis

            # Analyze weekend gaps
            if self.config["session_analysis"]["weekend_gap_analysis"]:
                weekend_analysis = await self._analyze_weekend_gaps(
                    strategy_results, market_data
                )
                session_performance["weekend_gaps"] = weekend_analysis

            logger.info(
                f"Session performance analysis completed for {len(session_performance)} sessions"
            )
            return session_performance

        except Exception as e:
            logger.error(f"Error in session performance analysis: {e}")
            return {}

    def _filter_trades_by_session(
        self, strategy_results: pd.DataFrame, session_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Filter trades that occurred during a specific trading session."""
        try:
            if strategy_results.empty or "timestamp" not in strategy_results.columns:
                return pd.DataFrame()

            start_hour = session_config["start_hour"]
            end_hour = session_config["end_hour"]

            # Convert timestamps to UTC hours
            strategy_results["utc_hour"] = strategy_results["timestamp"].dt.hour

            # Handle sessions that cross midnight (like Asian session)
            if start_hour > end_hour:
                # Session crosses midnight
                session_trades = strategy_results[
                    (strategy_results["utc_hour"] >= start_hour)
                    | (strategy_results["utc_hour"] < end_hour)
                ].copy()
            else:
                # Normal session within same day
                session_trades = strategy_results[
                    (strategy_results["utc_hour"] >= start_hour)
                    & (strategy_results["utc_hour"] < end_hour)
                ].copy()

            # Remove the temporary column
            if "utc_hour" in session_trades.columns:
                session_trades = session_trades.drop("utc_hour", axis=1)

            return session_trades

        except Exception as e:
            logger.error(f"Error filtering trades by session: {e}")
            return pd.DataFrame()

    def _calculate_session_performance(
        self, session_trades: pd.DataFrame, session_name: str
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a trading session."""
        try:
            if session_trades.empty:
                return self._get_zero_session_metrics()

            # Basic performance calculations
            total_trades = len(session_trades)

            # PnL calculations
            if "pnl" in session_trades.columns:
                total_pnl = float(session_trades["pnl"].sum())
                avg_pnl_per_trade = (
                    total_pnl / total_trades if total_trades > 0 else 0.0
                )

                # Win rate
                winning_trades = session_trades[session_trades["pnl"] > 0]
                losing_trades = session_trades[session_trades["pnl"] < 0]
                win_rate = (
                    len(winning_trades) / total_trades if total_trades > 0 else 0.0
                )

                # Profit factor
                gross_profit = (
                    float(winning_trades["pnl"].sum())
                    if not winning_trades.empty
                    else 0.0
                )
                gross_loss = (
                    float(abs(losing_trades["pnl"].sum()))
                    if not losing_trades.empty
                    else 1.0
                )
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
            else:
                total_pnl = 0.0
                avg_pnl_per_trade = 0.0
                win_rate = 0.0
                profit_factor = 0.0
                gross_profit = 0.0
                gross_loss = 0.0

            # Returns-based calculations
            if "pnl_pct" in session_trades.columns:
                returns = session_trades["pnl_pct"].dropna()
                if not returns.empty:
                    try:
                        prod_result = (1 + returns).prod()
                        # Convert pandas scalar to float, handling type issues
                        total_return = float(prod_result.real if hasattr(prod_result, "real") else prod_result) - 1.0  # type: ignore
                    except (ValueError, TypeError, AttributeError):
                        total_return = 0.0
                    volatility = float(returns.std())

                    # Sharpe ratio (simplified)
                    risk_free_rate = 0.02 / 252  # Daily risk-free rate
                    if volatility > 0:
                        excess_return = returns.mean() - risk_free_rate
                        sharpe_ratio = float(excess_return / volatility)
                    else:
                        sharpe_ratio = 0.0

                    # Maximum drawdown
                    cumulative_returns = (1 + returns).cumprod()
                    rolling_max = cumulative_returns.expanding().max()
                    drawdown = (cumulative_returns - rolling_max) / rolling_max
                    max_drawdown = float(abs(drawdown.min()))
                else:
                    total_return = 0.0
                    volatility = 0.0
                    sharpe_ratio = 0.0
                    max_drawdown = 0.0
            else:
                total_return = 0.0
                volatility = 0.0
                sharpe_ratio = 0.0
                max_drawdown = 0.0

            # Trade duration analysis
            if (
                "entry_time" in session_trades.columns
                and "exit_time" in session_trades.columns
            ):
                entry_times = pd.to_datetime(session_trades["entry_time"])
                exit_times = pd.to_datetime(session_trades["exit_time"])
                durations = exit_times - entry_times
                avg_trade_duration_hours = float(
                    durations.mean().total_seconds() / 3600
                )
            else:
                avg_trade_duration_hours = 0.0

            # Currency pair analysis
            if "currency_pair" in session_trades.columns:
                pair_performance = (
                    session_trades.groupby("currency_pair")["pnl"].sum().to_dict()
                )
                best_pair = (
                    max(pair_performance.items(), key=lambda x: x[1])[0]
                    if pair_performance
                    else "None"
                )
                worst_pair = (
                    min(pair_performance.items(), key=lambda x: x[1])[0]
                    if pair_performance
                    else "None"
                )
            else:
                pair_performance = {}
                best_pair = "None"
                worst_pair = "None"

            return {
                "session_name": session_name,
                "total_trades": total_trades,
                "total_pnl": total_pnl,
                "avg_pnl_per_trade": avg_pnl_per_trade,
                "total_return": total_return,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "sharpe_ratio": sharpe_ratio,
                "volatility": volatility,
                "max_drawdown": max_drawdown,
                "avg_trade_duration_hours": avg_trade_duration_hours,
                "gross_profit": gross_profit,
                "gross_loss": gross_loss,
                "best_performing_pair": best_pair,
                "worst_performing_pair": worst_pair,
                "pair_performance": pair_performance,
            }

        except Exception as e:
            logger.error(f"Error calculating session performance: {e}")
            return self._get_zero_session_metrics()

    def _get_zero_session_metrics(self) -> Dict[str, Any]:
        """Return zero metrics for error cases."""
        return {
            "session_name": "Unknown",
            "total_trades": 0,
            "total_pnl": 0.0,
            "avg_pnl_per_trade": 0.0,
            "total_return": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "avg_trade_duration_hours": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "best_performing_pair": "None",
            "worst_performing_pair": "None",
            "pair_performance": {},
        }

    async def _analyze_session_transitions(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze performance during session transitions."""
        try:
            logger.info("Analyzing session transition performance")

            transition_performance = {}

            # Define transition periods (1 hour before and after session changes)
            transitions = [
                {"name": "Asian_to_European", "start_hour": 6, "end_hour": 8},
                {"name": "European_to_American", "start_hour": 12, "end_hour": 14},
                {"name": "American_to_Asian", "start_hour": 21, "end_hour": 23},
            ]

            for transition in transitions:
                transition_trades = strategy_results[
                    (strategy_results["timestamp"].dt.hour >= transition["start_hour"])
                    & (strategy_results["timestamp"].dt.hour <= transition["end_hour"])
                ].copy()

                if not transition_trades.empty:
                    performance = self._calculate_session_performance(
                        transition_trades, transition["name"]
                    )
                    transition_performance[transition["name"]] = performance

            return transition_performance

        except Exception as e:
            logger.error(f"Error analyzing session transitions: {e}")
            return {}

    async def _analyze_weekend_gaps(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze impact of weekend gaps on strategy performance."""
        try:
            logger.info("Analyzing weekend gap impact")

            if strategy_results.empty:
                return {}

            # Identify trades that were open over weekends
            weekend_affected_trades = []

            for _, trade in strategy_results.iterrows():
                if "entry_time" in trade and "exit_time" in trade:
                    entry_time = pd.to_datetime(trade["entry_time"])
                    exit_time = pd.to_datetime(trade["exit_time"])

                    # Check if trade spans a weekend
                    current_time = entry_time
                    while current_time <= exit_time:
                        if current_time.weekday() in [5, 6]:  # Saturday or Sunday
                            weekend_affected_trades.append(trade)
                            break
                        current_time += timedelta(days=1)

            if not weekend_affected_trades:
                return {
                    "weekend_affected_trades": 0,
                    "impact": "No weekend trades found",
                }

            weekend_trades_df = pd.DataFrame(weekend_affected_trades)
            weekend_performance = self._calculate_session_performance(
                weekend_trades_df, "Weekend_Affected"
            )

            # Compare with non-weekend trades
            all_trade_ids = set(strategy_results.index)
            weekend_trade_ids = set(weekend_trades_df.index)
            non_weekend_trade_ids = all_trade_ids - weekend_trade_ids

            if non_weekend_trade_ids:
                non_weekend_trades = strategy_results.loc[list(non_weekend_trade_ids)]
                non_weekend_performance = self._calculate_session_performance(
                    non_weekend_trades, "Non_Weekend"
                )

                # Calculate impact
                pnl_impact = (
                    weekend_performance["avg_pnl_per_trade"]
                    - non_weekend_performance["avg_pnl_per_trade"]
                )

                win_rate_impact = (
                    weekend_performance["win_rate"]
                    - non_weekend_performance["win_rate"]
                )
            else:
                pnl_impact = 0.0
                win_rate_impact = 0.0
                non_weekend_performance = {}

            return {
                "weekend_affected_trades": len(weekend_affected_trades),
                "weekend_performance": weekend_performance,
                "non_weekend_performance": non_weekend_performance,
                "pnl_impact": pnl_impact,
                "win_rate_impact": win_rate_impact,
            }

        except Exception as e:
            logger.error(f"Error analyzing weekend gaps: {e}")
            return {}

    async def analyze_intraday_patterns(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Analyze intraday performance patterns by hour."""
        try:
            logger.info("Analyzing intraday performance patterns")

            if strategy_results.empty:
                return {}

            hourly_performance = {}

            # Group trades by hour of day
            strategy_results["hour"] = strategy_results["timestamp"].dt.hour

            for hour in range(24):
                hour_trades = strategy_results[strategy_results["hour"] == hour]

                if not hour_trades.empty:
                    performance = self._calculate_session_performance(
                        hour_trades, f"Hour_{hour:02d}"
                    )
                    hourly_performance[hour] = performance

            # Identify best and worst hours
            if hourly_performance:
                best_hour = max(
                    hourly_performance.items(), key=lambda x: x[1]["avg_pnl_per_trade"]
                )
                worst_hour = min(
                    hourly_performance.items(), key=lambda x: x[1]["avg_pnl_per_trade"]
                )

                # Calculate volatility by hour
                hourly_volatility = {}
                for hour, performance in hourly_performance.items():
                    hourly_volatility[hour] = performance["volatility"]

                return {
                    "hourly_performance": hourly_performance,
                    "best_hour": {"hour": best_hour[0], "performance": best_hour[1]},
                    "worst_hour": {"hour": worst_hour[0], "performance": worst_hour[1]},
                    "hourly_volatility": hourly_volatility,
                }
            else:
                return {}

        except Exception as e:
            logger.error(f"Error analyzing intraday patterns: {e}")
            return {}

    async def get_session_optimization_recommendations(
        self, session_performance: Dict[str, Any]
    ) -> List[str]:
        """Generate session-based optimization recommendations."""
        try:
            recommendations = []

            if not session_performance:
                return ["Insufficient data for session-based recommendations"]

            # Analyze session performance
            session_metrics = {}
            for session_name, metrics in session_performance.items():
                if isinstance(metrics, dict) and "avg_pnl_per_trade" in metrics:
                    session_metrics[session_name] = metrics

            if not session_metrics:
                return ["No valid session metrics found"]

            # Find best and worst performing sessions
            best_session = max(
                session_metrics.items(), key=lambda x: x[1]["avg_pnl_per_trade"]
            )
            worst_session = min(
                session_metrics.items(), key=lambda x: x[1]["avg_pnl_per_trade"]
            )

            recommendations.append(
                f"Best performing session: {best_session[0]} "
                f"(Avg PnL: {best_session[1]['avg_pnl_per_trade']:.4f})"
            )

            recommendations.append(
                f"Worst performing session: {worst_session[0]} "
                f"(Avg PnL: {worst_session[1]['avg_pnl_per_trade']:.4f})"
            )

            # Session-specific recommendations
            for session_name, metrics in session_metrics.items():
                if metrics["win_rate"] > 0.6:
                    recommendations.append(
                        f"Consider increasing position size during {session_name} "
                        f"(High win rate: {metrics['win_rate']:.2%})"
                    )
                elif metrics["win_rate"] < 0.4:
                    recommendations.append(
                        f"Consider reducing exposure during {session_name} "
                        f"(Low win rate: {metrics['win_rate']:.2%})"
                    )

                if metrics["volatility"] > 0.02:
                    recommendations.append(
                        f"High volatility detected in {session_name} - consider tighter stops"
                    )

            # Overlap recommendations
            if "London_NY_Overlap" in session_metrics:
                overlap_metrics = session_metrics["London_NY_Overlap"]
                if overlap_metrics["avg_pnl_per_trade"] > 0:
                    recommendations.append(
                        "London-NY overlap shows positive performance - consider focusing trades during this period"
                    )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating session optimization recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]
