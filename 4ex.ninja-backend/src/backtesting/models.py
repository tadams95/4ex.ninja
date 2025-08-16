"""
Core data models for the Universal Backtesting Framework.

This module contains shared data classes and types used across
the backtesting framework components.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from .regime_detector import MarketRegime


@dataclass
class Trade:
    """Executed trade record."""

    entry_time: datetime
    exit_time: Optional[datetime]
    pair: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    stop_loss: float
    take_profit: float
    pnl: Optional[float] = None
    pnl_pips: Optional[float] = None
    exit_reason: Optional[str] = None  # "TP", "SL", "TIME", "MANUAL"
    strategy_name: str = ""
    regime: Optional[MarketRegime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Results from a completed backtest."""

    trades: list
    strategy_name: str
    pair: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    performance_metrics: Dict[str, Any]
    regime_analysis: Dict[str, Any]
    data_quality: Any  # DataValidationReport
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.trades:
            self.total_trades = len(self.trades)
            self.winning_trades = len([t for t in self.trades if t.pnl and t.pnl > 0])
            self.losing_trades = len([t for t in self.trades if t.pnl and t.pnl < 0])
            self.win_rate = (
                self.winning_trades / self.total_trades
                if self.total_trades > 0
                else 0.0
            )
