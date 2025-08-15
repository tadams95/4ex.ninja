"""
Volatility Analyzer for regime detection.

This module analyzes market volatility patterns to classify volatility regimes
and provide insights for risk management and position sizing in swing trading.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_providers.base_provider import SwingCandleData

logger = logging.getLogger(__name__)


@dataclass
class VolatilityRegime:
    """Volatility regime classification result."""

    regime: str  # 'low', 'normal', 'high', 'extreme'
    current_volatility: float
    percentile_rank: float  # Where current vol sits in historical distribution
    normalized_volatility: float  # Volatility relative to average
    regime_persistence: float  # How long we've been in this regime
    confidence: float


class VolatilityAnalyzer:
    """
    Analyzes volatility patterns for regime classification.

    Identifies volatility regimes to support risk management and
    position sizing decisions in swing trading.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration parameters."""
        self.config = config.get("regime_detection", {})
        self.vol_thresholds = self.config.get("volatility_thresholds", {})

        # Volatility thresholds
        self.low_vol_threshold = self.vol_thresholds.get("low_volatility", 0.005)
        self.high_vol_threshold = self.vol_thresholds.get("high_volatility", 0.015)
        self.extreme_vol_threshold = self.vol_thresholds.get(
            "extreme_volatility", 0.025
        )

        # Analysis parameters
        self.lookback_periods = 100  # Periods for volatility calculation
        self.regime_memory = 20  # Periods to remember for regime persistence

        logger.info("VolatilityAnalyzer initialized")

    async def analyze_volatility_regime(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze volatility regime across currency pairs.

        Args:
            market_data: Dictionary containing price data for multiple pairs

        Returns:
            Dictionary with volatility regime analysis
        """
        try:
            if not market_data:
                return self._get_default_volatility_analysis()

            pair_volatilities = {}

            # Analyze each currency pair
            for pair, candles in market_data.items():
                if pair in ["timestamp", "timeframe"] or not candles:
                    continue

                volatility_info = self._analyze_single_pair_volatility(pair, candles)
                pair_volatilities[pair] = volatility_info

            # Aggregate volatility analysis
            overall_analysis = self._aggregate_volatility_analysis(pair_volatilities)

            logger.debug(
                f"Volatility analysis completed for {len(pair_volatilities)} pairs"
            )
            return overall_analysis

        except Exception as e:
            logger.error(f"Error in volatility analysis: {e}")
            return self._get_default_volatility_analysis()

    def _analyze_single_pair_volatility(
        self, pair: str, candles: List[SwingCandleData]
    ) -> VolatilityRegime:
        """Analyze volatility for a single currency pair."""

        if len(candles) < self.lookback_periods:
            logger.warning(f"Insufficient data for volatility analysis: {pair}")
            return VolatilityRegime(
                regime="normal",
                current_volatility=0.01,
                percentile_rank=0.5,
                normalized_volatility=1.0,
                regime_persistence=0.0,
                confidence=0.0,
            )

        # Calculate returns
        prices = np.array([float(candle.close) for candle in candles])
        returns = np.diff(np.log(prices))

        # Current volatility (last 20 periods)
        recent_returns = returns[-20:]
        current_volatility = np.std(recent_returns) * np.sqrt(
            24
        )  # Annualized for 4H data

        # Historical volatility distribution
        historical_volatilities = self._calculate_rolling_volatility(returns, window=20)

        if len(historical_volatilities) == 0:
            return VolatilityRegime(
                regime="normal",
                current_volatility=current_volatility,
                percentile_rank=0.5,
                normalized_volatility=1.0,
                regime_persistence=0.0,
                confidence=0.5,
            )

        # Percentile rank of current volatility
        percentile_rank = np.mean(historical_volatilities <= current_volatility)

        # Normalized volatility (relative to median)
        median_vol = np.median(historical_volatilities)
        normalized_volatility = (
            current_volatility / median_vol if median_vol > 0 else 1.0
        )

        # Classify regime
        regime = self._classify_volatility_regime(
            current_volatility, normalized_volatility
        )

        # Calculate regime persistence
        recent_regimes = [
            self._classify_volatility_regime(vol, vol / median_vol)
            for vol in historical_volatilities[-self.regime_memory :]
        ]
        regime_persistence = float(np.mean([r == regime for r in recent_regimes]))

        # Calculate confidence
        confidence = self._calculate_volatility_confidence(
            current_volatility, percentile_rank, regime_persistence
        )

        return VolatilityRegime(
            regime=regime,
            current_volatility=current_volatility,
            percentile_rank=percentile_rank,
            normalized_volatility=normalized_volatility,
            regime_persistence=regime_persistence,
            confidence=confidence,
        )

    def _calculate_rolling_volatility(
        self, returns: np.ndarray, window: int
    ) -> np.ndarray:
        """Calculate rolling volatility."""
        if len(returns) < window:
            return np.array([])

        rolling_vol = np.zeros(len(returns) - window + 1)
        for i in range(window - 1, len(returns)):
            window_returns = returns[i - window + 1 : i + 1]
            rolling_vol[i - window + 1] = np.std(window_returns) * np.sqrt(
                24
            )  # Annualized

        return rolling_vol

    def _classify_volatility_regime(
        self, volatility: float, normalized_vol: float
    ) -> str:
        """Classify volatility into regime categories."""

        # Use both absolute and relative thresholds
        if volatility > self.extreme_vol_threshold or normalized_vol > 2.5:
            return "extreme"
        elif volatility > self.high_vol_threshold or normalized_vol > 1.5:
            return "high"
        elif volatility < self.low_vol_threshold or normalized_vol < 0.7:
            return "low"
        else:
            return "normal"

    def _calculate_volatility_confidence(
        self, current_vol: float, percentile: float, persistence: float
    ) -> float:
        """Calculate confidence in volatility regime classification."""

        # High confidence for extreme values
        if percentile > 0.9 or percentile < 0.1:
            confidence = 0.9
        elif percentile > 0.8 or percentile < 0.2:
            confidence = 0.7
        else:
            confidence = 0.5

        # Adjust for regime persistence
        confidence = confidence * (0.5 + 0.5 * persistence)

        return min(max(confidence, 0.0), 1.0)

    def _aggregate_volatility_analysis(
        self, pair_volatilities: Dict[str, VolatilityRegime]
    ) -> Dict[str, Any]:
        """Aggregate individual pair volatility analysis."""

        if not pair_volatilities:
            return self._get_default_volatility_analysis()

        # Get volatility weights from config
        currency_config = self.config.get("currency_pairs", {})
        vol_weights = currency_config.get("volatility_weights", {})

        # Calculate weighted averages
        total_weight = 0.0
        weighted_volatility = 0.0
        weighted_normalized_vol = 0.0
        weighted_confidence = 0.0

        regime_counts = {"low": 0, "normal": 0, "high": 0, "extreme": 0}

        for pair, vol_info in pair_volatilities.items():
            weight = vol_weights.get(pair, 1.0)
            total_weight += weight

            weighted_volatility += vol_info.current_volatility * weight
            weighted_normalized_vol += vol_info.normalized_volatility * weight
            weighted_confidence += vol_info.confidence * weight

            regime_counts[vol_info.regime] += 1

        if total_weight > 0:
            avg_volatility = weighted_volatility / total_weight
            avg_normalized_vol = weighted_normalized_vol / total_weight
            avg_confidence = weighted_confidence / total_weight
        else:
            avg_volatility = 0.01
            avg_normalized_vol = 1.0
            avg_confidence = 0.0

        # Determine overall regime (most common or highest weighted)
        if regime_counts["extreme"] > 0:
            overall_regime = "extreme"
        elif regime_counts["high"] > regime_counts["low"]:
            overall_regime = "high"
        elif regime_counts["low"] > regime_counts["normal"]:
            overall_regime = "low"
        else:
            overall_regime = "normal"

        # Calculate market-wide volatility metrics
        all_volatilities = [v.current_volatility for v in pair_volatilities.values()]
        vol_dispersion = np.std(all_volatilities) if len(all_volatilities) > 1 else 0.0

        return {
            "regime": overall_regime,
            "average_volatility": avg_volatility,
            "normalized_volatility": avg_normalized_vol,
            "volatility_dispersion": vol_dispersion,
            "regime_distribution": regime_counts,
            "confidence": avg_confidence,
            "pair_count": len(pair_volatilities),
            "individual_pairs": {
                pair: {
                    "regime": v.regime,
                    "volatility": v.current_volatility,
                    "percentile": v.percentile_rank,
                    "normalized": v.normalized_volatility,
                    "persistence": v.regime_persistence,
                    "confidence": v.confidence,
                }
                for pair, v in pair_volatilities.items()
            },
        }

    def _get_default_volatility_analysis(self) -> Dict[str, Any]:
        """Return default volatility analysis for error cases."""
        return {
            "regime": "normal",
            "average_volatility": 0.01,
            "normalized_volatility": 1.0,
            "volatility_dispersion": 0.0,
            "regime_distribution": {"low": 0, "normal": 0, "high": 0, "extreme": 0},
            "confidence": 0.0,
            "pair_count": 0,
            "individual_pairs": {},
        }
