"""
MarketData Entity - Core business entity representing market data

This entity encapsulates all the essential properties and business logic
related to market data (OHLCV) in the 4ex.ninja system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List


class Granularity(Enum):
    """Enumeration for timeframe granularities"""

    S5 = "S5"  # 5 seconds
    S10 = "S10"  # 10 seconds
    S15 = "S15"  # 15 seconds
    S30 = "S30"  # 30 seconds
    M1 = "M1"  # 1 minute
    M2 = "M2"  # 2 minutes
    M4 = "M4"  # 4 minutes
    M5 = "M5"  # 5 minutes
    M10 = "M10"  # 10 minutes
    M15 = "M15"  # 15 minutes
    M30 = "M30"  # 30 minutes
    H1 = "H1"  # 1 hour
    H2 = "H2"  # 2 hours
    H3 = "H3"  # 3 hours
    H4 = "H4"  # 4 hours
    H6 = "H6"  # 6 hours
    H8 = "H8"  # 8 hours
    H12 = "H12"  # 12 hours
    D = "D"  # 1 day
    W = "W"  # 1 week
    M = "M"  # 1 month


@dataclass
class Candle:
    """
    Individual candle data representing OHLCV information for a specific time period.
    """

    # Required fields
    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    # Optional fields with defaults
    complete: bool = True
    spread: Optional[Decimal] = None

    def __post_init__(self):
        """Post-initialization validation"""
        self.validate()

    def validate(self) -> None:
        """Validate candle data integrity"""
        if self.high < max(self.open, self.close):
            raise ValueError("High price cannot be less than open or close")

        if self.low > min(self.open, self.close):
            raise ValueError("Low price cannot be greater than open or close")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

    def is_bullish(self) -> bool:
        """Check if candle is bullish (close > open)"""
        return self.close > self.open

    def is_bearish(self) -> bool:
        """Check if candle is bearish (close < open)"""
        return self.close < self.open

    def is_doji(self, threshold: float = 0.0001) -> bool:
        """Check if candle is a doji (open ≈ close)"""
        return abs(self.close - self.open) <= Decimal(str(threshold))

    def body_size(self) -> Decimal:
        """Calculate the size of the candle body"""
        return abs(self.close - self.open)

    def upper_shadow(self) -> Decimal:
        """Calculate the upper shadow size"""
        return self.high - max(self.open, self.close)

    def lower_shadow(self) -> Decimal:
        """Calculate the lower shadow size"""
        return min(self.open, self.close) - self.low

    def total_range(self) -> Decimal:
        """Calculate the total range (high - low)"""
        return self.high - self.low

    def typical_price(self) -> Decimal:
        """Calculate typical price (HLC/3)"""
        return (self.high + self.low + self.close) / Decimal("3")

    def weighted_close(self) -> Decimal:
        """Calculate weighted close (OHLC/4)"""
        return (self.open + self.high + self.low + self.close) / Decimal("4")

    def to_dict(self) -> dict:
        """Convert candle to dictionary for storage"""
        return {
            "time": self.time,
            "o": str(self.open),
            "h": str(self.high),
            "l": str(self.low),
            "c": str(self.close),
            "volume": self.volume,
            "complete": self.complete,
            "spread": str(self.spread) if self.spread else None,
        }


@dataclass
class MarketData:
    """
    Core MarketData entity representing market data for a currency pair.

    This entity contains OHLCV data and provides methods for technical analysis
    and data manipulation.
    """

    # Required fields
    instrument: str
    granularity: Granularity
    candles: List[Candle]

    # Optional fields with defaults
    last_updated: datetime = field(default_factory=datetime.utcnow)
    source: str = "OANDA"

    def __post_init__(self):
        """Post-initialization processing"""
        self.sort_candles()

    def sort_candles(self) -> None:
        """Sort candles by time in ascending order"""
        self.candles.sort(key=lambda x: x.time)

    def add_candle(self, candle: Candle) -> None:
        """Add a new candle and maintain sorted order"""
        self.candles.append(candle)
        self.sort_candles()
        self.last_updated = datetime.utcnow()

    def get_latest_candle(self) -> Optional[Candle]:
        """Get the most recent candle"""
        return self.candles[-1] if self.candles else None

    def get_candles_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[Candle]:
        """Get candles within a specific time range"""
        return [
            candle for candle in self.candles if start_time <= candle.time <= end_time
        ]

    def get_recent_candles(self, count: int) -> List[Candle]:
        """Get the most recent N candles"""
        return self.candles[-count:] if count <= len(self.candles) else self.candles

    def get_closes(self, count: Optional[int] = None) -> List[Decimal]:
        """Get closing prices"""
        candles = self.get_recent_candles(count) if count else self.candles
        return [candle.close for candle in candles]

    def get_highs(self, count: Optional[int] = None) -> List[Decimal]:
        """Get high prices"""
        candles = self.get_recent_candles(count) if count else self.candles
        return [candle.high for candle in candles]

    def get_lows(self, count: Optional[int] = None) -> List[Decimal]:
        """Get low prices"""
        candles = self.get_recent_candles(count) if count else self.candles
        return [candle.low for candle in candles]

    def get_volumes(self, count: Optional[int] = None) -> List[int]:
        """Get volumes"""
        candles = self.get_recent_candles(count) if count else self.candles
        return [candle.volume for candle in candles]

    def calculate_sma(self, period: int) -> Optional[Decimal]:
        """Calculate Simple Moving Average for the specified period"""
        if len(self.candles) < period:
            return None

        recent_closes = self.get_closes(period)
        return sum(recent_closes) / Decimal(str(period))

    def calculate_true_range(self, candle_index: int) -> Optional[Decimal]:
        """Calculate True Range for a specific candle"""
        if candle_index <= 0 or candle_index >= len(self.candles):
            return None

        current = self.candles[candle_index]
        previous = self.candles[candle_index - 1]

        tr1 = current.high - current.low
        tr2 = abs(current.high - previous.close)
        tr3 = abs(current.low - previous.close)

        return max(tr1, tr2, tr3)

    def calculate_atr(self, period: int) -> Optional[Decimal]:
        """Calculate Average True Range for the specified period"""
        if len(self.candles) < period + 1:  # Need one extra for previous close
            return None

        true_ranges = []
        for i in range(len(self.candles) - period, len(self.candles)):
            tr = self.calculate_true_range(i)
            if tr is not None:
                true_ranges.append(tr)

        if len(true_ranges) < period:
            return None

        return sum(true_ranges) / Decimal(str(period))

    def has_sufficient_data(self, required_periods: int) -> bool:
        """Check if there's sufficient data for analysis"""
        return len(self.candles) >= required_periods

    def get_price_change(self, periods: int = 1) -> Optional[Decimal]:
        """Calculate price change over specified periods"""
        if len(self.candles) < periods + 1:
            return None

        current_price = self.candles[-1].close
        past_price = self.candles[-(periods + 1)].close

        return current_price - past_price

    def get_price_change_percentage(self, periods: int = 1) -> Optional[float]:
        """Calculate percentage price change over specified periods"""
        if len(self.candles) < periods + 1:
            return None

        current_price = self.candles[-1].close
        past_price = self.candles[-(periods + 1)].close

        if past_price == 0:
            return None

        change = current_price - past_price
        return float((change / past_price) * Decimal("100"))

    def to_dict(self) -> dict:
        """Convert market data to dictionary for storage"""
        return {
            "instrument": self.instrument,
            "granularity": self.granularity.value,
            "candles": [candle.to_dict() for candle in self.candles],
            "last_updated": self.last_updated,
            "source": self.source,
            "candle_count": len(self.candles),
        }
