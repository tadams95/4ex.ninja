"""
Sentiment Analyzer for risk-on vs risk-off market conditions.

This module analyzes currency pair correlations and safe haven flows
to determine overall market risk sentiment for regime classification.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_providers.base_provider import SwingCandleData

logger = logging.getLogger(__name__)


@dataclass
class SentimentAnalysis:
    """Risk sentiment analysis result."""

    risk_sentiment_score: float  # -1.0 (risk-off) to 1.0 (risk-on)
    safe_haven_strength: float  # Strength of safe haven flows
    risk_asset_performance: float  # Performance of risk assets
    correlation_breakdown: bool  # Whether normal correlations are breaking down
    sentiment_regime: str  # 'risk_on', 'risk_off', 'neutral', 'transition'
    confidence: float


class SentimentAnalyzer:
    """
    Analyzes market risk sentiment through currency pair behavior.

    Identifies risk-on vs risk-off conditions by analyzing safe haven flows,
    risk asset performance, and correlation patterns.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration parameters."""
        self.config = config.get("regime_detection", {})
        self.sentiment_config = self.config.get("risk_sentiment", {})

        # Safe haven and risk asset pairs
        self.safe_haven_pairs = self.sentiment_config.get(
            "safe_haven_pairs", ["USDJPY", "USDCHF"]
        )
        self.risk_pairs = self.sentiment_config.get("risk_pairs", ["AUDUSD", "NZDUSD"])

        # Analysis parameters
        self.sentiment_threshold = self.sentiment_config.get("sentiment_threshold", 0.6)
        self.correlation_lookback = self.sentiment_config.get(
            "correlation_lookback_days", 30
        )

        logger.info("SentimentAnalyzer initialized")

    async def analyze_risk_sentiment(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze risk sentiment across currency pairs.

        Args:
            market_data: Dictionary containing price data for multiple pairs

        Returns:
            Dictionary with risk sentiment analysis
        """
        try:
            if not market_data:
                return self._get_default_sentiment_analysis()

            # Extract relevant pairs for sentiment analysis
            safe_haven_data = {
                pair: candles
                for pair, candles in market_data.items()
                if pair in self.safe_haven_pairs and candles
            }
            risk_asset_data = {
                pair: candles
                for pair, candles in market_data.items()
                if pair in self.risk_pairs and candles
            }

            # Analyze sentiment components
            sentiment_analysis = self._analyze_sentiment_components(
                safe_haven_data, risk_asset_data, market_data
            )

            logger.debug("Risk sentiment analysis completed")
            return sentiment_analysis

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._get_default_sentiment_analysis()

    def _analyze_sentiment_components(
        self,
        safe_haven_data: Dict[str, List[SwingCandleData]],
        risk_asset_data: Dict[str, List[SwingCandleData]],
        all_market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze individual sentiment components."""

        # Calculate safe haven performance
        safe_haven_strength = self._calculate_safe_haven_strength(safe_haven_data)

        # Calculate risk asset performance
        risk_asset_performance = self._calculate_risk_asset_performance(risk_asset_data)

        # Analyze correlation patterns
        correlation_breakdown = self._analyze_correlation_breakdown(all_market_data)

        # Calculate overall sentiment score
        sentiment_score = self._calculate_sentiment_score(
            safe_haven_strength, risk_asset_performance, correlation_breakdown
        )

        # Determine sentiment regime
        sentiment_regime = self._classify_sentiment_regime(sentiment_score)

        # Calculate confidence
        confidence = self._calculate_sentiment_confidence(
            safe_haven_strength,
            risk_asset_performance,
            len(safe_haven_data),
            len(risk_asset_data),
        )

        return {
            "risk_sentiment_score": sentiment_score,
            "safe_haven_strength": safe_haven_strength,
            "risk_asset_performance": risk_asset_performance,
            "correlation_breakdown": correlation_breakdown,
            "sentiment_regime": sentiment_regime,
            "confidence": confidence,
            "safe_haven_pairs_analyzed": len(safe_haven_data),
            "risk_pairs_analyzed": len(risk_asset_data),
            "individual_analysis": {
                "safe_haven": {
                    pair: self._analyze_single_pair_sentiment(candles, "safe_haven")
                    for pair, candles in safe_haven_data.items()
                },
                "risk_assets": {
                    pair: self._analyze_single_pair_sentiment(candles, "risk_asset")
                    for pair, candles in risk_asset_data.items()
                },
            },
        }

    def _calculate_safe_haven_strength(
        self, safe_haven_data: Dict[str, List[SwingCandleData]]
    ) -> float:
        """Calculate strength of safe haven flows."""

        if not safe_haven_data:
            return 0.0

        safe_haven_scores = []

        for pair, candles in safe_haven_data.items():
            if len(candles) < 20:
                continue

            # Calculate recent performance (last 10 periods vs previous 10)
            prices = np.array([float(candle.close) for candle in candles])

            if len(prices) >= 20:
                recent_performance = (
                    np.mean(prices[-10:]) / np.mean(prices[-20:-10]) - 1
                )

                # For USD safe haven pairs (USDJPY, USDCHF), positive performance indicates safe haven demand
                # Normalize the score
                normalized_score = np.tanh(
                    recent_performance * 20
                )  # Scale for sensitivity
                safe_haven_scores.append(normalized_score)

        if not safe_haven_scores:
            return 0.0

        return float(np.mean(safe_haven_scores))

    def _calculate_risk_asset_performance(
        self, risk_asset_data: Dict[str, List[SwingCandleData]]
    ) -> float:
        """Calculate performance of risk assets."""

        if not risk_asset_data:
            return 0.0

        risk_asset_scores = []

        for pair, candles in risk_asset_data.items():
            if len(candles) < 20:
                continue

            # Calculate recent performance
            prices = np.array([float(candle.close) for candle in candles])

            if len(prices) >= 20:
                recent_performance = (
                    np.mean(prices[-10:]) / np.mean(prices[-20:-10]) - 1
                )

                # For risk pairs (AUDUSD, NZDUSD), positive performance indicates risk-on sentiment
                normalized_score = np.tanh(recent_performance * 20)
                risk_asset_scores.append(normalized_score)

        if not risk_asset_scores:
            return 0.0

        return float(np.mean(risk_asset_scores))

    def _analyze_correlation_breakdown(self, market_data: Dict[str, Any]) -> bool:
        """Analyze whether normal correlations are breaking down."""

        # Extract major pairs for correlation analysis
        major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"]
        available_pairs = [
            pair for pair in major_pairs if pair in market_data and market_data[pair]
        ]

        if len(available_pairs) < 3:
            return False

        # Calculate recent correlations
        correlation_matrix = self._calculate_correlation_matrix(
            available_pairs, market_data
        )

        # Check for unusual correlation patterns
        # In normal markets, certain pairs should be correlated (e.g., EURUSD and GBPUSD)
        # During stress, these correlations often break down

        expected_correlations = {
            ("EURUSD", "GBPUSD"): 0.7,  # Typically positively correlated
            ("USDJPY", "USDCHF"): 0.6,  # Both USD strength plays
            ("AUDUSD", "NZDUSD"): 0.8,  # Both commodity currencies
        }

        breakdown_count = 0
        total_checks = 0

        for (pair1, pair2), expected_corr in expected_correlations.items():
            if pair1 in available_pairs and pair2 in available_pairs:
                actual_corr = correlation_matrix.get((pair1, pair2), 0.0)

                # Check if correlation is significantly different from expected
                if abs(actual_corr - expected_corr) > 0.4:
                    breakdown_count += 1
                total_checks += 1

        # Consider correlation breakdown if more than 50% of expected correlations are off
        return breakdown_count / total_checks > 0.5 if total_checks > 0 else False

    def _calculate_correlation_matrix(
        self, pairs: List[str], market_data: Dict[str, Any]
    ) -> Dict[tuple, float]:
        """Calculate correlation matrix for the given pairs."""

        correlations = {}

        # Extract returns for each pair
        pair_returns = {}
        min_length = float("inf")

        for pair in pairs:
            if pair not in market_data or not market_data[pair]:
                continue

            prices = np.array([float(candle.close) for candle in market_data[pair]])
            if len(prices) < 20:
                continue

            returns = np.diff(np.log(prices[-30:]))  # Last 30 periods
            pair_returns[pair] = returns
            min_length = min(min_length, len(returns))

        if min_length == float("inf") or min_length < 10:
            return correlations

        # Calculate pairwise correlations
        for i, pair1 in enumerate(pairs):
            if pair1 not in pair_returns:
                continue

            for j, pair2 in enumerate(pairs):
                if j <= i or pair2 not in pair_returns:
                    continue

                returns1 = pair_returns[pair1][-min_length:]
                returns2 = pair_returns[pair2][-min_length:]

                if len(returns1) == len(returns2) and len(returns1) > 0:
                    correlation = float(np.corrcoef(returns1, returns2)[0, 1])
                    correlations[(pair1, pair2)] = correlation
                    correlations[(pair2, pair1)] = correlation

        return correlations

    def _calculate_sentiment_score(
        self,
        safe_haven_strength: float,
        risk_asset_performance: float,
        correlation_breakdown: bool,
    ) -> float:
        """Calculate overall sentiment score."""

        # Base sentiment from asset performance
        # Risk-on: risk assets up, safe havens down
        # Risk-off: risk assets down, safe havens up
        base_sentiment = (risk_asset_performance - safe_haven_strength) / 2

        # Adjust for correlation breakdown (indicates stress)
        if correlation_breakdown:
            # Correlation breakdown typically indicates risk-off conditions
            stress_adjustment = -0.3
        else:
            stress_adjustment = 0.0

        sentiment_score = base_sentiment + stress_adjustment

        # Ensure score is in -1 to 1 range
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        return sentiment_score

    def _classify_sentiment_regime(self, sentiment_score: float) -> str:
        """Classify sentiment into regime categories."""

        if sentiment_score > self.sentiment_threshold:
            return "risk_on"
        elif sentiment_score < -self.sentiment_threshold:
            return "risk_off"
        elif abs(sentiment_score) < 0.2:
            return "neutral"
        else:
            return "transition"

    def _calculate_sentiment_confidence(
        self,
        safe_haven_strength: float,
        risk_asset_performance: float,
        safe_haven_count: int,
        risk_asset_count: int,
    ) -> float:
        """Calculate confidence in sentiment analysis."""

        # Higher confidence with more extreme sentiment readings
        signal_strength = abs(safe_haven_strength) + abs(risk_asset_performance)

        # Higher confidence with more pairs analyzed
        data_quality = min((safe_haven_count + risk_asset_count) / 4, 1.0)

        # Combine factors
        confidence = signal_strength * 0.7 + data_quality * 0.3

        return min(max(confidence, 0.0), 1.0)

    def _analyze_single_pair_sentiment(
        self, candles: List[SwingCandleData], pair_type: str
    ) -> Dict[str, float]:
        """Analyze sentiment indicators for a single pair."""

        if len(candles) < 10:
            return {"performance": 0.0, "volatility": 0.0, "momentum": 0.0}

        prices = np.array([float(candle.close) for candle in candles])

        # Recent performance
        if len(prices) >= 10:
            performance = (prices[-1] / prices[-10] - 1) * 100
        else:
            performance = 0.0

        # Volatility
        if len(prices) >= 5:
            returns = np.diff(np.log(prices[-20:]))
            volatility = float(np.std(returns) * 100) if len(returns) > 0 else 0.0
        else:
            volatility = 0.0

        # Momentum
        if len(prices) >= 5:
            momentum = float((prices[-1] - prices[-5]) / prices[-5] * 100)
        else:
            momentum = 0.0

        return {
            "performance": performance,
            "volatility": volatility,
            "momentum": momentum,
        }

    def _get_default_sentiment_analysis(self) -> Dict[str, Any]:
        """Return default sentiment analysis for error cases."""
        return {
            "risk_sentiment_score": 0.0,
            "safe_haven_strength": 0.0,
            "risk_asset_performance": 0.0,
            "correlation_breakdown": False,
            "sentiment_regime": "neutral",
            "confidence": 0.0,
            "safe_haven_pairs_analyzed": 0,
            "risk_pairs_analyzed": 0,
            "individual_analysis": {"safe_haven": {}, "risk_assets": {}},
        }
