"""
Trade Tracker for Universal Backtesting Framework.

This module tracks and analyzes trade execution and performance
for ANY strategy implementing the BaseStrategy interface.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import csv
import json
from pathlib import Path

from .strategy_interface import BaseStrategy, TradeSignal
from .universal_backtesting_engine import Trade
from .regime_detector import MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class TradeAnalytics:
    """Analytics for a single trade."""

    trade_id: str
    strategy_name: str
    pair: str
    entry_time: datetime
    exit_time: Optional[datetime]
    direction: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    pnl: Optional[float]
    pnl_pips: Optional[float]
    duration_hours: Optional[float]
    regime: Optional[MarketRegime]
    exit_reason: Optional[str]
    risk_reward_ratio: Optional[float]
    max_adverse_excursion: Optional[float]  # MAE
    max_favorable_excursion: Optional[float]  # MFE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy."""

    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    regime_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    monthly_returns: Dict[str, float] = field(default_factory=dict)


class TradeTracker:
    """
    Universal trade tracker that works with ANY strategy.

    This tracker monitors trade execution, calculates performance metrics,
    and provides detailed analytics for strategy optimization.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize trade tracker.

        Args:
            output_dir: Directory for saving trade logs and reports
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./backtest_results")
        self.output_dir.mkdir(exist_ok=True)

        self.trades: List[TradeAnalytics] = []
        self.strategy_performance: Dict[str, StrategyPerformance] = {}

        logger.info(f"TradeTracker initialized with output dir: {self.output_dir}")

    def track_trade(self, trade: Trade) -> TradeAnalytics:
        """
        Track a completed trade and generate analytics.

        Args:
            trade: Completed trade object

        Returns:
            TradeAnalytics object with calculated metrics
        """
        try:
            # Calculate duration
            duration_hours = None
            if trade.exit_time and trade.entry_time:
                duration = trade.exit_time - trade.entry_time
                duration_hours = duration.total_seconds() / 3600

            # Calculate risk-reward ratio
            risk_reward_ratio = None
            if trade.exit_price and trade.pnl:
                if trade.direction == "BUY":
                    risk = trade.entry_price - trade.stop_loss
                    reward = trade.exit_price - trade.entry_price
                else:
                    risk = trade.stop_loss - trade.entry_price
                    reward = trade.entry_price - trade.exit_price

                if risk > 0:
                    risk_reward_ratio = abs(reward / risk)

            # Create analytics object
            analytics = TradeAnalytics(
                trade_id=f"{trade.strategy_name}_{trade.pair}_{trade.entry_time.isoformat()}",
                strategy_name=trade.strategy_name,
                pair=trade.pair,
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                direction=trade.direction,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                position_size=trade.position_size,
                pnl=trade.pnl,
                pnl_pips=trade.pnl_pips,
                duration_hours=duration_hours,
                regime=trade.regime,
                exit_reason=trade.exit_reason,
                risk_reward_ratio=risk_reward_ratio,
                max_adverse_excursion=None,  # TODO: Calculate MAE
                max_favorable_excursion=None,  # TODO: Calculate MFE
                metadata=trade.metadata,
            )

            self.trades.append(analytics)
            logger.debug(f"Tracked trade: {analytics.trade_id}")

            return analytics

        except Exception as e:
            logger.error(f"Error tracking trade: {e}")
            raise

    def calculate_strategy_performance(self, strategy_name: str) -> StrategyPerformance:
        """
        Calculate comprehensive performance metrics for a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            StrategyPerformance object with all metrics
        """
        try:
            strategy_trades = [
                t for t in self.trades if t.strategy_name == strategy_name
            ]

            if not strategy_trades:
                return StrategyPerformance(
                    strategy_name=strategy_name,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_pnl=0.0,
                    total_return=0.0,
                    avg_win=0.0,
                    avg_loss=0.0,
                    profit_factor=0.0,
                    max_drawdown=0.0,
                )

            # Calculate basic metrics
            completed_trades = [t for t in strategy_trades if t.pnl is not None]
            total_trades = len(completed_trades)

            if total_trades == 0:
                total_pnl = 0.0
                winning_trades = []
                losing_trades = []
            else:
                # Extract valid PnL values for safe sum operations
                valid_pnl_values = [
                    t.pnl for t in completed_trades if t.pnl is not None
                ]
                total_pnl = sum(valid_pnl_values)
                winning_trades = [
                    t for t in completed_trades if t.pnl is not None and t.pnl > 0
                ]
                losing_trades = [
                    t for t in completed_trades if t.pnl is not None and t.pnl < 0
                ]

            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

            # Calculate averages safely
            winning_pnl = [t.pnl for t in winning_trades if t.pnl is not None]
            losing_pnl = [t.pnl for t in losing_trades if t.pnl is not None]

            avg_win = sum(winning_pnl) / len(winning_pnl) if winning_pnl else 0
            avg_loss = sum(losing_pnl) / len(losing_pnl) if losing_pnl else 0

            # Calculate profit factor
            total_wins = sum(winning_pnl) if winning_pnl else 0
            total_losses = abs(sum(losing_pnl)) if losing_pnl else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0

            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown(completed_trades)

            # Calculate regime performance
            regime_performance = self._calculate_regime_performance(completed_trades)

            # Calculate monthly returns
            monthly_returns = self._calculate_monthly_returns(completed_trades)

            performance = StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=total_trades,
                winning_trades=len(winning_trades),
                losing_trades=len(losing_trades),
                win_rate=win_rate,
                total_pnl=total_pnl,
                total_return=total_pnl / 10000.0,  # Simplified return calculation
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                max_drawdown=max_drawdown,
                regime_performance=regime_performance,
                monthly_returns=monthly_returns,
            )

            self.strategy_performance[strategy_name] = performance
            logger.info(
                f"Calculated performance for {strategy_name}: {total_trades} trades, {win_rate:.2%} win rate"
            )

            return performance

        except Exception as e:
            logger.error(f"Error calculating strategy performance: {e}")
            raise

    def _calculate_max_drawdown(self, trades: List[TradeAnalytics]) -> float:
        """
        Calculate maximum drawdown from trade sequence.

        Args:
            trades: List of trade analytics

        Returns:
            Maximum drawdown as percentage
        """
        if not trades:
            return 0.0

        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t.entry_time)

        running_balance = 0.0
        peak_balance = 0.0
        max_drawdown = 0.0

        for trade in sorted_trades:
            if trade.pnl is not None:
                running_balance += trade.pnl

                if running_balance > peak_balance:
                    peak_balance = running_balance

                if peak_balance > 0:
                    drawdown = (peak_balance - running_balance) / peak_balance
                    max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_regime_performance(
        self, trades: List[TradeAnalytics]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate performance by market regime.

        Args:
            trades: List of trade analytics

        Returns:
            Performance metrics by regime
        """
        regime_performance = {}

        # Group trades by regime
        regime_trades = {}
        for trade in trades:
            if trade.regime:
                regime_key = trade.regime.value
                if regime_key not in regime_trades:
                    regime_trades[regime_key] = []
                regime_trades[regime_key].append(trade)

        # Calculate performance for each regime
        for regime, regime_trade_list in regime_trades.items():
            valid_trades = [t for t in regime_trade_list if t.pnl is not None]

            if valid_trades:
                total_pnl = sum(t.pnl for t in valid_trades)
                winning = [t for t in valid_trades if t.pnl > 0]

                regime_performance[regime] = {
                    "total_trades": len(valid_trades),
                    "winning_trades": len(winning),
                    "win_rate": len(winning) / len(valid_trades),
                    "total_pnl": total_pnl,
                    "avg_pnl": total_pnl / len(valid_trades),
                }

        return regime_performance

    def _calculate_monthly_returns(
        self, trades: List[TradeAnalytics]
    ) -> Dict[str, float]:
        """
        Calculate monthly returns from trades.

        Args:
            trades: List of trade analytics

        Returns:
            Monthly returns dictionary
        """
        monthly_returns = {}

        for trade in trades:
            if trade.exit_time and trade.pnl is not None:
                month_key = trade.exit_time.strftime("%Y-%m")
                if month_key not in monthly_returns:
                    monthly_returns[month_key] = 0.0
                monthly_returns[month_key] += trade.pnl

        return monthly_returns

    def export_trade_log(self, strategy_name: Optional[str] = None) -> str:
        """
        Export trade log to CSV file.

        Args:
            strategy_name: Strategy to export (None for all)

        Returns:
            Path to exported file
        """
        try:
            # Filter trades if strategy specified
            trades_to_export = self.trades
            if strategy_name:
                trades_to_export = [
                    t for t in self.trades if t.strategy_name == strategy_name
                ]

            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if strategy_name:
                filename = f"trades_{strategy_name}_{timestamp}.csv"
            else:
                filename = f"trades_all_{timestamp}.csv"

            filepath = self.output_dir / filename

            # Write CSV
            with open(filepath, "w", newline="") as csvfile:
                fieldnames = [
                    "trade_id",
                    "strategy_name",
                    "pair",
                    "entry_time",
                    "exit_time",
                    "direction",
                    "entry_price",
                    "exit_price",
                    "position_size",
                    "pnl",
                    "pnl_pips",
                    "duration_hours",
                    "regime",
                    "exit_reason",
                    "risk_reward_ratio",
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for trade in trades_to_export:
                    row = {
                        "trade_id": trade.trade_id,
                        "strategy_name": trade.strategy_name,
                        "pair": trade.pair,
                        "entry_time": (
                            trade.entry_time.isoformat() if trade.entry_time else ""
                        ),
                        "exit_time": (
                            trade.exit_time.isoformat() if trade.exit_time else ""
                        ),
                        "direction": trade.direction,
                        "entry_price": trade.entry_price,
                        "exit_price": trade.exit_price,
                        "position_size": trade.position_size,
                        "pnl": trade.pnl,
                        "pnl_pips": trade.pnl_pips,
                        "duration_hours": trade.duration_hours,
                        "regime": trade.regime.value if trade.regime else "",
                        "exit_reason": trade.exit_reason,
                        "risk_reward_ratio": trade.risk_reward_ratio,
                    }
                    writer.writerow(row)

            logger.info(f"Exported {len(trades_to_export)} trades to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting trade log: {e}")
            raise

    def export_performance_report(self, strategy_name: str) -> str:
        """
        Export detailed performance report to JSON.

        Args:
            strategy_name: Strategy name

        Returns:
            Path to exported file
        """
        try:
            performance = self.calculate_strategy_performance(strategy_name)

            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_{strategy_name}_{timestamp}.json"
            filepath = self.output_dir / filename

            # Prepare data for JSON serialization
            report_data = {
                "strategy_name": performance.strategy_name,
                "total_trades": performance.total_trades,
                "winning_trades": performance.winning_trades,
                "losing_trades": performance.losing_trades,
                "win_rate": performance.win_rate,
                "total_pnl": performance.total_pnl,
                "total_return": performance.total_return,
                "avg_win": performance.avg_win,
                "avg_loss": performance.avg_loss,
                "profit_factor": performance.profit_factor,
                "max_drawdown": performance.max_drawdown,
                "sharpe_ratio": performance.sharpe_ratio,
                "regime_performance": performance.regime_performance,
                "monthly_returns": performance.monthly_returns,
                "generated_at": datetime.now().isoformat(),
            }

            # Write JSON
            with open(filepath, "w") as jsonfile:
                json.dump(report_data, jsonfile, indent=2)

            logger.info(f"Exported performance report to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting performance report: {e}")
            raise

    def get_trade_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked trades.

        Returns:
            Summary dictionary
        """
        strategies = set(t.strategy_name for t in self.trades)

        return {
            "total_trades": len(self.trades),
            "strategies": list(strategies),
            "trades_by_strategy": {
                strategy: len([t for t in self.trades if t.strategy_name == strategy])
                for strategy in strategies
            },
            "latest_trade": self.trades[-1].trade_id if self.trades else None,
            "output_directory": str(self.output_dir),
        }
