"""
Strategy Entity - Core business entity representing a trading strategy

This entity encapsulates all the essential properties and business logic
related to trading strategies in the 4ex.ninja system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod


class StrategyType(Enum):
    """Enumeration for strategy types"""

    MOVING_AVERAGE_CROSSOVER = "MOVING_AVERAGE_CROSSOVER"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    RSI = "RSI"
    MACD = "MACD"
    CUSTOM = "CUSTOM"


class StrategyStatus(Enum):
    """Enumeration for strategy status"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TESTING = "TESTING"
    ARCHIVED = "ARCHIVED"


@dataclass
class StrategyParameters:
    """Container for strategy parameters"""

    # Moving Average parameters
    fast_ma_period: Optional[int] = None
    slow_ma_period: Optional[int] = None

    # Risk management parameters
    atr_period: Optional[int] = None
    sl_atr_multiplier: Optional[float] = None
    tp_atr_multiplier: Optional[float] = None
    min_atr_value: Optional[float] = None
    min_rr_ratio: Optional[float] = None

    # Position sizing
    position_size_method: str = "FIXED"
    position_size_value: Optional[Decimal] = None
    max_risk_per_trade: Optional[float] = None

    # Timing parameters
    min_candles_required: int = 200
    sleep_seconds: int = 60

    # Additional custom parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert parameters to dictionary"""
        return {
            "fast_ma_period": self.fast_ma_period,
            "slow_ma_period": self.slow_ma_period,
            "atr_period": self.atr_period,
            "sl_atr_multiplier": self.sl_atr_multiplier,
            "tp_atr_multiplier": self.tp_atr_multiplier,
            "min_atr_value": self.min_atr_value,
            "min_rr_ratio": self.min_rr_ratio,
            "position_size_method": self.position_size_method,
            "position_size_value": (
                str(self.position_size_value) if self.position_size_value else None
            ),
            "max_risk_per_trade": self.max_risk_per_trade,
            "min_candles_required": self.min_candles_required,
            "sleep_seconds": self.sleep_seconds,
            "custom_params": self.custom_params,
        }


@dataclass
class StrategyPerformance:
    """Container for strategy performance metrics"""

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    # Performance metrics
    win_rate: float = 0.0
    total_pnl: Decimal = Decimal("0")
    average_win: Decimal = Decimal("0")
    average_loss: Decimal = Decimal("0")
    profit_factor: float = 0.0

    # Risk metrics
    max_drawdown: Decimal = Decimal("0")
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None

    # Recent performance
    last_30_days_pnl: Decimal = Decimal("0")
    last_7_days_trades: int = 0

    # Timestamps
    performance_start_date: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        self.win_rate = (self.winning_trades / self.total_trades) * 100
        return self.win_rate

    def calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        gross_profit = (
            self.winning_trades * self.average_win
            if self.winning_trades > 0
            else Decimal("0")
        )
        gross_loss = (
            abs(self.losing_trades * self.average_loss)
            if self.losing_trades > 0
            else Decimal("0")
        )

        if gross_loss == 0:
            self.profit_factor = float("inf") if gross_profit > 0 else 0.0
        else:
            self.profit_factor = float(gross_profit / gross_loss)

        return self.profit_factor

    def update_metrics(self) -> None:
        """Update calculated metrics"""
        self.calculate_win_rate()
        self.calculate_profit_factor()
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert performance to dictionary"""
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "total_pnl": str(self.total_pnl),
            "average_win": str(self.average_win),
            "average_loss": str(self.average_loss),
            "profit_factor": self.profit_factor,
            "max_drawdown": str(self.max_drawdown),
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "last_30_days_pnl": str(self.last_30_days_pnl),
            "last_7_days_trades": self.last_7_days_trades,
            "performance_start_date": self.performance_start_date,
            "last_updated": self.last_updated,
        }


@dataclass
class Strategy:
    """
    Core Strategy entity representing a trading strategy.

    This entity contains all the essential information needed to represent
    a trading strategy in the system, including parameters, performance
    metrics, and configuration.
    """

    # Required fields
    strategy_id: str
    name: str
    strategy_type: StrategyType
    pair: str
    timeframe: str

    # Configuration
    parameters: StrategyParameters

    # Optional fields with defaults
    description: Optional[str] = None
    status: StrategyStatus = StrategyStatus.INACTIVE
    version: str = "1.0.0"

    # Performance tracking
    performance: StrategyPerformance = field(default_factory=StrategyPerformance)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_signal_time: Optional[datetime] = None

    # Metadata
    creator: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def __post_init__(self):
        """Post-initialization processing"""
        self.validate_parameters()

    def validate_parameters(self) -> None:
        """Validate strategy parameters based on strategy type"""
        if self.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
            if not self.parameters.fast_ma_period or not self.parameters.slow_ma_period:
                raise ValueError(
                    "Moving Average strategy requires fast_ma_period and slow_ma_period"
                )

            if self.parameters.fast_ma_period >= self.parameters.slow_ma_period:
                raise ValueError("Fast MA period must be less than slow MA period")

    def activate(self) -> None:
        """Activate the strategy"""
        self.status = StrategyStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the strategy"""
        self.status = StrategyStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def set_testing_mode(self) -> None:
        """Set strategy to testing mode"""
        self.status = StrategyStatus.TESTING
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the strategy"""
        self.status = StrategyStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if strategy is currently active"""
        return self.status == StrategyStatus.ACTIVE

    def is_testing(self) -> bool:
        """Check if strategy is in testing mode"""
        return self.status == StrategyStatus.TESTING

    def update_last_signal_time(self) -> None:
        """Update the last signal generation time"""
        self.last_signal_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the strategy"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the strategy"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def get_required_data_periods(self) -> int:
        """Calculate the minimum number of data periods required for this strategy"""
        required_periods = self.parameters.min_candles_required

        if self.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
            ma_required = max(
                self.parameters.slow_ma_period or 0, self.parameters.atr_period or 0
            )
            required_periods = max(required_periods, ma_required)

        return required_periods

    def can_generate_signals(self, available_data_points: int) -> bool:
        """Check if strategy has sufficient data to generate signals"""
        return available_data_points >= self.get_required_data_periods()

    def update_performance(self, trade_result: dict) -> None:
        """Update strategy performance with new trade result"""
        self.performance.total_trades += 1

        pnl = Decimal(str(trade_result.get("pnl", 0)))
        self.performance.total_pnl += pnl

        if pnl > 0:
            self.performance.winning_trades += 1
            # Update average win
            if self.performance.winning_trades == 1:
                self.performance.average_win = pnl
            else:
                total_wins = (
                    self.performance.average_win * (self.performance.winning_trades - 1)
                    + pnl
                )
                self.performance.average_win = total_wins / Decimal(
                    str(self.performance.winning_trades)
                )
        else:
            self.performance.losing_trades += 1
            # Update average loss
            if self.performance.losing_trades == 1:
                self.performance.average_loss = pnl
            else:
                total_losses = (
                    self.performance.average_loss * (self.performance.losing_trades - 1)
                    + pnl
                )
                self.performance.average_loss = total_losses / Decimal(
                    str(self.performance.losing_trades)
                )

        self.performance.update_metrics()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert strategy to dictionary for storage"""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "strategy_type": self.strategy_type.value,
            "pair": self.pair,
            "timeframe": self.timeframe,
            "parameters": self.parameters.to_dict(),
            "description": self.description,
            "status": self.status.value,
            "version": self.version,
            "performance": self.performance.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_signal_time": self.last_signal_time,
            "creator": self.creator,
            "tags": self.tags,
            "notes": self.notes,
        }
