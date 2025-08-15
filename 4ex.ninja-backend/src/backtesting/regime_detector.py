"""
Market Regime Detection Engine for Swing Trading.

This module orchestrates the detection of market regimes by combining
multiple analysis components to identify trending vs ranging markets,
volatility regimes, and sentiment shifts.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .market_classifier import MarketClassifier
from .volatility_analyzer import VolatilityAnalyzer
from .trend_analyzer import TrendAnalyzer
from .sentiment_analyzer import SentimentAnalyzer
from .economic_event_analyzer import EconomicEventAnalyzer
from .data_infrastructure import DataInfrastructure

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications."""

    TRENDING_HIGH_VOL = "trending_high_vol"
    TRENDING_LOW_VOL = "trending_low_vol"
    RANGING_HIGH_VOL = "ranging_high_vol"
    RANGING_LOW_VOL = "ranging_low_vol"
    TRANSITION = "transition"
    UNCERTAIN = "uncertain"


class RiskSentiment(Enum):
    """Risk sentiment classifications."""

    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"


@dataclass
class RegimeDetectionResult:
    """Results from regime detection analysis."""

    timestamp: datetime
    regime: MarketRegime
    sentiment: RiskSentiment
    confidence: float
    volatility_level: str
    trend_strength: float
    regime_duration_hours: float
    contributing_factors: List[str]
    next_evaluation: datetime


