"""
Fallback implementation for correlation trends API endpoints
Provides mock data when the full correlation system is unavailable
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import random
import math

logger = logging.getLogger(__name__)

# Mock currency pairs for demo
DEMO_PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/GBP",
    "EUR/JPY",
    "GBP/JPY",
]


def generate_mock_correlation_trends(hours_back: int = 168) -> Dict[str, Any]:
    """
    Generate realistic mock correlation trends data
    """
    trends = []
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    # Generate hourly data points
    for hour in range(0, hours_back, 6):  # Every 6 hours
        timestamp = start_time + timedelta(hours=hour)

        for pair in DEMO_PAIRS[:4]:  # Limit to 4 pairs for demo
            # Create trending correlation with some noise
            base_correlation = 0.3 + 0.4 * math.sin(hour / 24)  # Daily cycle
            noise = random.uniform(-0.1, 0.1)
            correlation = max(-1, min(1, base_correlation + noise))

            # Determine trend direction
            if hour > 6:
                prev_hour = hour - 6
                prev_correlation = (
                    0.3 + 0.4 * math.sin(prev_hour / 24) + random.uniform(-0.05, 0.05)
                )
                if correlation > prev_correlation + 0.02:
                    trend_direction = "increasing"
                elif correlation < prev_correlation - 0.02:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "stable"

            trends.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "pair": pair,
                    "correlation": round(correlation, 4),
                    "trend_direction": trend_direction,
                    "confidence": round(random.uniform(0.7, 0.95), 3),
                    "predicted_correlation": round(
                        correlation + random.uniform(-0.05, 0.05), 4
                    ),
                    "upper_bound": round(correlation + 0.1, 4),
                    "lower_bound": round(correlation - 0.1, 4),
                    "breach_probability": round(
                        max(0, abs(correlation) - 0.3) / 0.7, 3
                    ),
                }
            )

    return {
        "trends": trends,
        "total_points": len(trends),
        "time_range": {
            "start": start_time.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
        },
        "status": "success_mock",
    }


def generate_mock_correlation_forecast() -> Dict[str, Any]:
    """
    Generate mock correlation forecast data
    """
    forecasts = []

    for pair in DEMO_PAIRS[:4]:
        current_correlation = round(random.uniform(-0.8, 0.8), 4)

        # Generate prediction points
        predicted_values = []
        for hours_ahead in [6, 12, 24, 48]:
            trend_factor = random.uniform(-0.1, 0.1)
            predicted_value = current_correlation + trend_factor * (hours_ahead / 24)
            predicted_value = max(-1, min(1, predicted_value))

            predicted_values.append(
                {
                    "timestamp": (
                        datetime.now(timezone.utc) + timedelta(hours=hours_ahead)
                    ).isoformat(),
                    "value": round(predicted_value, 4),
                    "confidence_lower": round(predicted_value - 0.1, 4),
                    "confidence_upper": round(predicted_value + 0.1, 4),
                }
            )

        forecasts.append(
            {
                "pair": pair,
                "current_correlation": current_correlation,
                "predicted_values": predicted_values,
                "breach_probability": round(
                    max(0, abs(current_correlation) - 0.3) / 0.7, 3
                ),
                "trend_strength": round(random.uniform(0.1, 0.9), 3),
            }
        )

    return {
        "forecasts": forecasts,
        "prediction_horizon_hours": 48,
        "model_accuracy": 0.78,
        "status": "success_mock",
    }


def generate_mock_market_regime() -> Dict[str, Any]:
    """
    Generate mock market regime data
    """
    regimes = ["low_volatility", "normal", "high_volatility", "crisis"]
    current_regime = random.choice(regimes[:3])  # Avoid crisis for demo

    return {
        "current_regime": {
            "regime": current_regime,
            "start_time": (
                datetime.now(timezone.utc) - timedelta(hours=random.randint(6, 72))
            ).isoformat(),
            "characteristics": {
                "avg_correlation": round(random.uniform(0.2, 0.7), 3),
                "volatility_level": round(random.uniform(0.1, 0.8), 3),
            },
        },
        "regime_probability": round(random.uniform(0.7, 0.95), 3),
        "recent_changes": [],
        "status": "success_mock",
    }
