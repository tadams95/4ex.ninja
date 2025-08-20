"""
Signal Models
Data models for trading signals and strategy results.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SignalType(str, Enum):
    """Trading signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStatus(str, Enum):
    """Signal processing status."""

    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    SENT = "SENT"


class TradingSignal(BaseModel):
    """Trading signal data model."""

    id: Optional[str] = None
    pair: str = Field(..., description="Currency pair (e.g., EUR_USD)")
    timeframe: str = Field(..., description="Timeframe (e.g., D)")
    signal_type: SignalType = Field(..., description="BUY, SELL, or HOLD")
    price: float = Field(..., description="Current price when signal generated")
    fast_ma: float = Field(..., description="Fast MA value")
    slow_ma: float = Field(..., description="Slow MA value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: SignalStatus = Field(default=SignalStatus.PENDING)
    strategy_type: str = Field(default="conservative_moderate_daily")
    confidence: Optional[float] = Field(None, description="Signal confidence (0-1)")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class StrategyConfig(BaseModel):
    """Strategy configuration model."""

    pair: str
    timeframe: str
    fast_ma: int = 50
    slow_ma: int = 200
    source: str = "close"
    strategy_type: str = "conservative_moderate_daily"
    expected_return: str
    validated: bool = True


class PerformanceMetrics(BaseModel):
    """Strategy performance metrics."""

    pair: str
    timeframe: str
    total_return: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    profit_factor: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PriceData(BaseModel):
    """Price data model for MA calculations."""

    pair: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MACalculation(BaseModel):
    """Moving average calculation result."""

    pair: str
    timeframe: str
    timestamp: datetime
    fast_ma_period: int = 50
    slow_ma_period: int = 200
    fast_ma_value: float
    slow_ma_value: float
    current_price: float
    signal_generated: bool = False
    signal_type: Optional[SignalType] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NotificationPayload(BaseModel):
    """Discord notification payload."""

    content: str
    embeds: Optional[List[Dict[str, Any]]] = None


class SignalResponse(BaseModel):
    """API response for signal operations."""

    success: bool
    message: str
    signal: Optional[TradingSignal] = None
    signals: Optional[List[TradingSignal]] = None


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float
    strategy_count: int
    last_signal_time: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class StrategyConfigResponse(BaseModel):
    """Strategy configuration response."""

    success: bool
    message: str
    config: Optional[StrategyConfig] = None
    configs: Optional[Dict[str, StrategyConfig]] = None


class PerformanceResponse(BaseModel):
    """Performance metrics response."""

    success: bool
    message: str
    metrics: Optional[PerformanceMetrics] = None
    all_metrics: Optional[Dict[str, PerformanceMetrics]] = None


# Request models for API endpoints
class GenerateSignalRequest(BaseModel):
    """Request to generate signal for specific pair."""

    pair: str = Field(..., description="Currency pair (e.g., EUR_USD_D)")
    force_recalculate: bool = Field(default=False)


class UpdateConfigRequest(BaseModel):
    """Request to update strategy configuration."""

    pair: str
    timeframe: str
    fast_ma: Optional[int] = None
    slow_ma: Optional[int] = None
    source: Optional[str] = None