class RegimeDetector:
    """
    Main regime detection orchestrator.

    Combines multiple analysis components to identify current market regime
    and provide confidence metrics for swing trading optimization.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the regime detector with configuration."""
        self.config = self._load_config(config_path)
        self.data_infrastructure = DataInfrastructure()

        # Initialize analysis components
        self.market_classifier = MarketClassifier(self.config)
        self.volatility_analyzer = VolatilityAnalyzer(self.config)
        self.trend_analyzer = TrendAnalyzer(self.config)
        self.sentiment_analyzer = SentimentAnalyzer(self.config)
        self.economic_analyzer = EconomicEventAnalyzer(self.config)

        # Regime tracking
        self.current_regime: Optional[MarketRegime] = None
        self.regime_start_time: Optional[datetime] = None
        self.regime_history: List[RegimeDetectionResult] = []

        logger.info("RegimeDetector initialized successfully")

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if config_path is None:
            config_file_path = (
                Path(__file__).parent.parent.parent
                / "config"
                / "regime_parameters.json"
            )
        else:
            config_file_path = Path(config_path)

        try:
            with open(config_file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file loading fails."""
        return {
            "regime_detection": {
                "volatility_thresholds": {
                    "low_volatility": 0.005,
                    "high_volatility": 0.015,
                },
                "trend_parameters": {
                    "trend_strength_threshold": 0.7,
                    "ranging_threshold": 0.3,
                },
                "regime_confirmation": {
                    "min_regime_duration_hours": 24,
                    "stability_threshold": 0.8,
                },
            }
        }

    async def detect_current_regime(
        self, currency_pairs: List[str], timeframe: str = "4H"
    ) -> RegimeDetectionResult:
        """
        Detect the current market regime.

        Args:
            currency_pairs: List of currency pairs to analyze
            timeframe: Primary timeframe for analysis

        Returns:
            RegimeDetectionResult with current regime classification
        """
        try:
            logger.info(f"Starting regime detection for {len(currency_pairs)} pairs")

            # Get market data for analysis
            market_data = await self._gather_market_data(currency_pairs, timeframe)

            # Run parallel analysis
            analysis_tasks = [
                self.market_classifier.classify_market_condition(market_data),
                self.volatility_analyzer.analyze_volatility_regime(market_data),
                self.trend_analyzer.analyze_trend_strength(market_data),
                self.sentiment_analyzer.analyze_risk_sentiment(market_data),
                self.economic_analyzer.analyze_event_impact(market_data),
            ]

            results = await asyncio.gather(*analysis_tasks)
            (
                market_condition,
                volatility_info,
                trend_info,
                sentiment_info,
                event_impact,
            ) = results

            # Synthesize regime classification
            regime_result = self._synthesize_regime(
                market_condition,
                volatility_info,
                trend_info,
                sentiment_info,
                event_impact,
            )

            # Update regime tracking
            self._update_regime_tracking(regime_result)

            logger.info(f"Regime detection completed: {regime_result.regime}")
            return regime_result

        except Exception as e:
            logger.error(f"Error in regime detection: {e}")
            return self._create_uncertain_regime_result()

    async def _gather_market_data(
        self, currency_pairs: List[str], timeframe: str
    ) -> Dict[str, Any]:
        """Gather market data from data infrastructure."""
        try:
            # Get recent data for analysis (last 200 periods for sufficient history)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=800)  # ~200 4H periods

            market_data = {}
            for pair in currency_pairs:
                candles = await self.data_infrastructure.get_candles(
                    pair, timeframe, start_time, end_time
                )
                market_data[pair] = candles

            market_data["timestamp"] = end_time
            market_data["timeframe"] = timeframe

            return market_data

        except Exception as e:
            logger.error(f"Error gathering market data: {e}")
            return {}

    def _synthesize_regime(
        self,
        market_condition: Dict[str, Any],
        volatility_info: Dict[str, Any],
        trend_info: Dict[str, Any],
        sentiment_info: Dict[str, Any],
        event_impact: Dict[str, Any],
    ) -> RegimeDetectionResult:
        """Synthesize individual analysis results into regime classification."""

        # Determine base regime from market condition and volatility
        is_trending = market_condition.get("is_trending", False)
        volatility_level = volatility_info.get("regime", "normal")

        if is_trending:
            if volatility_level in ["high", "extreme"]:
                base_regime = MarketRegime.TRENDING_HIGH_VOL
            else:
                base_regime = MarketRegime.TRENDING_LOW_VOL
        else:
            if volatility_level in ["high", "extreme"]:
                base_regime = MarketRegime.RANGING_HIGH_VOL
            else:
                base_regime = MarketRegime.RANGING_LOW_VOL

        # Check for transition conditions
        trend_strength = trend_info.get("strength", 0.5)
        if 0.3 <= trend_strength <= 0.7:
            base_regime = MarketRegime.TRANSITION

        # Determine sentiment
        sentiment_score = sentiment_info.get("risk_sentiment_score", 0.5)
        if sentiment_score > 0.6:
            sentiment = RiskSentiment.RISK_ON
        elif sentiment_score < 0.4:
            sentiment = RiskSentiment.RISK_OFF
        else:
            sentiment = RiskSentiment.NEUTRAL

        # Calculate confidence
        confidence = self._calculate_confidence(
            market_condition, volatility_info, trend_info, sentiment_info
        )

        # Compile contributing factors
        factors = []
        if is_trending:
            factors.append(f"trending_market (strength: {trend_strength:.2f})")
        else:
            factors.append("ranging_market")

        factors.append(f"volatility_{volatility_level}")
        factors.append(f"sentiment_{sentiment.value}")

        if event_impact.get("high_impact_events", 0) > 0:
            factors.append("economic_events")

        # Calculate regime duration
        regime_duration = 0.0
        if self.regime_start_time:
            regime_duration = (
                datetime.now() - self.regime_start_time
            ).total_seconds() / 3600

        return RegimeDetectionResult(
            timestamp=datetime.now(),
            regime=base_regime,
            sentiment=sentiment,
            confidence=confidence,
            volatility_level=volatility_level,
            trend_strength=trend_strength,
            regime_duration_hours=regime_duration,
            contributing_factors=factors,
            next_evaluation=datetime.now() + timedelta(hours=4),
        )

    def _calculate_confidence(
        self,
        market_condition: Dict[str, Any],
        volatility_info: Dict[str, Any],
        trend_info: Dict[str, Any],
        sentiment_info: Dict[str, Any],
    ) -> float:
        """Calculate confidence in regime classification."""

        # Base confidence from trend strength
        trend_confidence = abs(trend_info.get("strength", 0.5) - 0.5) * 2

        # Volatility confidence (higher for clear high/low vol)
        vol_confidence = volatility_info.get("confidence", 0.5)

        # Market condition confidence
        market_confidence = market_condition.get("confidence", 0.5)

        # Sentiment confidence
        sentiment_confidence = (
            abs(sentiment_info.get("risk_sentiment_score", 0.5) - 0.5) * 2
        )

        # Weighted average
        confidence = (
            trend_confidence * 0.3
            + vol_confidence * 0.25
            + market_confidence * 0.25
            + sentiment_confidence * 0.2
        )

        return min(max(confidence, 0.0), 1.0)

    def _update_regime_tracking(self, regime_result: RegimeDetectionResult):
        """Update regime tracking and history."""
        if self.current_regime != regime_result.regime:
            logger.info(
                f"Regime change detected: {self.current_regime} -> {regime_result.regime}"
            )
            self.current_regime = regime_result.regime
            self.regime_start_time = regime_result.timestamp

        # Add to history (keep last 100 results)
        self.regime_history.append(regime_result)
        if len(self.regime_history) > 100:
            self.regime_history.pop(0)

    def _create_uncertain_regime_result(self) -> RegimeDetectionResult:
        """Create result for uncertain/error conditions."""
        return RegimeDetectionResult(
            timestamp=datetime.now(),
            regime=MarketRegime.UNCERTAIN,
            sentiment=RiskSentiment.NEUTRAL,
            confidence=0.0,
            volatility_level="unknown",
            trend_strength=0.5,
            regime_duration_hours=0.0,
            contributing_factors=["error_in_analysis"],
            next_evaluation=datetime.now() + timedelta(hours=1),
        )

    def get_regime_history(self, hours_back: int = 168) -> List[RegimeDetectionResult]:
        """Get regime history for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        return [r for r in self.regime_history if r.timestamp >= cutoff_time]

    def get_current_regime_info(self) -> Optional[RegimeDetectionResult]:
        """Get the most recent regime detection result."""
        return self.regime_history[-1] if self.regime_history else None
