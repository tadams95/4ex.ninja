"""
Economic Event Analyzer for market regime detection.

This module analyzes the impact of economic events on market behavior
to support regime classification and trading decisions.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_providers.base_provider import SwingCandleData

logger = logging.getLogger(__name__)


@dataclass
class EconomicEventImpact:
    """Economic event impact analysis result."""

    high_impact_events: int
    volatility_spike_detected: bool
    event_impact_score: float  # 0.0 to 1.0
    affected_currencies: List[str]
    market_reaction_strength: float
    confidence: float


class EconomicEventAnalyzer:
    """
    Analyzes economic event impact on currency markets.

    Detects volatility spikes and unusual market behavior that may be
    attributed to economic events or news releases.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration parameters."""
        self.config = config.get("regime_detection", {})
        self.event_config = self.config.get("economic_events", {})

        # Major currencies to monitor
        self.major_currencies = self.event_config.get(
            "high_impact_currencies",
            ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"],
        )

        # Event detection parameters
        self.volatility_spike_threshold = self.event_config.get(
            "volatility_spike_threshold", 2.0
        )
        self.event_window_hours = self.event_config.get("event_impact_window_hours", 4)

        logger.info("EconomicEventAnalyzer initialized")

    async def analyze_event_impact(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze economic event impact on currency pairs.

        Args:
            market_data: Dictionary containing price data for multiple pairs

        Returns:
            Dictionary with economic event impact analysis
        """
        try:
            if not market_data:
                return self._get_default_event_analysis()

            # Analyze volatility spikes across pairs
            volatility_analysis = self._analyze_volatility_spikes(market_data)

            # Detect synchronized movements (indicating major events)
            synchronized_movements = self._detect_synchronized_movements(market_data)

            # Analyze currency-specific impacts
            currency_impacts = self._analyze_currency_impacts(market_data)

            # Synthesize event impact assessment
            event_impact = self._synthesize_event_impact(
                volatility_analysis, synchronized_movements, currency_impacts
            )

            logger.debug("Economic event impact analysis completed")
            return event_impact

        except Exception as e:
            logger.error(f"Error in economic event analysis: {e}")
            return self._get_default_event_analysis()

    def _analyze_volatility_spikes(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze volatility spikes that may indicate economic events."""

        spike_data = {
            "pairs_with_spikes": [],
            "spike_count": 0,
            "max_spike_magnitude": 0.0,
            "average_spike_magnitude": 0.0,
        }

        spike_magnitudes = []

        for pair, candles in market_data.items():
            if pair in ["timestamp", "timeframe"] or not candles or len(candles) < 20:
                continue

            # Calculate volatility spike for this pair
            spike_magnitude = self._calculate_volatility_spike(pair, candles)

            if spike_magnitude > self.volatility_spike_threshold:
                spike_data["pairs_with_spikes"].append(
                    {"pair": pair, "magnitude": spike_magnitude}
                )
                spike_magnitudes.append(spike_magnitude)

        if spike_magnitudes:
            spike_data["spike_count"] = len(spike_magnitudes)
            spike_data["max_spike_magnitude"] = float(np.max(spike_magnitudes))
            spike_data["average_spike_magnitude"] = float(np.mean(spike_magnitudes))

        return spike_data

    def _calculate_volatility_spike(
        self, pair: str, candles: List[SwingCandleData]
    ) -> float:
        """Calculate volatility spike magnitude for a currency pair."""

        if len(candles) < 20:
            return 0.0

        # Calculate returns
        prices = np.array([float(candle.close) for candle in candles])
        returns = np.diff(np.log(prices))

        if len(returns) < 10:
            return 0.0

        # Current volatility (last 5 periods)
        recent_vol = np.std(returns[-5:]) if len(returns) >= 5 else 0.0

        # Baseline volatility (previous 15 periods, excluding last 5)
        if len(returns) >= 20:
            baseline_vol = np.std(returns[-20:-5])
        else:
            baseline_vol = np.std(returns[:-5]) if len(returns) > 5 else 0.01

        # Calculate spike magnitude
        if baseline_vol > 0:
            spike_magnitude = float(recent_vol / baseline_vol)
        else:
            spike_magnitude = 0.0

        return spike_magnitude

    def _detect_synchronized_movements(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect synchronized movements across currency pairs."""

        sync_data = {
            "synchronized_pairs": [],
            "synchronization_score": 0.0,
            "movement_direction": "mixed",
        }

        # Extract recent price movements
        pair_movements = {}

        for pair, candles in market_data.items():
            if pair in ["timestamp", "timeframe"] or not candles or len(candles) < 5:
                continue

            prices = np.array([float(candle.close) for candle in candles])

            if len(prices) >= 5:
                # Calculate recent movement (last 3 periods)
                recent_change = (prices[-1] / prices[-4] - 1) * 100  # Percentage change
                pair_movements[pair] = recent_change

        if len(pair_movements) < 3:
            return sync_data

        # Analyze synchronization
        movements = list(pair_movements.values())

        # Calculate how many pairs moved in the same direction
        positive_moves = sum(1 for m in movements if m > 0.1)
        negative_moves = sum(1 for m in movements if m < -0.1)
        total_significant_moves = positive_moves + negative_moves

        if total_significant_moves > 0:
            # Synchronization score based on how many pairs moved in same direction
            max_directional = max(positive_moves, negative_moves)
            sync_data["synchronization_score"] = max_directional / len(movements)

            # Determine dominant direction
            if positive_moves > negative_moves * 1.5:
                sync_data["movement_direction"] = "up"
            elif negative_moves > positive_moves * 1.5:
                sync_data["movement_direction"] = "down"
            else:
                sync_data["movement_direction"] = "mixed"

            # Identify synchronized pairs
            if sync_data["synchronization_score"] > 0.6:
                dominant_direction = positive_moves > negative_moves
                for pair, movement in pair_movements.items():
                    if (movement > 0.1) == dominant_direction:
                        sync_data["synchronized_pairs"].append(
                            {"pair": pair, "movement": movement}
                        )

        return sync_data

    def _analyze_currency_impacts(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze impact on individual currencies."""

        currency_impacts = {}

        # Extract currency performance from pair data
        currency_performance = {currency: [] for currency in self.major_currencies}

        for pair, candles in market_data.items():
            if pair in ["timestamp", "timeframe"] or not candles or len(candles) < 5:
                continue

            # Extract base and quote currencies from pair name
            if len(pair) == 6:
                base_currency = pair[:3]
                quote_currency = pair[3:]

                if (
                    base_currency in self.major_currencies
                    or quote_currency in self.major_currencies
                ):
                    prices = np.array([float(candle.close) for candle in candles])

                    if len(prices) >= 5:
                        # Calculate recent performance
                        performance = (prices[-1] / prices[-5] - 1) * 100

                        # For base currency, positive performance means strength
                        if base_currency in self.major_currencies:
                            currency_performance[base_currency].append(performance)

                        # For quote currency, negative performance means strength
                        if quote_currency in self.major_currencies:
                            currency_performance[quote_currency].append(-performance)

        # Calculate aggregate currency performance
        for currency in self.major_currencies:
            if currency_performance[currency]:
                performances = currency_performance[currency]
                avg_performance = np.mean(performances)
                performance_volatility = (
                    np.std(performances) if len(performances) > 1 else 0.0
                )

                currency_impacts[currency] = {
                    "performance": float(avg_performance),
                    "volatility": float(performance_volatility),
                    "pair_count": len(performances),
                    "impact_score": min(
                        float(abs(avg_performance)) / 2.0, 1.0
                    ),  # Normalize to 0-1
                }
            else:
                currency_impacts[currency] = {
                    "performance": 0.0,
                    "volatility": 0.0,
                    "pair_count": 0,
                    "impact_score": 0.0,
                }

        return currency_impacts

    def _synthesize_event_impact(
        self,
        volatility_analysis: Dict[str, Any],
        synchronized_movements: Dict[str, Any],
        currency_impacts: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesize overall economic event impact assessment."""

        # Count high impact indicators
        high_impact_events = 0

        # Volatility spikes indicate possible events
        if volatility_analysis["spike_count"] > 0:
            high_impact_events += volatility_analysis["spike_count"]

        # Synchronized movements indicate market-wide events
        if synchronized_movements["synchronization_score"] > 0.6:
            high_impact_events += 1

        # Check for significant currency impacts
        affected_currencies = []
        for currency, impact in currency_impacts.items():
            if impact["impact_score"] > 0.5:
                affected_currencies.append(currency)

        if len(affected_currencies) > 2:
            high_impact_events += 1

        # Calculate overall event impact score
        volatility_component = min(
            volatility_analysis["average_spike_magnitude"] / 3.0, 1.0
        )
        synchronization_component = synchronized_movements["synchronization_score"]
        currency_impact_component = len(affected_currencies) / len(
            self.major_currencies
        )

        event_impact_score = (
            volatility_component * 0.4
            + synchronization_component * 0.3
            + currency_impact_component * 0.3
        )

        # Detect volatility spike
        volatility_spike_detected = (
            volatility_analysis["max_spike_magnitude"] > self.volatility_spike_threshold
        )

        # Calculate market reaction strength
        market_reaction_strength = max(
            volatility_analysis["max_spike_magnitude"] / 5.0,
            synchronized_movements["synchronization_score"],
        )
        market_reaction_strength = min(market_reaction_strength, 1.0)

        # Calculate confidence
        confidence = self._calculate_event_confidence(
            volatility_analysis, synchronized_movements, len(affected_currencies)
        )

        return {
            "high_impact_events": high_impact_events,
            "volatility_spike_detected": volatility_spike_detected,
            "event_impact_score": event_impact_score,
            "affected_currencies": affected_currencies,
            "market_reaction_strength": market_reaction_strength,
            "confidence": confidence,
            "detailed_analysis": {
                "volatility_spikes": volatility_analysis,
                "synchronized_movements": synchronized_movements,
                "currency_impacts": currency_impacts,
            },
        }

    def _calculate_event_confidence(
        self,
        volatility_analysis: Dict[str, Any],
        synchronized_movements: Dict[str, Any],
        affected_currency_count: int,
    ) -> float:
        """Calculate confidence in event impact assessment."""

        # Higher confidence with multiple confirming indicators
        indicators = 0

        if volatility_analysis["spike_count"] > 0:
            indicators += 1

        if synchronized_movements["synchronization_score"] > 0.5:
            indicators += 1

        if affected_currency_count > 1:
            indicators += 1

        # Base confidence on number of confirming indicators
        base_confidence = indicators / 3.0

        # Adjust for signal strength
        signal_strength = max(
            volatility_analysis["max_spike_magnitude"] / 5.0,
            synchronized_movements["synchronization_score"],
        )

        confidence = base_confidence * 0.7 + min(signal_strength, 1.0) * 0.3

        return min(max(confidence, 0.0), 1.0)

    def _get_default_event_analysis(self) -> Dict[str, Any]:
        """Return default event analysis for error cases."""
        return {
            "high_impact_events": 0,
            "volatility_spike_detected": False,
            "event_impact_score": 0.0,
            "affected_currencies": [],
            "market_reaction_strength": 0.0,
            "confidence": 0.0,
            "detailed_analysis": {
                "volatility_spikes": {
                    "pairs_with_spikes": [],
                    "spike_count": 0,
                    "max_spike_magnitude": 0.0,
                    "average_spike_magnitude": 0.0,
                },
                "synchronized_movements": {
                    "synchronized_pairs": [],
                    "synchronization_score": 0.0,
                    "movement_direction": "mixed",
                },
                "currency_impacts": {},
            },
        }
