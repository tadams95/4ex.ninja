"""
Report Generator for comprehensive backtesting reports.

Creates detailed performance reports, charts, and analysis summaries
integrating with existing Phase 2 infrastructure.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import logging

from .models import BacktestResult, Trade
from .validation_pipeline import ValidationResult, ValidationMetrics

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    include_charts: bool = True
    include_trade_list: bool = True
    include_recommendations: bool = True
    format: str = "json"  # json, csv, html
    export_path: Optional[str] = None


class ReportGenerator:
    """
    Comprehensive report generator for backtesting results.

    Creates detailed performance reports with analysis and recommendations.
    """

    def __init__(self):
        """Initialize report generator."""
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def generate_backtest_report(
        self, result: BacktestResult, config: Optional[ReportConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive backtest report.

        Args:
            result: Backtest result to analyze
            config: Report configuration

        Returns:
            Comprehensive report dictionary
        """
        if config is None:
            config = ReportConfig()

        logger.info(f"Generating report for {result.strategy_name}")

        # Calculate basic metrics
        basic_metrics = self._calculate_basic_metrics(result)

        # Calculate advanced metrics
        advanced_metrics = self._calculate_advanced_metrics(result)

        # Analyze trade patterns
        trade_analysis = self._analyze_trade_patterns(result.trades)

        # Generate risk analysis
        risk_analysis = self._analyze_risk_metrics(result.trades)

        # Time-based analysis
        time_analysis = self._analyze_time_patterns(result.trades)

        # Regime analysis (if available)
        regime_analysis = self._analyze_regime_performance(result)

        # Compile comprehensive report
        report = {
            "metadata": {
                "strategy_name": result.strategy_name,
                "report_generated": datetime.utcnow().isoformat(),
                "total_trades": len(result.trades),
                "report_version": "1.0",
            },
            "summary": {**basic_metrics, **advanced_metrics},
            "trade_analysis": trade_analysis,
            "risk_analysis": risk_analysis,
            "time_analysis": time_analysis,
            "regime_analysis": regime_analysis,
            "recommendations": self._generate_recommendations(
                result, basic_metrics, advanced_metrics
            ),
        }

        if config.include_trade_list:
            report["trade_details"] = self._format_trade_list(result.trades)

        # Export if path specified
        if config.export_path:
            self._export_report(report, config)

        return report

    def generate_validation_report(
        self, validation_result: ValidationResult, config: Optional[ReportConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate validation report.

        Args:
            validation_result: Validation result to report
            config: Report configuration

        Returns:
            Validation report dictionary
        """
        if config is None:
            config = ReportConfig()

        logger.info(
            f"Generating validation report for {validation_result.strategy_name}"
        )

        report = {
            "metadata": {
                "strategy_name": validation_result.strategy_name,
                "validation_passed": validation_result.validation_passed,
                "report_generated": datetime.utcnow().isoformat(),
                "report_type": "validation",
            },
            "validation_summary": {
                "overall_result": (
                    "PASSED" if validation_result.validation_passed else "FAILED"
                ),
                "failed_criteria": validation_result.failed_criteria,
                "key_metrics": {
                    "total_trades": validation_result.metrics.total_trades,
                    "win_rate": f"{validation_result.metrics.win_rate:.2%}",
                    "profit_factor": f"{validation_result.metrics.profit_factor:.2f}",
                    "max_drawdown": f"{validation_result.metrics.max_drawdown:.2%}",
                    "total_return": f"{validation_result.metrics.total_return:.2f}",
                    "sharpe_ratio": f"{validation_result.metrics.sharpe_ratio:.2f}",
                },
            },
            "detailed_metrics": self._format_validation_metrics(
                validation_result.metrics
            ),
            "recommendations": validation_result.recommendations,
            "detailed_results": validation_result.detailed_results,
        }

        # Export if path specified
        if config.export_path:
            self._export_report(report, config)

        return report

    def generate_comparison_report(
        self, results: List[BacktestResult], config: Optional[ReportConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate comparison report for multiple strategies.

        Args:
            results: List of backtest results to compare
            config: Report configuration

        Returns:
            Comparison report dictionary
        """
        if config is None:
            config = ReportConfig()

        logger.info(f"Generating comparison report for {len(results)} strategies")

        if not results:
            return {"error": "No results provided for comparison"}

        # Calculate metrics for each strategy
        strategy_metrics = {}
        for result in results:
            basic_metrics = self._calculate_basic_metrics(result)
            advanced_metrics = self._calculate_advanced_metrics(result)

            strategy_metrics[result.strategy_name] = {
                **basic_metrics,
                **advanced_metrics,
            }

        # Rank strategies
        rankings = self._rank_strategies(strategy_metrics)

        # Performance comparison
        performance_comparison = self._compare_performance(strategy_metrics)

        report = {
            "metadata": {
                "report_type": "comparison",
                "strategies_compared": [r.strategy_name for r in results],
                "report_generated": datetime.utcnow().isoformat(),
                "total_strategies": len(results),
            },
            "summary": {
                "best_overall": rankings["overall"][0] if rankings["overall"] else None,
                "most_profitable": (
                    rankings["profit"][0] if rankings["profit"] else None
                ),
                "least_risky": rankings["risk"][0] if rankings["risk"] else None,
                "most_consistent": (
                    rankings["consistency"][0] if rankings["consistency"] else None
                ),
            },
            "strategy_metrics": strategy_metrics,
            "rankings": rankings,
            "performance_comparison": performance_comparison,
            "recommendations": self._generate_comparison_recommendations(
                strategy_metrics
            ),
        }

        # Export if path specified
        if config.export_path:
            self._export_report(report, config)

        return report

    def _calculate_basic_metrics(self, result: BacktestResult) -> Dict[str, Any]:
        """Calculate basic performance metrics."""

        trades = result.trades
        if not trades:
            return {
                "total_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
            }

        total_trades = len(trades)
        total_pnl = sum(trade.pnl or 0 for trade in trades)

        winning_trades = [t for t in trades if (t.pnl or 0) > 0]
        losing_trades = [t for t in trades if (t.pnl or 0) < 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        avg_win = (
            sum(t.pnl or 0 for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0
        )
        avg_loss = (
            sum(t.pnl or 0 for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0
        )

        gross_profit = sum(t.pnl or 0 for t in winning_trades)
        gross_loss = abs(sum(t.pnl or 0 for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        return {
            "total_trades": total_trades,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 4),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
        }

    def _calculate_advanced_metrics(self, result: BacktestResult) -> Dict[str, Any]:
        """Calculate advanced performance metrics."""

        trades = result.trades
        if not trades:
            return {
                "max_drawdown": 0,
                "recovery_factor": 0,
                "expectancy": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
            }

        # Max drawdown calculation
        max_drawdown = self._calculate_max_drawdown(trades)

        # Recovery factor
        total_pnl = sum(trade.pnl or 0 for trade in trades)
        recovery_factor = abs(total_pnl / max_drawdown) if max_drawdown != 0 else 0

        # Expectancy
        win_rate = len([t for t in trades if (t.pnl or 0) > 0]) / len(trades)
        avg_win = sum(t.pnl or 0 for t in trades if (t.pnl or 0) > 0) / max(
            1, len([t for t in trades if (t.pnl or 0) > 0])
        )
        avg_loss = sum(t.pnl or 0 for t in trades if (t.pnl or 0) < 0) / max(
            1, len([t for t in trades if (t.pnl or 0) < 0])
        )
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        # Largest win/loss
        largest_win = max((t.pnl or 0 for t in trades), default=0)
        largest_loss = min((t.pnl or 0 for t in trades), default=0)

        # Consecutive wins/losses
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(
            trades
        )

        return {
            "max_drawdown": round(max_drawdown, 4),
            "recovery_factor": round(recovery_factor, 2),
            "expectancy": round(expectancy, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "consecutive_wins": consecutive_wins,
            "consecutive_losses": consecutive_losses,
        }

    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """Calculate maximum drawdown from trade sequence."""

        if not trades:
            return 0.0

        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min)

        running_balance = 10000  # Starting balance
        peak_balance = running_balance
        max_drawdown = 0

        for trade in sorted_trades:
            trade_pnl = trade.pnl or 0.0
            running_balance += trade_pnl

            if running_balance > peak_balance:
                peak_balance = running_balance

            drawdown = (peak_balance - running_balance) / peak_balance
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_consecutive_trades(self, trades: List[Trade]) -> tuple[int, int]:
        """Calculate maximum consecutive wins and losses."""

        if not trades:
            return 0, 0

        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min)

        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in sorted_trades:
            trade_pnl = trade.pnl or 0

            if trade_pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif trade_pnl < 0:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)

        return max_consecutive_wins, max_consecutive_losses

    def _analyze_trade_patterns(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze trade patterns and distributions."""

        if not trades:
            return {"message": "No trades to analyze"}

        # Trade distribution by result
        wins = len([t for t in trades if (t.pnl or 0) > 0])
        losses = len([t for t in trades if (t.pnl or 0) < 0])
        breakevens = len([t for t in trades if (t.pnl or 0) == 0])

        # Trade distribution by direction
        longs = len([t for t in trades if t.direction == "BUY"])
        shorts = len([t for t in trades if t.direction == "SELL"])

        # Trade distribution by pair
        pair_distribution = {}
        for trade in trades:
            pair = trade.pair
            if pair not in pair_distribution:
                pair_distribution[pair] = 0
            pair_distribution[pair] += 1

        return {
            "result_distribution": {
                "wins": wins,
                "losses": losses,
                "breakevens": breakevens,
            },
            "direction_distribution": {"longs": longs, "shorts": shorts},
            "pair_distribution": pair_distribution,
            "avg_holding_time": self._calculate_avg_holding_time(trades),
        }

    def _calculate_avg_holding_time(self, trades: List[Trade]) -> Dict[str, float]:
        """Calculate average holding time statistics."""

        durations = []
        for trade in trades:
            if trade.entry_time and trade.exit_time:
                duration = (
                    trade.exit_time - trade.entry_time
                ).total_seconds() / 3600  # hours
                durations.append(duration)

        if not durations:
            return {"hours": 0, "days": 0}

        avg_hours = sum(durations) / len(durations)
        return {"hours": round(avg_hours, 2), "days": round(avg_hours / 24, 2)}

    def _analyze_risk_metrics(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze risk-related metrics."""

        if not trades:
            return {"message": "No trades to analyze"}

        # Risk-reward ratios
        rr_ratios = []
        for trade in trades:
            if (
                hasattr(trade, "stop_loss")
                and hasattr(trade, "take_profit")
                and trade.entry_price
            ):
                # Calculate theoretical RR ratio
                if trade.direction == "BUY" and trade.stop_loss and trade.take_profit:
                    risk = trade.entry_price - trade.stop_loss
                    reward = trade.take_profit - trade.entry_price
                    if risk > 0:
                        rr_ratios.append(reward / risk)

        avg_rr_ratio = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0

        # Position sizing analysis
        position_sizes = [
            trade.position_size
            for trade in trades
            if hasattr(trade, "position_size") and trade.position_size
        ]
        avg_position_size = (
            sum(position_sizes) / len(position_sizes) if position_sizes else 0
        )

        return {
            "avg_risk_reward_ratio": round(avg_rr_ratio, 2),
            "total_rr_samples": len(rr_ratios),
            "avg_position_size": round(avg_position_size, 4),
            "position_size_range": {
                "min": min(position_sizes, default=0),
                "max": max(position_sizes, default=0),
            },
        }

    def _analyze_time_patterns(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze time-based trading patterns."""

        if not trades:
            return {"message": "No trades to analyze"}

        # Monthly distribution
        monthly_dist = {}
        daily_dist = {}
        hourly_dist = {}

        for trade in trades:
            if trade.entry_time:
                month = trade.entry_time.strftime("%Y-%m")
                day = trade.entry_time.strftime("%A")
                hour = trade.entry_time.hour

                monthly_dist[month] = monthly_dist.get(month, 0) + 1
                daily_dist[day] = daily_dist.get(day, 0) + 1
                hourly_dist[hour] = hourly_dist.get(hour, 0) + 1

        return {
            "monthly_distribution": monthly_dist,
            "daily_distribution": daily_dist,
            "hourly_distribution": hourly_dist,
        }

    def _analyze_regime_performance(self, result: BacktestResult) -> Dict[str, Any]:
        """Analyze performance by market regime."""

        # Simplified regime analysis - could be enhanced with actual regime detection
        return {
            "message": "Regime analysis available in validation reports",
            "total_trades": len(result.trades),
        }

    def _generate_recommendations(
        self,
        result: BacktestResult,
        basic_metrics: Dict[str, Any],
        advanced_metrics: Dict[str, Any],
    ) -> List[str]:
        """Generate optimization recommendations."""

        recommendations = []

        if basic_metrics["total_trades"] < 30:
            recommendations.append(
                "Consider adjusting signal sensitivity to generate more trades for statistical significance"
            )

        if basic_metrics["win_rate"] < 0.4:
            recommendations.append(
                "Low win rate detected - review entry criteria and signal quality"
            )

        if basic_metrics["profit_factor"] < 1.2:
            recommendations.append(
                "Poor profit factor - optimize stop-loss and take-profit levels"
            )

        if advanced_metrics["max_drawdown"] > 0.15:
            recommendations.append(
                "High drawdown risk - implement stricter position sizing or risk management"
            )

        if advanced_metrics["consecutive_losses"] > 5:
            recommendations.append(
                "High consecutive losses - consider adding trend filters or market condition checks"
            )

        if (
            basic_metrics["avg_loss"] != 0
            and abs(basic_metrics["avg_win"] / basic_metrics["avg_loss"]) < 1.5
        ):
            recommendations.append(
                "Poor risk-reward ratio - increase take-profit targets or tighten stop-losses"
            )

        return recommendations

    def _format_validation_metrics(self, metrics: ValidationMetrics) -> Dict[str, Any]:
        """Format validation metrics for reporting."""

        return {
            "core_metrics": {
                "total_trades": metrics.total_trades,
                "win_rate": f"{metrics.win_rate:.2%}",
                "profit_factor": f"{metrics.profit_factor:.2f}",
                "max_drawdown": f"{metrics.max_drawdown:.2%}",
                "total_return": f"{metrics.total_return:.2f}",
            },
            "risk_metrics": {
                "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                "calmar_ratio": f"{metrics.calmar_ratio:.2f}",
                "avg_trade_duration_hours": f"{metrics.avg_trade_duration:.1f}",
            },
            "regime_performance": metrics.regime_performance,
        }

    def _format_trade_list(self, trades: List[Trade]) -> List[Dict[str, Any]]:
        """Format trade list for reporting."""

        formatted_trades = []
        for trade in trades:
            formatted_trades.append(
                {
                    "pair": trade.pair,
                    "direction": trade.direction,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "entry_time": (
                        trade.entry_time.isoformat() if trade.entry_time else None
                    ),
                    "exit_time": (
                        trade.exit_time.isoformat() if trade.exit_time else None
                    ),
                    "pnl": trade.pnl,
                    "position_size": getattr(trade, "position_size", 0),
                }
            )

        return formatted_trades

    def _rank_strategies(
        self, strategy_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Rank strategies by different criteria."""

        if not strategy_metrics:
            return {"overall": [], "profit": [], "risk": [], "consistency": []}

        # Rank by total PnL
        profit_ranking = sorted(
            strategy_metrics.items(), key=lambda x: x[1]["total_pnl"], reverse=True
        )

        # Rank by profit factor
        consistency_ranking = sorted(
            strategy_metrics.items(), key=lambda x: x[1]["profit_factor"], reverse=True
        )

        # Rank by drawdown (lower is better)
        risk_ranking = sorted(
            strategy_metrics.items(), key=lambda x: x[1]["max_drawdown"]
        )

        # Overall ranking (composite score)
        overall_ranking = sorted(
            strategy_metrics.items(),
            key=lambda x: (
                x[1]["profit_factor"] * 0.4
                + (1 - x[1]["max_drawdown"]) * 0.3
                + x[1]["win_rate"] * 0.3
            ),
            reverse=True,
        )

        return {
            "overall": [name for name, _ in overall_ranking],
            "profit": [name for name, _ in profit_ranking],
            "risk": [name for name, _ in risk_ranking],
            "consistency": [name for name, _ in consistency_ranking],
        }

    def _compare_performance(
        self, strategy_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance across strategies."""

        if not strategy_metrics:
            return {}

        metrics_keys = ["total_pnl", "win_rate", "profit_factor", "max_drawdown"]
        comparison = {}

        for key in metrics_keys:
            values = [metrics[key] for metrics in strategy_metrics.values()]
            comparison[key] = {
                "best": max(values) if key != "max_drawdown" else min(values),
                "worst": min(values) if key != "max_drawdown" else max(values),
                "average": sum(values) / len(values),
                "range": max(values) - min(values),
            }

        return comparison

    def _generate_comparison_recommendations(
        self, strategy_metrics: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for strategy comparison."""

        recommendations = []

        if len(strategy_metrics) < 3:
            recommendations.append(
                "Consider testing additional strategy variations for better comparison"
            )

        # Find best performing strategy
        best_strategy = max(
            strategy_metrics.items(), key=lambda x: x[1]["profit_factor"]
        )
        recommendations.append(
            f"Best performing strategy: {best_strategy[0]} with profit factor {best_strategy[1]['profit_factor']:.2f}"
        )

        # Check for consistent performers
        consistent_strategies = [
            name
            for name, metrics in strategy_metrics.items()
            if metrics["max_drawdown"] < 0.1
        ]
        if consistent_strategies:
            recommendations.append(
                f"Most consistent strategies (low drawdown): {', '.join(consistent_strategies)}"
            )

        return recommendations

    def _export_report(self, report: Dict[str, Any], config: ReportConfig) -> None:
        """Export report to specified format and path."""

        try:
            if config.export_path and config.format.lower() == "json":
                with open(config.export_path, "w") as f:
                    json.dump(report, f, indent=2, default=str)
            elif config.export_path and config.format.lower() == "csv":
                # Export key metrics to CSV
                import pandas as pd

                if "summary" in report:
                    df = pd.DataFrame([report["summary"]])
                    if config.export_path:
                        df.to_csv(config.export_path, index=False)

            logger.info(f"Report exported to {config.export_path}")

        except Exception as e:
            logger.error(f"Failed to export report: {e}")


# Global report generator instance
report_generator = ReportGenerator()
