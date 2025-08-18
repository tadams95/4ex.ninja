"""
Portfolio Correlation Manager - Real-time correlation monitoring for Phase 2
Target: Maintain cross-pair correlation <0.4

This module implements sophisticated correlation calculation and management:
- Real-time correlation matrix calculation
- Correlation breach detection and alerts
- Position adjustment recommendations
- Dynamic correlation-based rebalancing
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from itertools import combinations

try:
    from ..backtesting.portfolio_manager import PortfolioState
    from .emergency_risk_manager import EmergencyRiskManager
except ImportError:
    # Local development fallback
    try:
        from backtesting.portfolio_manager import PortfolioState
        from risk.emergency_risk_manager import EmergencyRiskManager
    except ImportError:
        # Final fallback for production deployment
        from src.backtesting.portfolio_manager import PortfolioState
        from src.risk.emergency_risk_manager import EmergencyRiskManager

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CorrelationAlert:
    """Data class for correlation alerts"""

    pair1: str
    pair2: str
    correlation: float
    threshold: float
    timestamp: datetime
    severity: str
    recommendation: str

    def to_dict(self) -> Dict:
        return {
            "pair1": self.pair1,
            "pair2": self.pair2,
            "correlation": self.correlation,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "recommendation": self.recommendation,
        }


@dataclass
class PositionAdjustment:
    """Position adjustment recommendation"""

    currency_pair: str
    current_size: float
    recommended_size: float
    adjustment_ratio: float
    reason: str
    priority: str

    def to_dict(self) -> Dict:
        return {
            "currency_pair": self.currency_pair,
            "current_size": self.current_size,
            "recommended_size": self.recommended_size,
            "adjustment_ratio": self.adjustment_ratio,
            "reason": self.reason,
            "priority": self.priority,
        }


class CorrelationManager:
    """
    Real-time portfolio correlation monitoring and management
    Target: Maintain cross-pair correlation <0.4
    """

    def __init__(
        self,
        correlation_threshold: float = 0.4,
        emergency_manager: Optional[EmergencyRiskManager] = None,
    ):
        """
        Initialize Correlation Manager

        Args:
            correlation_threshold: Maximum allowed correlation between pairs
            emergency_manager: Emergency risk manager for severe correlation events
        """
        self.correlation_threshold = correlation_threshold
        self.correlation_window = 60  # 60-day rolling correlation
        self.rebalance_threshold = 0.35  # Trigger at 0.35 to prevent breach
        self.severe_correlation_threshold = 0.6  # Severe correlation level

        # Dependencies
        self.emergency_manager = emergency_manager

        # Correlation tracking
        self.correlation_history = {}
        self.last_correlation_matrix = pd.DataFrame()
        self.correlation_alerts = []
        self.breach_count = 0

        logger.info(
            f"CorrelationManager initialized with {correlation_threshold} threshold"
        )

    def _safe_correlation_value(self, value) -> float:
        """
        Safely convert correlation value to float

        Args:
            value: Correlation value from pandas DataFrame

        Returns:
            Float correlation value between 0 and 1
        """
        try:
            if pd.isna(value):
                return 0.0
            # Convert to float and take absolute value
            correlation = float(value)
            return abs(correlation)
        except (TypeError, ValueError):
            logger.warning(f"Could not convert correlation value {value} to float")
            return 0.0

    def _safe_float_conversion(self, value) -> float:
        """
        Safely convert pandas Series/value to float

        Args:
            value: Value to convert

        Returns:
            Float value
        """
        try:
            if hasattr(value, "iloc"):
                # It's a Series, get the first value
                return float(value.iloc[0]) if len(value) > 0 else 0.0
            else:
                return float(value) if not pd.isna(value) else 0.0
        except (TypeError, ValueError, IndexError):
            return 0.0

    def _safe_int_conversion(self, value) -> int:
        """
        Safely convert pandas Series/value to int

        Args:
            value: Value to convert

        Returns:
            Integer value
        """
        try:
            if hasattr(value, "iloc"):
                # It's a Series, get the first value
                return int(value.iloc[0]) if len(value) > 0 else 0
            else:
                return int(value) if not pd.isna(value) else 0
        except (TypeError, ValueError, IndexError):
            return 0

    async def calculate_correlation_matrix(
        self, portfolio_state: PortfolioState
    ) -> pd.DataFrame:
        """
        Calculate real-time correlation matrix for active positions

        Args:
            portfolio_state: Current portfolio state

        Returns:
            Correlation matrix as pandas DataFrame
        """
        try:
            # Get active currency pairs
            active_pairs = list(portfolio_state.active_positions.keys())

            if len(active_pairs) < 2:
                logger.info(
                    "Less than 2 active pairs - no correlation calculation needed"
                )
                return pd.DataFrame()

            # Get price histories for all pairs
            price_data = {}
            for pair in active_pairs:
                price_history = await self._get_price_history(pair)
                if (
                    price_history is not None
                    and len(price_history) >= self.correlation_window
                ):
                    # Calculate returns for correlation
                    returns = price_history.pct_change().dropna()
                    if len(returns) >= 30:  # Minimum for meaningful correlation
                        price_data[pair] = returns.tail(self.correlation_window)

            if len(price_data) < 2:
                logger.warning("Insufficient price data for correlation calculation")
                return pd.DataFrame()

            # Create returns dataframe
            returns_df = pd.DataFrame(price_data)

            # Calculate correlation matrix
            correlation_matrix = returns_df.corr()

            # Store for trend analysis
            self.last_correlation_matrix = correlation_matrix
            self._store_correlation_history(correlation_matrix)

            logger.info(f"Correlation matrix calculated for {len(active_pairs)} pairs")
            return correlation_matrix

        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()

    async def monitor_correlation_drift(
        self, correlation_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Monitor correlation changes over time

        Args:
            correlation_matrix: Current correlation matrix

        Returns:
            Dictionary of correlation drift metrics
        """
        try:
            drift_metrics = {
                "max_correlation": 0.0,
                "avg_correlation": 0.0,
                "high_correlation_pairs": 0,
                "breach_pairs": 0,
                "drift_trend": "stable",
            }

            if correlation_matrix.empty:
                return drift_metrics

            # Get upper triangle of correlation matrix (exclude diagonal)
            upper_triangle = correlation_matrix.where(
                np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
            )

            # Calculate metrics
            correlations = upper_triangle.stack().abs().dropna()
            if len(correlations) > 0:
                try:
                    max_corr = correlations.max()
                    avg_corr = correlations.mean()
                    high_pairs = (correlations > self.rebalance_threshold).sum()
                    breach_pairs = (correlations > self.correlation_threshold).sum()

                    drift_metrics["max_correlation"] = max_corr
                    drift_metrics["avg_correlation"] = avg_corr
                    drift_metrics["high_correlation_pairs"] = high_pairs
                    drift_metrics["breach_pairs"] = breach_pairs
                except Exception as e:
                    logger.warning(f"Error calculating correlation metrics: {e}")
                    # Set defaults
                    drift_metrics["max_correlation"] = 0.0
                    drift_metrics["avg_correlation"] = 0.0
                    drift_metrics["high_correlation_pairs"] = 0
                    drift_metrics["breach_pairs"] = 0

            # Analyze trend if we have historical data
            if len(self.correlation_history) >= 3:
                recent_max_corr = [
                    data["max_correlation"]
                    for data in list(self.correlation_history.values())[-3:]
                ]
                if len(recent_max_corr) == 3:
                    if recent_max_corr[-1] > recent_max_corr[-2] > recent_max_corr[-3]:
                        drift_metrics["drift_trend"] = "increasing"
                    elif (
                        recent_max_corr[-1] < recent_max_corr[-2] < recent_max_corr[-3]
                    ):
                        drift_metrics["drift_trend"] = "decreasing"
                    else:
                        drift_metrics["drift_trend"] = "stable"

            logger.debug(f"Correlation drift metrics: {drift_metrics}")
            return drift_metrics

        except Exception as e:
            logger.error(f"Error monitoring correlation drift: {e}")
            return {}

    async def detect_correlation_breaches(
        self, correlation_matrix: pd.DataFrame
    ) -> List[CorrelationAlert]:
        """
        Detect correlation threshold breaches

        Args:
            correlation_matrix: Current correlation matrix

        Returns:
            List of correlation alerts
        """
        alerts = []

        try:
            if correlation_matrix.empty:
                return alerts

            # Check all pair combinations for breaches
            pairs = correlation_matrix.columns.tolist()

            for pair1, pair2 in combinations(pairs, 2):
                correlation_value = correlation_matrix.loc[pair1, pair2]
                # Use safe conversion helper
                correlation = self._safe_correlation_value(correlation_value)

                # Determine alert severity
                if correlation > self.severe_correlation_threshold:
                    severity = "CRITICAL"
                    recommendation = (
                        f"Immediately reduce position sizes for {pair1} and {pair2}"
                    )
                elif correlation > self.correlation_threshold:
                    severity = "HIGH"
                    recommendation = f"Consider reducing exposure to {pair1} or {pair2}"
                elif correlation > self.rebalance_threshold:
                    severity = "MEDIUM"
                    recommendation = f"Monitor {pair1}-{pair2} correlation closely"
                else:
                    continue  # No alert needed

                alert = CorrelationAlert(
                    pair1=pair1,
                    pair2=pair2,
                    correlation=correlation,
                    threshold=self.correlation_threshold,
                    timestamp=datetime.now(),
                    severity=severity,
                    recommendation=recommendation,
                )

                alerts.append(alert)
                self.correlation_alerts.append(alert)

                # Track breach count
                if correlation > self.correlation_threshold:
                    self.breach_count += 1
                    logger.warning(
                        f"Correlation breach: {pair1}-{pair2} = {correlation:.3f}"
                    )

            return alerts

        except Exception as e:
            logger.error(f"Error detecting correlation breaches: {e}")
            return []

    async def suggest_position_adjustments(
        self, portfolio_state: PortfolioState, correlation_matrix: pd.DataFrame
    ) -> List[PositionAdjustment]:
        """
        Recommend position changes to reduce correlation

        Args:
            portfolio_state: Current portfolio state
            correlation_matrix: Current correlation matrix

        Returns:
            List of position adjustment recommendations
        """
        adjustments = []

        try:
            if correlation_matrix.empty or len(portfolio_state.active_positions) < 2:
                return adjustments

            # Identify high correlation pairs
            high_corr_pairs = []
            pairs = correlation_matrix.columns.tolist()

            for pair1, pair2 in combinations(pairs, 2):
                correlation_value = correlation_matrix.loc[pair1, pair2]
                correlation = self._safe_correlation_value(correlation_value)
                if correlation > self.rebalance_threshold:
                    high_corr_pairs.append((pair1, pair2, correlation))

            # Sort by correlation strength (highest first)
            high_corr_pairs.sort(key=lambda x: x[2], reverse=True)

            # Generate adjustment recommendations
            adjustment_made = set()

            for pair1, pair2, correlation in high_corr_pairs:
                if pair1 in adjustment_made or pair2 in adjustment_made:
                    continue  # Already adjusted one of these pairs

                # Get current position sizes
                pos1 = portfolio_state.active_positions.get(pair1)
                pos2 = portfolio_state.active_positions.get(pair2)

                if not pos1 or not pos2:
                    continue

                size1 = getattr(pos1, "position_size", 0)
                size2 = getattr(pos2, "position_size", 0)

                # Determine which position to adjust (prefer larger position)
                if abs(size1) >= abs(size2):
                    target_pair, other_pair = pair1, pair2
                    current_size = size1
                else:
                    target_pair, other_pair = pair2, pair1
                    current_size = size2

                # Calculate adjustment based on correlation level
                if correlation > self.severe_correlation_threshold:
                    # Severe correlation - reduce by 50%
                    adjustment_ratio = 0.5
                    priority = "CRITICAL"
                    reason = f"Severe correlation with {other_pair} ({correlation:.3f})"
                elif correlation > self.correlation_threshold:
                    # Breach - reduce by 30%
                    adjustment_ratio = 0.7
                    priority = "HIGH"
                    reason = f"Correlation breach with {other_pair} ({correlation:.3f})"
                else:
                    # Early warning - reduce by 15%
                    adjustment_ratio = 0.85
                    priority = "MEDIUM"
                    reason = f"High correlation with {other_pair} ({correlation:.3f})"

                recommended_size = current_size * adjustment_ratio

                adjustment = PositionAdjustment(
                    currency_pair=target_pair,
                    current_size=current_size,
                    recommended_size=recommended_size,
                    adjustment_ratio=adjustment_ratio,
                    reason=reason,
                    priority=priority,
                )

                adjustments.append(adjustment)
                adjustment_made.add(target_pair)

                logger.info(
                    f"Position adjustment suggested for {target_pair}: "
                    f"{current_size:.2f} -> {recommended_size:.2f}"
                )

            return adjustments

        except Exception as e:
            logger.error(f"Error suggesting position adjustments: {e}")
            return []

    async def apply_emergency_correlation_protocol(
        self, correlation_matrix: pd.DataFrame
    ) -> bool:
        """
        Apply emergency correlation management protocols

        Args:
            correlation_matrix: Current correlation matrix

        Returns:
            True if emergency protocols were triggered
        """
        try:
            if correlation_matrix.empty:
                return False

            # Check for emergency conditions
            pairs = correlation_matrix.columns.tolist()
            emergency_triggered = False

            # Count severe correlations
            severe_correlations = 0
            for pair1, pair2 in combinations(pairs, 2):
                correlation_value = correlation_matrix.loc[pair1, pair2]
                correlation = self._safe_correlation_value(correlation_value)
                if correlation > self.severe_correlation_threshold:
                    severe_correlations += 1

            # Trigger emergency if multiple severe correlations
            if severe_correlations >= 2:
                logger.critical(
                    f"EMERGENCY: {severe_correlations} severe correlations detected"
                )

                if self.emergency_manager:
                    # Log emergency correlation event
                    logger.error(
                        "SEVERE CORRELATION EMERGENCY - Multiple pairs highly correlated"
                    )

                emergency_triggered = True

            # Check for systematic correlation increase
            elif len(self.correlation_history) >= 5:
                recent_max_correlations = [
                    data["max_correlation"]
                    for data in list(self.correlation_history.values())[-5:]
                ]

                # If correlation has been increasing consistently
                if all(
                    recent_max_correlations[i] < recent_max_correlations[i + 1]
                    for i in range(len(recent_max_correlations) - 1)
                ):
                    if recent_max_correlations[-1] > self.correlation_threshold:
                        logger.warning(
                            "CORRELATION TREND ALERT: Systematic correlation increase"
                        )
                        emergency_triggered = True

            return emergency_triggered

        except Exception as e:
            logger.error(f"Error in emergency correlation protocol: {e}")
            return False

    async def _get_price_history(self, currency_pair: str) -> Optional[pd.Series]:
        """Get price history for currency pair (mock implementation for Phase 2)"""
        try:
            # For Phase 2 initial implementation, we'll use mock data
            # This will be replaced with actual data integration
            dates = pd.date_range(
                end=datetime.now(), periods=self.correlation_window + 50, freq="D"
            )

            # Generate realistic forex price movements with different correlations
            np.random.seed(hash(currency_pair) % 2**32)

            # Base price movements
            if "EUR" in currency_pair:
                base_factor = 1.0
            elif "GBP" in currency_pair:
                base_factor = 0.8  # Somewhat correlated with EUR
            elif "JPY" in currency_pair:
                base_factor = -0.3  # Often negatively correlated
            else:
                base_factor = 0.2  # Low correlation

            # Generate correlated returns
            base_returns = np.random.normal(0, 0.01, len(dates))
            pair_specific = np.random.normal(0, 0.008, len(dates))
            returns = (
                base_factor * base_returns + (1 - abs(base_factor)) * pair_specific
            )

            # Generate prices
            initial_price = 1.1000 if "EUR" in currency_pair else 1.2500
            prices = [initial_price]

            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))

            return pd.Series(prices, index=dates)

        except Exception as e:
            logger.error(f"Error getting price history for {currency_pair}: {e}")
            return None

    def _store_correlation_history(self, correlation_matrix: pd.DataFrame):
        """Store correlation matrix for trend analysis"""
        try:
            timestamp = datetime.now().isoformat()

            # Calculate summary metrics
            upper_triangle = correlation_matrix.where(
                np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
            )
            correlations = upper_triangle.stack().abs()

            if len(correlations) > 0:
                summary = {
                    "max_correlation": self._safe_float_conversion(correlations.max()),
                    "avg_correlation": self._safe_float_conversion(correlations.mean()),
                    "correlation_matrix": correlation_matrix.to_dict(),
                    "pair_count": len(correlation_matrix.columns),
                }

                self.correlation_history[timestamp] = summary

                # Keep only last 100 entries
                if len(self.correlation_history) > 100:
                    oldest_key = min(self.correlation_history.keys())
                    del self.correlation_history[oldest_key]

        except Exception as e:
            logger.error(f"Error storing correlation history: {e}")

    def get_correlation_summary(self) -> Dict:
        """Get current correlation summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "correlation_threshold": self.correlation_threshold,
            "rebalance_threshold": self.rebalance_threshold,
            "breach_count": self.breach_count,
            "recent_alerts": len(
                [
                    a
                    for a in self.correlation_alerts
                    if (datetime.now() - a.timestamp).days < 1
                ]
            ),
            "correlation_window": self.correlation_window,
        }

        if not self.last_correlation_matrix.empty:
            upper_triangle = self.last_correlation_matrix.where(
                np.triu(np.ones_like(self.last_correlation_matrix, dtype=bool), k=1)
            )
            correlations = upper_triangle.stack().abs()

            if len(correlations) > 0:
                summary.update(
                    {
                        "current_max_correlation": self._safe_float_conversion(
                            correlations.max()
                        ),
                        "current_avg_correlation": self._safe_float_conversion(
                            correlations.mean()
                        ),
                        "high_correlation_pairs": self._safe_int_conversion(
                            (correlations > self.rebalance_threshold).sum()
                        ),
                        "breach_pairs": self._safe_int_conversion(
                            (correlations > self.correlation_threshold).sum()
                        ),
                    }
                )

        return summary


# Example usage and testing
if __name__ == "__main__":

    async def test_correlation_manager():
        """Test correlation monitoring functionality"""
        print("Testing Correlation Manager...")

        # Initialize manager
        correlation_manager = CorrelationManager(correlation_threshold=0.4)

        # Create mock portfolio state
        from ..backtesting.position_manager import Position

        positions = {
            "EUR_USD": Position(
                position_id="test_001",
                pair="EUR_USD",
                direction="BUY",
                entry_price=1.1000,
                position_size=1000.0,
                stop_loss=1.0950,
                take_profit=1.1100,
                entry_time=datetime.now(),
                strategy_name="test_strategy",
            ),
            "GBP_USD": Position(
                position_id="test_002",
                pair="GBP_USD",
                direction="BUY",
                entry_price=1.2500,
                position_size=800.0,
                stop_loss=1.2400,
                take_profit=1.2600,
                entry_time=datetime.now(),
                strategy_name="test_strategy",
            ),
        }

        portfolio_state = PortfolioState(
            total_balance=100000.0,
            available_balance=90000.0,
            total_risk=0.02,
            active_positions=positions,
            strategy_allocations={},
        )

        # Calculate correlation matrix
        correlation_matrix = await correlation_manager.calculate_correlation_matrix(
            portfolio_state
        )
        print(f"Correlation Matrix:\n{correlation_matrix}")

        # Monitor drift
        drift_metrics = await correlation_manager.monitor_correlation_drift(
            correlation_matrix
        )
        print(f"Drift Metrics: {drift_metrics}")

        # Detect breaches
        alerts = await correlation_manager.detect_correlation_breaches(
            correlation_matrix
        )
        print(f"Correlation Alerts: {len(alerts)}")
        for alert in alerts:
            print(
                f"  - {alert.pair1}-{alert.pair2}: {alert.correlation:.3f} ({alert.severity})"
            )

        # Suggest adjustments
        adjustments = await correlation_manager.suggest_position_adjustments(
            portfolio_state, correlation_matrix
        )
        print(f"Position Adjustments: {len(adjustments)}")
        for adj in adjustments:
            print(
                f"  - {adj.currency_pair}: {adj.current_size:.0f} -> {adj.recommended_size:.0f}"
            )

        # Get summary
        summary = correlation_manager.get_correlation_summary()
        print(f"Correlation Summary: {summary}")

    # Run test
    asyncio.run(test_correlation_manager())
