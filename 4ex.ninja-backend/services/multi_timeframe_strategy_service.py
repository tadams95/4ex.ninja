"""
Multi-Timeframe Strategy Service
Implements Phase 1 improvements: Multi-timeframe hierarchy with weekly/daily/4H analysis.
Replaces single-timeframe MA 50/200 approach with sophisticated trend/swing/position trading.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum

from models.signal_models import (
    TradingSignal,
    SignalType,
    PriceData,
    PerformanceMetrics,
    StrategyConfig,
)
from config.settings import OPTIMAL_STRATEGY_CONFIG


class TimeframeAnalysis(NamedTuple):
    """Analysis result for a specific timeframe"""

    timeframe: str
    trend_direction: str  # 'up', 'down', 'sideways'
    trend_strength: str  # 'strong', 'moderate', 'weak'
    bias: str  # 'bullish', 'bearish', 'neutral'
    tradeable: bool
    confidence: float
    ema_20: float
    ema_50: float
    rsi: float
    adx: float


class MultiTimeframeAnalysis(NamedTuple):
    """Combined analysis across all timeframes"""

    weekly: TimeframeAnalysis
    daily: TimeframeAnalysis
    fourhour: TimeframeAnalysis
    confluence_score: float
    primary_direction: str
    trade_recommendation: str


class TradingStyle(Enum):
    """Different trading styles based on timeframe"""

    POSITION = "position"  # Weekly-based, 2-8 weeks
    SWING = "swing"  # Daily-based, 3-10 days
    PRECISION = "precision"  # 4H-based, 12h-3 days


class MultiTimeframeStrategyService:
    """
    Enhanced Multi-Timeframe Strategy Service
    Implements weekly/daily/4H hierarchy for superior forex trading.
    """

    def __init__(self):
        # Timeframe configurations
        self.timeframes = {
            "weekly": {
                "period": "1W",
                "ema_fast": 20,
                "ema_slow": 50,
                "rsi_period": 14,
                "adx_period": 14,
                "atr_period": 14,
            },
            "daily": {
                "period": "1D",
                "ema_fast": 21,
                "rsi_period": 14,
                "volume_ma": 10,
                "adx_period": 14,
            },
            "fourhour": {
                "period": "4H",
                "swing_lookback": 5,
                "rsi_period": 14,
                "pattern_detection": True,
            },
        }

        # Trading rules
        self.confluence_threshold = 0.6  # Minimum 2/3 timeframes must align
        self.min_trend_strength = 25  # ADX threshold for strong trends
        self.risk_rewards = {
            TradingStyle.POSITION: {
                "min_rr": 3.0,
                "max_risk": 0.015,
            },  # 1:3 R:R, 1.5% risk
            TradingStyle.SWING: {
                "min_rr": 3.0,
                "max_risk": 0.010,
            },  # 1:3 R:R, 1.0% risk
            TradingStyle.PRECISION: {
                "min_rr": 2.0,
                "max_risk": 0.008,
            },  # 1:2 R:R, 0.8% risk
        }

    async def analyze_weekly_trend(
        self, weekly_data: List[PriceData]
    ) -> TimeframeAnalysis:
        """
        Analyze weekly timeframe for primary trend direction.

        Weekly Timeframe (Position Trading):
        - Primary Trend: 20/50 EMA crossover for major trend direction
        - Momentum Filter: Weekly RSI > 50 for uptrend, < 50 for downtrend
        - Trend Strength: ADX > 25 confirms strong trending conditions
        """
        if len(weekly_data) < 50:
            raise ValueError(
                f"Insufficient weekly data: need 50+ periods, got {len(weekly_data)}"
            )

        # Calculate indicators
        closes = np.array([p.close for p in weekly_data])
        highs = np.array([p.high for p in weekly_data])
        lows = np.array([p.low for p in weekly_data])

        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50)
        rsi = self._calculate_rsi(closes, 14)
        adx = self._calculate_adx(highs, lows, closes, 14)

        # Determine trend direction
        current_ema_20 = ema_20[-1]
        current_ema_50 = ema_50[-1]
        current_rsi = rsi[-1]
        current_adx = adx[-1]

        # Trend direction logic
        if current_ema_20 > current_ema_50:
            trend_direction = "up"
            bias = "bullish" if current_rsi > 50 else "neutral"
        elif current_ema_20 < current_ema_50:
            trend_direction = "down"
            bias = "bearish" if current_rsi < 50 else "neutral"
        else:
            trend_direction = "sideways"
            bias = "neutral"

        # Trend strength
        if current_adx > 25:
            trend_strength = "strong"
        elif current_adx > 20:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"

        # Tradeable conditions
        tradeable = (
            trend_strength in ["strong", "moderate"]
            and trend_direction != "sideways"
            and bias != "neutral"
        )

        # Confidence calculation
        ema_separation = abs(current_ema_20 - current_ema_50) / current_ema_50
        rsi_strength = abs(current_rsi - 50) / 50
        adx_strength = min(current_adx / 40, 1.0)  # Normalize ADX

        confidence = ema_separation * 0.4 + rsi_strength * 0.3 + adx_strength * 0.3
        confidence = min(max(confidence, 0.0), 1.0)

        return TimeframeAnalysis(
            timeframe="weekly",
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            bias=bias,
            tradeable=tradeable,
            confidence=confidence,
            ema_20=current_ema_20,
            ema_50=current_ema_50,
            rsi=current_rsi,
            adx=current_adx,
        )

    async def analyze_daily_swing(
        self, daily_data: List[PriceData], weekly_analysis: TimeframeAnalysis
    ) -> TimeframeAnalysis:
        """
        Analyze daily timeframe for swing trading opportunities.

        Daily Timeframe (Swing Trading):
        - Entry Setup: Pullbacks to 21 EMA in trending markets
        - Momentum Confirmation: Daily RSI divergence analysis
        - Volume Confirmation: Above-average volume on breakouts
        """
        if len(daily_data) < 30:
            raise ValueError(
                f"Insufficient daily data: need 30+ periods, got {len(daily_data)}"
            )

        # Calculate indicators
        closes = np.array([p.close for p in daily_data])
        highs = np.array([p.high for p in daily_data])
        lows = np.array([p.low for p in daily_data])
        volumes = np.array(
            [getattr(p, "volume", 1000) for p in daily_data]
        )  # Default volume if not available

        ema_21 = self._calculate_ema(closes, 21)
        rsi = self._calculate_rsi(closes, 14)
        volume_ma = self._calculate_sma(volumes, 10)
        adx = self._calculate_adx(highs, lows, closes, 14)

        current_close = closes[-1]
        current_ema_21 = ema_21[-1]
        current_rsi = rsi[-1]
        current_volume = volumes[-1]
        current_volume_ma = volume_ma[-1]
        current_adx = adx[-1]

        # Check for pullback setup in weekly trend direction
        pullback_setup = False
        if weekly_analysis.trend_direction == "up":
            # Looking for pullback to EMA21 in uptrend
            pullback_setup = (
                current_close <= current_ema_21 * 1.002  # Close near EMA21
                and current_rsi < 70  # Not overbought
                and current_volume > current_volume_ma
            )  # Volume confirmation
            trend_direction = "up"
            bias = "bullish"
        elif weekly_analysis.trend_direction == "down":
            # Looking for pullback to EMA21 in downtrend
            pullback_setup = (
                current_close >= current_ema_21 * 0.998  # Close near EMA21
                and current_rsi > 30  # Not oversold
                and current_volume > current_volume_ma
            )  # Volume confirmation
            trend_direction = "down"
            bias = "bearish"
        else:
            trend_direction = "sideways"
            bias = "neutral"

        # Trend strength
        if current_adx > 25:
            trend_strength = "strong"
        elif current_adx > 20:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"

        # Tradeable conditions (must align with weekly)
        tradeable = (
            weekly_analysis.tradeable
            and pullback_setup
            and trend_direction == weekly_analysis.trend_direction
            and trend_strength in ["strong", "moderate"]
        )

        # Confidence calculation
        weekly_alignment = (
            1.0 if trend_direction == weekly_analysis.trend_direction else 0.3
        )
        pullback_quality = 1.0 if pullback_setup else 0.5
        volume_confirmation = min(current_volume / current_volume_ma, 2.0) / 2.0

        confidence = (
            weekly_alignment * 0.5 + pullback_quality * 0.3 + volume_confirmation * 0.2
        )
        confidence = min(max(confidence, 0.0), 1.0)

        return TimeframeAnalysis(
            timeframe="daily",
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            bias=bias,
            tradeable=tradeable,
            confidence=confidence,
            ema_20=current_ema_21,  # Using EMA21 for daily
            ema_50=0.0,  # Not used for daily
            rsi=current_rsi,
            adx=current_adx,
        )

    async def analyze_fourhour_execution(
        self,
        fourhour_data: List[PriceData],
        weekly_analysis: TimeframeAnalysis,
        daily_analysis: TimeframeAnalysis,
    ) -> TimeframeAnalysis:
        """
        Analyze 4H timeframe for precise execution timing.

        4-Hour Timeframe (Precision Execution):
        - Entry Trigger: Break of minor resistance/support in trend direction
        - Risk Management: Stop loss below/above recent swing high/low
        - Pattern Recognition: Clean candlestick patterns (engulfing, hammer, etc.)
        """
        if len(fourhour_data) < 20:
            raise ValueError(
                f"Insufficient 4H data: need 20+ periods, got {len(fourhour_data)}"
            )

        # Calculate indicators
        closes = np.array([p.close for p in fourhour_data])
        highs = np.array([p.high for p in fourhour_data])
        lows = np.array([p.low for p in fourhour_data])

        rsi = self._calculate_rsi(closes, 14)

        current_close = closes[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        current_rsi = rsi[-1]

        # Swing levels analysis
        lookback = 5
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        swing_high = np.max(recent_highs[:-1])  # Exclude current bar
        swing_low = np.min(recent_lows[:-1])  # Exclude current bar

        # Break of structure detection
        breakout_setup = False
        trend_direction = "sideways"
        bias = "neutral"

        if weekly_analysis.tradeable and daily_analysis.tradeable:
            if weekly_analysis.trend_direction == "up":
                # Looking for break above recent swing high
                breakout_setup = current_high > swing_high
                trend_direction = "up"
                bias = "bullish"
            elif weekly_analysis.trend_direction == "down":
                # Looking for break below recent swing low
                breakout_setup = current_low < swing_low
                trend_direction = "down"
                bias = "bearish"

        # RSI momentum confirmation
        rsi_confirmation = False
        if trend_direction == "up" and current_rsi > 50:
            rsi_confirmation = True
        elif trend_direction == "down" and current_rsi < 50:
            rsi_confirmation = True

        # Pattern recognition (simplified)
        pattern_quality = self._analyze_candlestick_pattern(
            fourhour_data[-3:], trend_direction
        )

        # Trend strength (based on momentum)
        if breakout_setup and rsi_confirmation:
            trend_strength = "strong"
        elif breakout_setup or rsi_confirmation:
            trend_strength = "moderate"
        else:
            trend_strength = "weak"

        # Tradeable conditions
        tradeable = (
            weekly_analysis.tradeable
            and daily_analysis.tradeable
            and breakout_setup
            and rsi_confirmation
            and pattern_quality > 0.6
        )

        # Confidence calculation
        timeframe_alignment = (
            1.0 if (weekly_analysis.tradeable and daily_analysis.tradeable) else 0.4
        )
        breakout_quality = 1.0 if breakout_setup else 0.3
        momentum_quality = 1.0 if rsi_confirmation else 0.5

        confidence = (
            timeframe_alignment * 0.4
            + breakout_quality * 0.3
            + momentum_quality * 0.2
            + pattern_quality * 0.1
        )
        confidence = min(max(confidence, 0.0), 1.0)

        return TimeframeAnalysis(
            timeframe="4h",
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            bias=bias,
            tradeable=tradeable,
            confidence=confidence,
            ema_20=0.0,  # Not used for 4H
            ema_50=0.0,  # Not used for 4H
            rsi=current_rsi,
            adx=0.0,  # Not calculated for 4H
        )

    async def generate_multi_timeframe_signal(
        self,
        pair: str,
        weekly_data: List[PriceData],
        daily_data: List[PriceData],
        fourhour_data: List[PriceData],
    ) -> TradingSignal:
        """
        Generate trading signal based on multi-timeframe analysis.

        Confluence Requirements:
        - Minimum 2/3 timeframes must align for trade execution
        - Weekly trend + Daily setup + 4H trigger = optimal entry
        - Risk only 1-2% per trade with 1:3 minimum R:R ratio
        """

        # Analyze each timeframe
        weekly_analysis = await self.analyze_weekly_trend(weekly_data)
        daily_analysis = await self.analyze_daily_swing(daily_data, weekly_analysis)
        fourhour_analysis = await self.analyze_fourhour_execution(
            fourhour_data, weekly_analysis, daily_analysis
        )

        # Calculate confluence score
        confluence_score = self._calculate_confluence_score(
            weekly_analysis, daily_analysis, fourhour_analysis
        )

        # Determine primary direction
        directions = [
            weekly_analysis.trend_direction,
            daily_analysis.trend_direction,
            fourhour_analysis.trend_direction,
        ]
        direction_counts = {d: directions.count(d) for d in set(directions)}
        primary_direction = max(
            direction_counts.keys(), key=lambda k: direction_counts[k]
        )

        # Generate trading recommendation
        if confluence_score >= self.confluence_threshold and primary_direction in [
            "up",
            "down",
        ]:
            if primary_direction == "up":
                signal_type = SignalType.BUY
                trade_recommendation = f"BUY - {confluence_score:.1%} confluence"
            else:
                signal_type = SignalType.SELL
                trade_recommendation = f"SELL - {confluence_score:.1%} confluence"
        else:
            signal_type = SignalType.HOLD
            trade_recommendation = f"HOLD - {confluence_score:.1%} confluence (below {self.confluence_threshold:.1%} threshold)"

        # Calculate overall confidence
        timeframe_confidences = [
            weekly_analysis.confidence,
            daily_analysis.confidence,
            fourhour_analysis.confidence,
        ]
        overall_confidence = float(confluence_score * np.mean(timeframe_confidences))

        # Extract pair and timeframe info
        pair_parts = pair.split("_")
        currency_pair = f"{pair_parts[0]}_{pair_parts[1]}"

        # Use the current price from 4H data (most recent)
        current_price = fourhour_data[-1].close

        # Create signal
        signal = TradingSignal(
            pair=currency_pair,
            timeframe="4H",  # Primary execution timeframe
            signal_type=signal_type,
            price=current_price,
            fast_ma=weekly_analysis.ema_20,
            slow_ma=weekly_analysis.ema_50,
            confidence=overall_confidence,
            strategy_type="multi_timeframe_enhanced",
        )

        return signal

    def _calculate_confluence_score(
        self,
        weekly: TimeframeAnalysis,
        daily: TimeframeAnalysis,
        fourhour: TimeframeAnalysis,
    ) -> float:
        """Calculate confluence score based on timeframe alignment."""

        # Direction alignment (most important)
        directions = [
            weekly.trend_direction,
            daily.trend_direction,
            fourhour.trend_direction,
        ]
        same_direction_count = max([directions.count(d) for d in set(directions)])
        direction_score = same_direction_count / 3.0

        # Tradeable alignment
        tradeable_count = sum([weekly.tradeable, daily.tradeable, fourhour.tradeable])
        tradeable_score = tradeable_count / 3.0

        # Confidence alignment
        confidence_score = np.mean(
            [weekly.confidence, daily.confidence, fourhour.confidence]
        )

        # Weighted combination
        confluence = float(
            direction_score * 0.5 + tradeable_score * 0.3 + confidence_score * 0.2
        )
        return max(0.0, min(confluence, 1.0))

    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]

        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]

        return ema

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        result = pd.Series(prices).rolling(window=period).mean()
        return np.array(result.fillna(prices[0]).values, dtype=np.float64)

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = pd.Series(gains).rolling(window=period).mean()
        avg_losses = pd.Series(losses).rolling(window=period).mean()

        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        # Prepend first value to match original array length
        rsi_values = np.array(rsi.fillna(50).values, dtype=np.float64)
        return np.concatenate([np.array([50.0], dtype=np.float64), rsi_values])

    def _calculate_adx(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
    ) -> np.ndarray:
        """Calculate Average Directional Index."""
        # Simplified ADX calculation
        high_diff = np.diff(highs)
        low_diff = -np.diff(lows)

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        # True Range
        tr1 = highs[1:] - lows[1:]
        tr2 = np.abs(highs[1:] - closes[:-1])
        tr3 = np.abs(lows[1:] - closes[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # Smooth the values
        plus_di = (
            100
            * pd.Series(plus_dm).rolling(window=period).mean()
            / pd.Series(tr).rolling(window=period).mean()
        )
        minus_di = (
            100
            * pd.Series(minus_dm).rolling(window=period).mean()
            / pd.Series(tr).rolling(window=period).mean()
        )

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = pd.Series(dx).rolling(window=period).mean()

        # Prepend values to match original array length
        adx_values = np.array(adx.fillna(20.0).values, dtype=np.float64)
        return np.concatenate([np.array([20.0, 20.0], dtype=np.float64), adx_values])

    def _analyze_candlestick_pattern(
        self, candles: List[PriceData], trend_direction: str
    ) -> float:
        """Analyze candlestick patterns for quality score."""
        if len(candles) < 2:
            return 0.5

        current = candles[-1]
        previous = candles[-2]

        # Basic pattern recognition
        pattern_score = 0.5  # Neutral base

        # Bullish patterns in uptrend
        if trend_direction == "up":
            # Bullish engulfing
            if (
                current.close > current.open
                and previous.close < previous.open
                and current.open < previous.close
                and current.close > previous.open
            ):
                pattern_score = 0.9
            # Hammer
            elif current.close > current.open and (current.close - current.open) > 2 * (
                current.open - current.low
            ):
                pattern_score = 0.8
            # Strong bullish candle
            elif current.close > current.open and (
                current.close - current.open
            ) > 0.7 * (current.high - current.low):
                pattern_score = 0.7

        # Bearish patterns in downtrend
        elif trend_direction == "down":
            # Bearish engulfing
            if (
                current.close < current.open
                and previous.close > previous.open
                and current.open > previous.close
                and current.close < previous.open
            ):
                pattern_score = 0.9
            # Shooting star
            elif current.close < current.open and (current.high - current.open) > 2 * (
                current.close - current.low
            ):
                pattern_score = 0.8
            # Strong bearish candle
            elif current.close < current.open and (
                current.open - current.close
            ) > 0.7 * (current.high - current.low):
                pattern_score = 0.7

        return pattern_score

    async def get_trading_style_recommendation(
        self, confluence_analysis: MultiTimeframeAnalysis
    ) -> TradingStyle:
        """Recommend optimal trading style based on timeframe analysis."""

        if (
            confluence_analysis.weekly.tradeable
            and confluence_analysis.weekly.trend_strength == "strong"
        ):
            return TradingStyle.POSITION
        elif (
            confluence_analysis.daily.tradeable
            and confluence_analysis.confluence_score > 0.7
        ):
            return TradingStyle.SWING
        elif confluence_analysis.fourhour.tradeable:
            return TradingStyle.PRECISION
        else:
            return TradingStyle.PRECISION  # Default to most conservative
