"""
Correlation Trend Analysis - Advanced Analytics Module
Extends the existing CorrelationManager with trend analysis and prediction capabilities

This module implements:
- Historical correlation pattern analysis
- Predictive correlation modeling
- Market regime correlation adjustments
- Trend-based alert generation
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio


# Simple linear regression implementation to avoid sklearn dependency
def simple_linear_regression(
    X: np.ndarray, y: np.ndarray
) -> Tuple[float, float, float]:
    """
    Simple linear regression implementation
    Returns: (slope, intercept, r_squared)
    """
    n = len(X)
    if n < 2:
        return 0.0, 0.0, 0.0

    x_mean = float(np.mean(X))
    y_mean = float(np.mean(y))

    numerator = float(np.sum((X - x_mean) * (y - y_mean)))
    denominator = float(np.sum((X - x_mean) ** 2))

    if denominator == 0:
        return 0.0, y_mean, 0.0

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    # Calculate R-squared
    y_pred = slope * X + intercept
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y_mean) ** 2))

    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return float(slope), float(intercept), float(r_squared)


logger = logging.getLogger(__name__)


@dataclass
class CorrelationTrend:
    """Data class for correlation trend analysis"""

    pair1: str
    pair2: str
    current_correlation: float
    trend_slope: float  # Linear regression slope
    trend_direction: str  # "increasing", "decreasing", "stable"
    volatility: float  # Correlation volatility
    prediction_1d: float  # 1-day forecast
    prediction_3d: float  # 3-day forecast
    breach_probability: float  # Probability of exceeding 0.35 threshold
    confidence_interval: Tuple[float, float]  # 95% confidence interval
    r_squared: float  # Trend fit quality
    timestamp: datetime


@dataclass
class MarketRegime:
    """Market regime analysis for correlation expectations"""

    regime_type: str  # "normal", "stress", "volatility_spike"
    expected_correlation_range: Tuple[float, float]
    regime_confidence: float
    regime_start: datetime
    characteristics: Dict[str, Any]


class CorrelationTrendAnalyzer:
    """
    Advanced correlation trend analysis and prediction system
    Extends CorrelationManager with sophisticated analytics
    """

    def __init__(self, correlation_manager=None, lookback_days: int = 90):
        """
        Initialize trend analyzer

        Args:
            correlation_manager: Reference to main CorrelationManager
            lookback_days: Days of history for trend analysis
        """
        self.correlation_manager = correlation_manager
        self.lookback_days = lookback_days
        self.trend_cache = {}
        self.regime_cache = {}
        self.prediction_accuracy = {}

        # Thresholds
        self.breach_threshold = 0.35  # Early warning threshold
        self.critical_threshold = 0.4  # Breach threshold
        self.stability_threshold = 0.05  # Volatility threshold for "stable"

        logger.info(
            f"CorrelationTrendAnalyzer initialized with {lookback_days}-day lookback"
        )

    async def calculate_correlation_trends(
        self, lookback_days: Optional[int] = None
    ) -> Dict[str, CorrelationTrend]:
        """
        Calculate correlation trends for all currency pairs

        Args:
            lookback_days: Override default lookback period

        Returns:
            Dictionary of pair-wise correlation trends
        """
        try:
            days = lookback_days or self.lookback_days
            trends = {}

            if (
                not self.correlation_manager
                or not self.correlation_manager.correlation_history
            ):
                logger.warning("No correlation history available for trend analysis")
                return {}

            # Get historical correlation data
            history = self.correlation_manager.correlation_history

            # Extract time series for each pair combination
            pair_series = self._extract_pair_time_series(history, days)

            # Calculate trends for each pair
            for pair_key, correlation_series in pair_series.items():
                if len(correlation_series) < 10:  # Need minimum data points
                    continue

                trend = await self._calculate_single_pair_trend(
                    pair_key, correlation_series
                )
                if trend:
                    trends[pair_key] = trend

            logger.info(f"Calculated trends for {len(trends)} correlation pairs")
            return trends

        except Exception as e:
            logger.error(f"Error calculating correlation trends: {e}")
            return {}

    def _extract_pair_time_series(
        self, history: Dict, days: int
    ) -> Dict[str, pd.Series]:
        """
        Extract time series data for each currency pair combination

        Args:
            history: Correlation history from CorrelationManager
            days: Number of days to extract

        Returns:
            Dictionary of time series for each pair combination
        """
        try:
            # Sort history by timestamp
            sorted_timestamps = sorted(history.keys())

            # Limit to requested days
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_timestamps = [
                ts
                for ts in sorted_timestamps
                if datetime.fromisoformat(ts) >= cutoff_date
            ]

            pair_series = {}

            for timestamp in recent_timestamps:
                correlation_matrix = history[timestamp].get("correlation_matrix", {})

                # Extract all pair combinations
                for pair1, pair1_correlations in correlation_matrix.items():
                    for pair2, correlation in pair1_correlations.items():
                        if pair1 != pair2:
                            # Create consistent pair key (alphabetical order)
                            pair_key = f"{min(pair1, pair2)}_{max(pair1, pair2)}"

                            if pair_key not in pair_series:
                                pair_series[pair_key] = []

                            pair_series[pair_key].append(
                                {
                                    "timestamp": datetime.fromisoformat(timestamp),
                                    "correlation": abs(float(correlation)),
                                }
                            )

            # Convert to pandas Series
            for pair_key, data_points in pair_series.items():
                if len(data_points) > 0:
                    df = pd.DataFrame(data_points)
                    df.set_index("timestamp", inplace=True)
                    pair_series[pair_key] = df["correlation"].sort_index()

            return pair_series

        except Exception as e:
            logger.error(f"Error extracting pair time series: {e}")
            return {}

    async def _calculate_single_pair_trend(
        self, pair_key: str, correlation_series: pd.Series
    ) -> Optional[CorrelationTrend]:
        """
        Calculate trend analysis for a single currency pair combination

        Args:
            pair_key: Pair identifier (e.g., "EUR_USD_GBP_USD")
            correlation_series: Time series of correlation values

        Returns:
            CorrelationTrend object with analysis results
        """
        try:
            if len(correlation_series) < 5:
                return None

            # Prepare data for linear regression
            timestamps = correlation_series.index
            correlations = np.array(correlation_series.values, dtype=float)

            # Convert timestamps to numeric for regression
            timestamp_numeric = np.array(
                [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]
            )

            # Fit linear regression using our simple implementation
            slope, intercept, r_squared = simple_linear_regression(
                timestamp_numeric, correlations
            )

            # Calculate trend metrics
            # Determine trend direction
            if abs(slope) < 0.001:  # Very small slope
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"

            # Calculate correlation volatility
            volatility = float(correlation_series.std())

            # Make predictions
            last_timestamp_numeric = timestamp_numeric[-1]
            prediction_1d = slope * (last_timestamp_numeric + 1) + intercept
            prediction_3d = slope * (last_timestamp_numeric + 3) + intercept

            # Calculate breach probability
            breach_prob = self._calculate_breach_probability(
                correlations, slope, volatility
            )

            # Calculate confidence interval (simplified)
            y_pred = slope * timestamp_numeric + intercept
            residuals = correlations - y_pred
            mse = float(np.mean(residuals**2))
            std_error = float(np.sqrt(mse))
            confidence_interval = (
                float(correlations[-1]) - 1.96 * std_error,
                float(correlations[-1]) + 1.96 * std_error,
            )

            # Parse pair names
            pair_names = pair_key.split("_")
            if len(pair_names) >= 4:
                pair1 = f"{pair_names[0]}_{pair_names[1]}"
                pair2 = f"{pair_names[2]}_{pair_names[3]}"
            else:
                pair1, pair2 = pair_key.split("_")[:2]

            trend = CorrelationTrend(
                pair1=pair1,
                pair2=pair2,
                current_correlation=float(correlations[-1]),
                trend_slope=slope,
                trend_direction=trend_direction,
                volatility=volatility,
                prediction_1d=max(0.0, min(1.0, prediction_1d)),  # Clamp to [0,1]
                prediction_3d=max(0.0, min(1.0, prediction_3d)),  # Clamp to [0,1]
                breach_probability=breach_prob,
                confidence_interval=confidence_interval,
                r_squared=r_squared,
                timestamp=datetime.now(),
            )

            return trend

        except Exception as e:
            logger.error(f"Error calculating trend for {pair_key}: {e}")
            return None

    def _calculate_breach_probability(
        self, correlations: np.ndarray, slope: float, volatility: float
    ) -> float:
        """
        Calculate probability of correlation breaching 0.35 threshold

        Args:
            correlations: Historical correlation values
            slope: Trend slope
            volatility: Correlation volatility

        Returns:
            Probability of breach (0-1)
        """
        try:
            current_corr = correlations[-1]

            # If already above threshold
            if current_corr >= self.breach_threshold:
                return 1.0

            # If trend is decreasing significantly
            if slope < -0.005:
                return 0.1

            # Calculate days to reach threshold at current slope
            if slope > 0:
                days_to_breach = (self.breach_threshold - current_corr) / slope
                if days_to_breach <= 3:
                    return 0.8
                elif days_to_breach <= 7:
                    return 0.5
                else:
                    return 0.2

            # Factor in volatility for stable/decreasing trends
            if volatility > 0.1:  # High volatility
                return 0.3
            else:
                return 0.1

        except Exception as e:
            logger.error(f"Error calculating breach probability: {e}")
            return 0.0

    async def predict_correlation_movement(
        self, pair: str, forecast_days: int = 3
    ) -> Dict[str, Any]:
        """
        Predict correlation movement for a specific pair

        Args:
            pair: Currency pair identifier
            forecast_days: Number of days to forecast

        Returns:
            Prediction results dictionary
        """
        try:
            # Find matching trend data
            trends = await self.calculate_correlation_trends()

            matching_trends = []
            for trend_key, trend in trends.items():
                if pair in trend_key:
                    matching_trends.append(trend)

            if not matching_trends:
                return {
                    "pair": pair,
                    "forecast_days": forecast_days,
                    "predictions": [],
                    "error": "No trend data available for this pair",
                }

            predictions = []
            for trend in matching_trends:
                other_pair = trend.pair2 if trend.pair1 == pair else trend.pair1

                prediction = {
                    "with_pair": other_pair,
                    "current_correlation": trend.current_correlation,
                    "predicted_correlation": (
                        trend.prediction_3d
                        if forecast_days >= 3
                        else trend.prediction_1d
                    ),
                    "trend_direction": trend.trend_direction,
                    "breach_probability": trend.breach_probability,
                    "confidence": trend.r_squared,
                }
                predictions.append(prediction)

            return {
                "pair": pair,
                "forecast_days": forecast_days,
                "predictions": predictions,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error predicting correlation movement for {pair}: {e}")
            return {"error": str(e)}

    async def detect_regime_shifts(self) -> Dict[str, MarketRegime]:
        """
        Detect market regime changes affecting correlation patterns

        Returns:
            Dictionary of detected market regimes
        """
        try:
            regimes = {}

            if (
                not self.correlation_manager
                or not self.correlation_manager.correlation_history
            ):
                return {}

            history = self.correlation_manager.correlation_history

            # Analyze recent correlation patterns
            recent_data = self._get_recent_correlation_metrics(history, days=30)

            if len(recent_data) < 10:
                return {}

            # Calculate regime indicators
            avg_max_corr = np.mean([d["max_correlation"] for d in recent_data])
            avg_avg_corr = np.mean([d["avg_correlation"] for d in recent_data])
            corr_volatility = np.std([d["max_correlation"] for d in recent_data])

            # Determine regime type
            if avg_max_corr > 0.6:
                regime_type = "stress"
                expected_range = (0.4, 0.8)
                confidence = 0.8
            elif corr_volatility > 0.15:
                regime_type = "volatility_spike"
                expected_range = (0.2, 0.6)
                confidence = 0.7
            else:
                regime_type = "normal"
                expected_range = (0.1, 0.4)
                confidence = 0.9

            regime = MarketRegime(
                regime_type=regime_type,
                expected_correlation_range=expected_range,
                regime_confidence=confidence,
                regime_start=datetime.now() - timedelta(days=7),  # Simplified
                characteristics={
                    "avg_max_correlation": avg_max_corr,
                    "avg_correlation": avg_avg_corr,
                    "correlation_volatility": corr_volatility,
                },
            )

            regimes["current"] = regime

            logger.info(
                f"Detected market regime: {regime_type} (confidence: {confidence:.2f})"
            )
            return regimes

        except Exception as e:
            logger.error(f"Error detecting regime shifts: {e}")
            return {}

    def _get_recent_correlation_metrics(self, history: Dict, days: int) -> List[Dict]:
        """
        Get recent correlation metrics for regime analysis

        Args:
            history: Correlation history
            days: Number of recent days to analyze

        Returns:
            List of recent correlation metrics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_data = []

            for timestamp, metrics in history.items():
                if datetime.fromisoformat(timestamp) >= cutoff_date:
                    recent_data.append(metrics)

            return sorted(recent_data, key=lambda x: x.get("timestamp", ""))

        except Exception as e:
            logger.error(f"Error getting recent correlation metrics: {e}")
            return []

    async def generate_trend_alerts(self) -> List[Dict[str, Any]]:
        """
        Generate alerts based on correlation trend analysis

        Returns:
            List of trend-based alerts
        """
        try:
            trends = await self.calculate_correlation_trends()
            alerts = []

            for trend_key, trend in trends.items():
                # High breach probability alert
                if trend.breach_probability > 0.7:
                    alerts.append(
                        {
                            "type": "breach_warning",
                            "severity": "high",
                            "pair1": trend.pair1,
                            "pair2": trend.pair2,
                            "current_correlation": trend.current_correlation,
                            "breach_probability": trend.breach_probability,
                            "message": f"High correlation breach risk: {trend.pair1}-{trend.pair2} ({trend.current_correlation:.3f})",
                            "recommendation": "Consider position size reduction",
                            "timestamp": trend.timestamp.isoformat(),
                        }
                    )

                # Rapid correlation increase alert
                if trend.trend_direction == "increasing" and trend.trend_slope > 0.01:
                    alerts.append(
                        {
                            "type": "rapid_increase",
                            "severity": "medium",
                            "pair1": trend.pair1,
                            "pair2": trend.pair2,
                            "trend_slope": trend.trend_slope,
                            "message": f"Rapid correlation increase: {trend.pair1}-{trend.pair2}",
                            "recommendation": "Monitor closely for potential breach",
                            "timestamp": trend.timestamp.isoformat(),
                        }
                    )

                # Low confidence trend alert
                if trend.r_squared < 0.3 and trend.volatility > 0.15:
                    alerts.append(
                        {
                            "type": "unstable_correlation",
                            "severity": "low",
                            "pair1": trend.pair1,
                            "pair2": trend.pair2,
                            "volatility": trend.volatility,
                            "r_squared": trend.r_squared,
                            "message": f"Unstable correlation pattern: {trend.pair1}-{trend.pair2}",
                            "recommendation": "Increase monitoring frequency",
                            "timestamp": trend.timestamp.isoformat(),
                        }
                    )

            logger.info(f"Generated {len(alerts)} trend-based alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error generating trend alerts: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":

    async def test_correlation_trends():
        """Test correlation trend analysis functionality"""
        analyzer = CorrelationTrendAnalyzer()

        # Test trend calculations (would need real correlation manager)
        print("Testing Correlation Trend Analysis...")

        trends = await analyzer.calculate_correlation_trends()
        print(f"Calculated trends: {len(trends)}")

        regimes = await analyzer.detect_regime_shifts()
        print(f"Detected regimes: {regimes}")

        alerts = await analyzer.generate_trend_alerts()
        print(f"Generated alerts: {len(alerts)}")

    # Run test
    asyncio.run(test_correlation_trends())
