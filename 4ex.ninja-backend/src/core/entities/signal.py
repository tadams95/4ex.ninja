"""
Signal Entity - Core business entity representing a trading signal

This entity encapsulates all the essential properties and business logic
related to trading signals in the 4ex.ninja system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class SignalType(Enum):
    """Enumeration for signal types"""

    BUY = "BUY"
    SELL = "SELL"


class SignalStatus(Enum):
    """Enumeration for signal status"""

    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class CrossoverType(Enum):
    """Enumeration for crossover types"""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


@dataclass
class Signal:
    """
    Core Signal entity representing a trading signal.

    This entity contains all the essential information needed to represent
    a trading signal in the system, including entry/exit points, risk
    management parameters, and metadata.
    """

    # Identification (required fields first)
    signal_id: str
    pair: str
    timeframe: str

    # Signal classification (required)
    signal_type: SignalType
    crossover_type: CrossoverType

    # Price information (required)
    entry_price: Decimal
    current_price: Decimal

    # Technical analysis data (required)
    fast_ma: int
    slow_ma: int

    # Timestamps (required)
    timestamp: datetime

    # Optional fields with defaults
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    atr_value: Optional[Decimal] = None
    atr_multiplier_sl: Optional[float] = None
    atr_multiplier_tp: Optional[float] = None

    # Risk management (optional)
    risk_reward_ratio: Optional[float] = None
    position_size: Optional[Decimal] = None

    # Timestamps with defaults
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Status and metadata with defaults
    status: SignalStatus = SignalStatus.ACTIVE
    confidence_score: Optional[float] = None
    strategy_name: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Post-initialization validation and calculations"""
        if self.risk_reward_ratio is None and self.stop_loss and self.take_profit:
            self.calculate_risk_reward_ratio()

    def calculate_risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk-reward ratio based on stop loss and take profit"""
        if not self.stop_loss or not self.take_profit:
            return None

        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)

        if risk > 0:
            self.risk_reward_ratio = float(reward / risk)
            return self.risk_reward_ratio

        return None

    def is_profitable(self) -> bool:
        """Check if signal is currently profitable"""
        if self.signal_type == SignalType.BUY:
            return self.current_price > self.entry_price
        else:
            return self.current_price < self.entry_price

    def get_pnl(self) -> Decimal:
        """Calculate current profit/loss"""
        if self.signal_type == SignalType.BUY:
            return self.current_price - self.entry_price
        else:
            return self.entry_price - self.current_price

    def update_current_price(self, new_price: Decimal) -> None:
        """Update current price and timestamp"""
        self.current_price = new_price
        self.updated_at = datetime.utcnow()

    def should_stop_loss(self) -> bool:
        """Check if stop loss should be triggered"""
        if not self.stop_loss:
            return False

        if self.signal_type == SignalType.BUY:
            return self.current_price <= self.stop_loss
        else:
            return self.current_price >= self.stop_loss

    def should_take_profit(self) -> bool:
        """Check if take profit should be triggered"""
        if not self.take_profit:
            return False

        if self.signal_type == SignalType.BUY:
            return self.current_price >= self.take_profit
        else:
            return self.current_price <= self.take_profit

    def close_signal(self, reason: str = "Manual") -> None:
        """Close the signal with reason"""
        self.status = SignalStatus.FILLED
        self.notes = f"{self.notes or ''} Closed: {reason}".strip()
        self.updated_at = datetime.utcnow()

    def cancel_signal(self, reason: str = "Cancelled") -> None:
        """Cancel the signal with reason"""
        self.status = SignalStatus.CANCELLED
        self.notes = f"{self.notes or ''} Cancelled: {reason}".strip()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert signal to dictionary for storage"""
        return {
            "signal_id": self.signal_id,
            "pair": self.pair,
            "timeframe": self.timeframe,
            "signal_type": self.signal_type.value,
            "crossover_type": self.crossover_type.value,
            "entry_price": str(self.entry_price),
            "current_price": str(self.current_price),
            "stop_loss": str(self.stop_loss) if self.stop_loss else None,
            "take_profit": str(self.take_profit) if self.take_profit else None,
            "fast_ma": self.fast_ma,
            "slow_ma": self.slow_ma,
            "atr_value": str(self.atr_value) if self.atr_value else None,
            "atr_multiplier_sl": self.atr_multiplier_sl,
            "atr_multiplier_tp": self.atr_multiplier_tp,
            "risk_reward_ratio": self.risk_reward_ratio,
            "position_size": str(self.position_size) if self.position_size else None,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "confidence_score": self.confidence_score,
            "strategy_name": self.strategy_name,
            "notes": self.notes,
        }
