"""
Market Classifier for determining trending vs ranging conditions.

This module analyzes market data to classify whether the market is in
a trending or ranging state, which is fundamental for swing trading strategy selection.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_providers.base_provider import SwingCandleData

logger = logging.getLogger(__name__)


@dataclass
class MarketCondition:
    """Market condition classification result."""

    is_trending: bool
    trend_direction: Optional[str]  # 'up', 'down', or None
    trend_strength: float  # 0.0 to 1.0
    ranging_strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timeframe_alignment: Dict[str, bool]  # alignment across timeframes


class MarketClassifier:
    """
    Classifies market conditions as trending or ranging.

    Uses multiple indicators and timeframe analysis to determine
    market state for swing trading optimization.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration parameters."""
        self.config = config.get("regime_detection", {})
        self.trend_params = self.config.get("trend_parameters", {})

        # Default parameters
        self.sma_fast = self.trend_params.get("sma_fast_period", 20)
        self.sma_slow = self.trend_params.get("sma_slow_period", 50)
        self.atr_period = self.trend_params.get("atr_period", 14)
        self.trend_threshold = self.trend_params.get("trend_strength_threshold", 0.7)
        self.ranging_threshold = self.trend_params.get("ranging_threshold", 0.3)

        logger.info("MarketClassifier initialized")

    async def classify_market_condition(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify current market condition across currency pairs.

        Args:
            market_data: Dictionary containing price data for multiple pairs

        Returns:
            Dictionary with market condition classification
        """
        try:
            if not market_data:
                return self._get_default_classification()

            pair_classifications = {}

            # Analyze each currency pair
            for pair, candles in market_data.items():
                if pair in ["timestamp", "timeframe"] or not candles:
                    continue

                classification = self._classify_single_pair(pair, candles)
                pair_classifications[pair] = classification

            # Aggregate classifications
            overall_classification = self._aggregate_classifications(
                pair_classifications
            )

            logger.debug(
                f"Market classification completed for {len(pair_classifications)} pairs"
            )
            return overall_classification

        except Exception as e:
            logger.error(f"Error in market classification: {e}")
            return self._get_default_classification()

    def _classify_single_pair(
        self, pair: str, candles: List[SwingCandleData]
    ) -> MarketCondition:
        """Classify market condition for a single currency pair."""

        if len(candles) < max(self.sma_slow, self.atr_period) + 10:
            logger.warning(f"Insufficient data for {pair}")
            return MarketCondition(
                is_trending=False,
                trend_direction=None,
                trend_strength=0.5,
                ranging_strength=0.5,
                confidence=0.0,
                timeframe_alignment={},
            )

        # Extract price arrays
        prices = np.array([float(candle.close) for candle in candles])
        highs = np.array([float(candle.high) for candle in candles])
        lows = np.array([float(candle.low) for candle in candles])

        # Calculate moving averages
        sma_fast = self._calculate_sma(prices, self.sma_fast)
        sma_slow = self._calculate_sma(prices, self.sma_slow)

        # Calculate ATR for volatility context
        atr = self._calculate_atr(highs, lows, prices, self.atr_period)

        # Determine trend direction and strength
        trend_direction, trend_strength = self._analyze_trend(
            prices, sma_fast, sma_slow
        )

        # Calculate ranging characteristics
        ranging_strength = self._calculate_ranging_strength(prices, highs, lows, atr)

        # Determine if trending
        is_trending = (
            trend_strength > self.trend_threshold
            and ranging_strength < self.ranging_threshold
        )

        # Calculate confidence
        confidence = self._calculate_confidence(trend_strength, ranging_strength)

        return MarketCondition(
            is_trending=is_trending,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            ranging_strength=ranging_strength,
            confidence=confidence,
            timeframe_alignment={},  # TODO: Implement multi-timeframe analysis
        )

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return np.array([])

        sma = np.zeros(len(prices))
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1 : i + 1])

        return sma[period - 1 :]

    def _calculate_atr(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int
    ) -> np.ndarray:
        """Calculate Average True Range."""
        if len(highs) < period + 1:
            return np.array([0.0])

        # True Range calculation
        tr = np.zeros(len(highs) - 1)
        for i in range(1, len(highs)):
            tr[i - 1] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )

        # ATR (moving average of TR)
        if len(tr) < period:
            return np.array([np.mean(tr)])

        atr = np.zeros(len(tr) - period + 1)
        for i in range(period - 1, len(tr)):
            atr[i - period + 1] = np.mean(tr[i - period + 1 : i + 1])

        return atr

    def _analyze_trend(
        self, prices: np.ndarray, sma_fast: np.ndarray, sma_slow: np.ndarray
    ) -> tuple[Optional[str], float]:
        """Analyze trend direction and strength."""

        if len(sma_fast) == 0 or len(sma_slow) == 0:
            return None, 0.5

        # Align arrays (take the overlapping portion)
        min_len = min(len(sma_fast), len(sma_slow))
        fast_recent = sma_fast[-min_len:]
        slow_recent = sma_slow[-min_len:]

        if min_len < 10:
            return None, 0.5

        # Current MA relationship
        fast_above_slow = fast_recent[-1] > slow_recent[-1]

        # Trend consistency over recent periods
        lookback = min(20, min_len)
        trend_consistency = 0.0

        for i in range(-lookback, 0):
            if (fast_recent[i] > slow_recent[i]) == fast_above_slow:
                trend_consistency += 1

        trend_consistency /= lookback

        # Price momentum
        recent_prices = prices[-min_len:]
        price_momentum = self._calculate_momentum(recent_prices, lookback)

        # Combine trend strength indicators
        trend_strength = trend_consistency * 0.6 + abs(price_momentum) * 0.4

        # Determine direction
        direction = (
            "up"
            if fast_above_slow and price_momentum > 0
            else "down" if not fast_above_slow and price_momentum < 0 else None
        )

        return direction, trend_strength

    def _calculate_momentum(self, prices: np.ndarray, lookback: int) -> float:
        """Calculate price momentum over lookback period."""
        if len(prices) < lookback + 1:
            return 0.0

        # Rate of change
        roc = (prices[-1] - prices[-lookback]) / prices[-lookback]

        # Normalize to -1 to 1 range (using 2% as reference for strong momentum)
        normalized_momentum = np.tanh(roc / 0.02)

        return normalized_momentum

    def _calculate_ranging_strength(
        self, prices: np.ndarray, highs: np.ndarray, lows: np.ndarray, atr: np.ndarray
    ) -> float:
        """Calculate how much the market is ranging."""

        if len(prices) < 20 or len(atr) == 0:
            return 0.5

        # Look at recent price action
        lookback = min(20, len(prices))
        recent_prices = prices[-lookback:]
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        current_atr = atr[-1] if len(atr) > 0 else 0.01

        # Calculate range characteristics
        price_range = np.max(recent_highs) - np.min(recent_lows)
        normalized_range = (
            price_range / (current_atr * lookback) if current_atr > 0 else 0
        )

        # Price distribution (how much time spent in middle of range)
        range_low = np.min(recent_lows)
        range_high = np.max(recent_highs)
        middle_zone = 0.4  # Middle 40% of range

        middle_low = range_low + (range_high - range_low) * (0.5 - middle_zone / 2)
        middle_high = range_low + (range_high - range_low) * (0.5 + middle_zone / 2)

        time_in_middle = np.sum(
            (recent_prices >= middle_low) & (recent_prices <= middle_high)
        ) / len(recent_prices)

        # Ranging strength (higher when range is wide but price stays in middle)
        ranging_strength = min(normalized_range * time_in_middle, 1.0)

        return ranging_strength

    def _calculate_confidence(
        self, trend_strength: float, ranging_strength: float
    ) -> float:
        """Calculate confidence in classification."""

        # High confidence when clearly trending or clearly ranging
        if trend_strength > 0.8 or ranging_strength > 0.8:
            return 0.9
        elif trend_strength > 0.6 or ranging_strength > 0.6:
            return 0.7
        elif abs(trend_strength - ranging_strength) > 0.3:
            return 0.6
        else:
            return 0.4  # Low confidence in transition periods

    def _aggregate_classifications(
        self, pair_classifications: Dict[str, MarketCondition]
    ) -> Dict[str, Any]:
        """Aggregate individual pair classifications into overall market view."""

        if not pair_classifications:
            return self._get_default_classification()

        # Count trending vs ranging
        trending_count = sum(1 for c in pair_classifications.values() if c.is_trending)
        total_pairs = len(pair_classifications)

        # Average metrics
        avg_trend_strength = np.mean(
            [c.trend_strength for c in pair_classifications.values()]
        )
        avg_ranging_strength = np.mean(
            [c.ranging_strength for c in pair_classifications.values()]
        )
        avg_confidence = np.mean([c.confidence for c in pair_classifications.values()])

        # Overall classification
        trending_percentage = trending_count / total_pairs
        is_trending = trending_percentage > 0.6  # Majority of pairs trending

        # Determine dominant direction
        up_trends = sum(
            1
            for c in pair_classifications.values()
            if c.is_trending and c.trend_direction == "up"
        )
        down_trends = sum(
            1
            for c in pair_classifications.values()
            if c.is_trending and c.trend_direction == "down"
        )

        if up_trends > down_trends:
            dominant_direction = "up"
        elif down_trends > up_trends:
            dominant_direction = "down"
        else:
            dominant_direction = "mixed"

        return {
            "is_trending": is_trending,
            "trending_percentage": trending_percentage,
            "dominant_direction": dominant_direction,
            "trend_strength": avg_trend_strength,
            "ranging_strength": avg_ranging_strength,
            "confidence": avg_confidence,
            "pair_count": total_pairs,
            "individual_pairs": {
                pair: {
                    "is_trending": c.is_trending,
                    "direction": c.trend_direction,
                    "strength": c.trend_strength,
                    "confidence": c.confidence,
                }
                for pair, c in pair_classifications.items()
            },
        }

    def _get_default_classification(self) -> Dict[str, Any]:
        """Return default classification for error cases."""
        return {
            "is_trending": False,
            "trending_percentage": 0.0,
            "dominant_direction": "mixed",
            "trend_strength": 0.5,
            "ranging_strength": 0.5,
            "confidence": 0.0,
            "pair_count": 0,
            "individual_pairs": {},
        }
