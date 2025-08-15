"""
Trend Analyzer for market regime detection.

This module analyzes trend strength and direction to support
swing trading strategy optimization and regime classification.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_providers.base_provider import SwingCandleData

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    """Trend analysis result for a currency pair."""

    direction: Optional[str]  # 'up', 'down', or None
    strength: float  # 0.0 to 1.0
    consistency: float  # How consistent the trend is
    momentum: float  # Current momentum
    trend_age_periods: int  # How long trend has been active
    confidence: float


class TrendAnalyzer:
    """
    Analyzes trend characteristics for regime detection.

    Identifies trend strength, direction, and momentum to support
    swing trading decisions and market regime classification.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration parameters."""
        self.config = config.get("regime_detection", {})
        self.trend_params = self.config.get("trend_parameters", {})

        # Trend analysis parameters
        self.sma_fast = self.trend_params.get("sma_fast_period", 20)
        self.sma_slow = self.trend_params.get("sma_slow_period", 50)
        self.momentum_period = 14  # For momentum calculation
        self.trend_lookback = 50  # Periods to analyze for trend

        logger.info("TrendAnalyzer initialized")

    async def analyze_trend_strength(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze trend strength across currency pairs.

        Args:
            market_data: Dictionary containing price data for multiple pairs

        Returns:
            Dictionary with trend analysis results
        """
        try:
            if not market_data:
                return self._get_default_trend_analysis()

            pair_trends = {}

            # Analyze each currency pair
            for pair, candles in market_data.items():
                if pair in ["timestamp", "timeframe"] or not candles:
                    continue

                trend_info = self._analyze_single_pair_trend(pair, candles)
                pair_trends[pair] = trend_info

            # Aggregate trend analysis
            overall_analysis = self._aggregate_trend_analysis(pair_trends)

            logger.debug(f"Trend analysis completed for {len(pair_trends)} pairs")
            return overall_analysis

        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return self._get_default_trend_analysis()

    def _analyze_single_pair_trend(
        self, pair: str, candles: List[SwingCandleData]
    ) -> TrendAnalysis:
        """Analyze trend for a single currency pair."""

        if len(candles) < max(self.sma_slow, self.trend_lookback) + 10:
            logger.warning(f"Insufficient data for trend analysis: {pair}")
            return TrendAnalysis(
                direction=None,
                strength=0.5,
                consistency=0.0,
                momentum=0.0,
                trend_age_periods=0,
                confidence=0.0,
            )

        # Extract price data
        prices = np.array([float(candle.close) for candle in candles])
        highs = np.array([float(candle.high) for candle in candles])
        lows = np.array([float(candle.low) for candle in candles])

        # Calculate moving averages
        sma_fast = self._calculate_sma(prices, self.sma_fast)
        sma_slow = self._calculate_sma(prices, self.sma_slow)

        # Analyze trend direction and strength
        direction, strength = self._determine_trend_direction_strength(
            prices, sma_fast, sma_slow
        )

        # Calculate trend consistency
        consistency = self._calculate_trend_consistency(prices, sma_fast, sma_slow)

        # Calculate momentum
        momentum = self._calculate_momentum(prices)

        # Calculate trend age
        trend_age = self._calculate_trend_age(sma_fast, sma_slow)

        # Calculate confidence
        confidence = self._calculate_trend_confidence(strength, consistency, momentum)

        return TrendAnalysis(
            direction=direction,
            strength=strength,
            consistency=consistency,
            momentum=momentum,
            trend_age_periods=trend_age,
            confidence=confidence,
        )

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return np.array([])

        sma = np.zeros(len(prices))
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1 : i + 1])

        return sma[period - 1 :]

    def _determine_trend_direction_strength(
        self, prices: np.ndarray, sma_fast: np.ndarray, sma_slow: np.ndarray
    ) -> tuple[Optional[str], float]:
        """Determine trend direction and strength."""

        if len(sma_fast) == 0 or len(sma_slow) == 0:
            return None, 0.5

        # Align arrays
        min_len = min(len(sma_fast), len(sma_slow))
        fast_recent = sma_fast[-min_len:]
        slow_recent = sma_slow[-min_len:]
        recent_prices = prices[-min_len:]

        if min_len < 10:
            return None, 0.5

        # Current MA relationship
        fast_above_slow = fast_recent[-1] > slow_recent[-1]

        # Price position relative to MAs
        price_above_fast = recent_prices[-1] > fast_recent[-1]
        price_above_slow = recent_prices[-1] > slow_recent[-1]

        # MA slope analysis
        fast_slope = self._calculate_slope(fast_recent[-10:])
        slow_slope = self._calculate_slope(slow_recent[-10:])

        # Determine direction
        if fast_above_slow and price_above_fast and fast_slope > 0:
            direction = "up"
        elif not fast_above_slow and not price_above_fast and fast_slope < 0:
            direction = "down"
        else:
            direction = None

        # Calculate strength components
        ma_separation = abs(fast_recent[-1] - slow_recent[-1]) / slow_recent[-1]
        slope_alignment = 1.0 if (fast_slope > 0) == (slow_slope > 0) else 0.0
        price_ma_alignment = (
            1.0 if (price_above_fast == price_above_slow == fast_above_slow) else 0.5
        )

        # Combine strength indicators
        strength = min(
            (ma_separation * 50 + slope_alignment + price_ma_alignment) / 3, 1.0
        )

        return direction, strength

    def _calculate_slope(self, values: np.ndarray) -> float:
        """Calculate slope of a series using linear regression."""
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        # Normalize slope relative to average value
        avg_value = np.mean(values)
        normalized_slope = slope / avg_value if avg_value != 0 else 0.0

        return normalized_slope

    def _calculate_trend_consistency(
        self, prices: np.ndarray, sma_fast: np.ndarray, sma_slow: np.ndarray
    ) -> float:
        """Calculate how consistent the trend has been."""

        if len(sma_fast) == 0 or len(sma_slow) == 0:
            return 0.0

        # Look at recent periods
        lookback = min(20, min(len(sma_fast), len(sma_slow)))
        fast_recent = sma_fast[-lookback:]
        slow_recent = sma_slow[-lookback:]

        if len(fast_recent) < 5:
            return 0.0

        # Check MA relationship consistency
        fast_above_slow = fast_recent > slow_recent
        current_relationship = fast_above_slow[-1]

        # Count periods where relationship matches current
        consistent_periods = np.sum(fast_above_slow == current_relationship)
        consistency_ratio = consistent_periods / len(fast_above_slow)

        # Check slope consistency
        fast_slopes = []
        slow_slopes = []
        window = 5

        for i in range(window, len(fast_recent)):
            fast_slopes.append(self._calculate_slope(fast_recent[i - window : i]))
            slow_slopes.append(self._calculate_slope(slow_recent[i - window : i]))

        if len(fast_slopes) > 0:
            # Check if slopes are generally in same direction
            fast_slope_consistency = float(
                np.mean(np.array(fast_slopes) > 0)
                if current_relationship
                else np.mean(np.array(fast_slopes) < 0)
            )
            slope_consistency = max(
                fast_slope_consistency, 1.0 - fast_slope_consistency
            )
        else:
            slope_consistency = 0.5

        # Combine consistency measures
        overall_consistency = consistency_ratio * 0.7 + slope_consistency * 0.3

        return overall_consistency

    def _calculate_momentum(self, prices: np.ndarray) -> float:
        """Calculate current momentum."""

        if len(prices) < self.momentum_period + 1:
            return 0.0

        # Rate of change momentum
        roc = (prices[-1] - prices[-self.momentum_period]) / prices[
            -self.momentum_period
        ]

        # RSI-style momentum
        recent_changes = np.diff(prices[-self.momentum_period - 1 :])
        gains = recent_changes[recent_changes > 0]
        losses = abs(recent_changes[recent_changes < 0])

        avg_gain = np.mean(gains) if len(gains) > 0 else 0.0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0

        if avg_loss == 0:
            rsi_momentum = 1.0
        else:
            rs = avg_gain / avg_loss
            rsi_momentum = (rs / (1 + rs)) * 2 - 1  # Normalize to -1 to 1

        # Combine momentum indicators
        momentum = roc * 0.6 + rsi_momentum * 0.4

        # Normalize to -1 to 1 range
        momentum = np.tanh(momentum * 5)

        return float(momentum)

    def _calculate_trend_age(self, sma_fast: np.ndarray, sma_slow: np.ndarray) -> int:
        """Calculate how long the current trend has been active."""

        if len(sma_fast) == 0 or len(sma_slow) == 0:
            return 0

        # Look back to find when MA relationship last changed
        min_len = min(len(sma_fast), len(sma_slow))
        fast_recent = sma_fast[-min_len:]
        slow_recent = sma_slow[-min_len:]

        current_relationship = fast_recent[-1] > slow_recent[-1]

        # Count periods since relationship changed
        trend_age = 0
        for i in range(len(fast_recent) - 1, -1, -1):
            if (fast_recent[i] > slow_recent[i]) == current_relationship:
                trend_age += 1
            else:
                break

        return trend_age

    def _calculate_trend_confidence(
        self, strength: float, consistency: float, momentum: float
    ) -> float:
        """Calculate confidence in trend analysis."""

        # High confidence for strong, consistent trends with momentum
        momentum_factor = min(abs(momentum), 1.0)

        confidence = strength * 0.4 + consistency * 0.4 + momentum_factor * 0.2

        return min(max(confidence, 0.0), 1.0)

    def _aggregate_trend_analysis(
        self, pair_trends: Dict[str, TrendAnalysis]
    ) -> Dict[str, Any]:
        """Aggregate individual pair trend analysis."""

        if not pair_trends:
            return self._get_default_trend_analysis()

        # Count trend directions
        up_trends = sum(1 for t in pair_trends.values() if t.direction == "up")
        down_trends = sum(1 for t in pair_trends.values() if t.direction == "down")
        no_trend = len(pair_trends) - up_trends - down_trends

        # Calculate averages
        avg_strength = np.mean([t.strength for t in pair_trends.values()])
        avg_consistency = np.mean([t.consistency for t in pair_trends.values()])
        avg_momentum = np.mean([t.momentum for t in pair_trends.values()])
        avg_confidence = np.mean([t.confidence for t in pair_trends.values()])

        # Determine overall market trend bias
        total_pairs = len(pair_trends)
        if up_trends > total_pairs * 0.6:
            market_bias = "bullish"
        elif down_trends > total_pairs * 0.6:
            market_bias = "bearish"
        else:
            market_bias = "mixed"

        # Calculate trend strength distribution
        strong_trends = sum(1 for t in pair_trends.values() if t.strength > 0.7)
        weak_trends = sum(1 for t in pair_trends.values() if t.strength < 0.4)

        return {
            "strength": avg_strength,
            "consistency": avg_consistency,
            "momentum": avg_momentum,
            "confidence": avg_confidence,
            "market_bias": market_bias,
            "trend_distribution": {
                "up_trends": up_trends,
                "down_trends": down_trends,
                "no_trend": no_trend,
                "strong_trends": strong_trends,
                "weak_trends": weak_trends,
            },
            "pair_count": total_pairs,
            "individual_pairs": {
                pair: {
                    "direction": t.direction,
                    "strength": t.strength,
                    "consistency": t.consistency,
                    "momentum": t.momentum,
                    "trend_age": t.trend_age_periods,
                    "confidence": t.confidence,
                }
                for pair, t in pair_trends.items()
            },
        }

    def _get_default_trend_analysis(self) -> Dict[str, Any]:
        """Return default trend analysis for error cases."""
        return {
            "strength": 0.5,
            "consistency": 0.0,
            "momentum": 0.0,
            "confidence": 0.0,
            "market_bias": "mixed",
            "trend_distribution": {
                "up_trends": 0,
                "down_trends": 0,
                "no_trend": 0,
                "strong_trends": 0,
                "weak_trends": 0,
            },
            "pair_count": 0,
            "individual_pairs": {},
        }
