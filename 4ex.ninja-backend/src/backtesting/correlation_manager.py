"""
Correlation Manager for Portfolio Risk Analysis.

This module provides correlation analysis capabilities for managing
portfolio-level risk across multiple currency pairs and strategies.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CorrelationManager:
    """
    Manages correlation analysis for portfolio risk management.

    Provides real-time correlation tracking and risk assessment
    for multiple currency pairs and strategies.
    """

    def __init__(self, lookback_days: int = 30):
        """
        Initialize correlation manager.

        Args:
            lookback_days: Number of days to use for correlation calculation
        """
        self.lookback_days = lookback_days
        self.correlation_cache: Dict[str, Dict[str, float]] = {}
        self.last_update: Optional[datetime] = None
        self.correlation_threshold_high = 0.7  # High correlation threshold
        self.correlation_threshold_medium = 0.5  # Medium correlation threshold

        logger.info(
            f"Correlation manager initialized with {lookback_days} day lookback"
        )

    def calculate_pair_correlations(
        self, price_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for all currency pairs.

        Args:
            price_data: Dictionary of pair -> price DataFrame

        Returns:
            Correlation matrix as nested dictionary
        """
        pairs = list(price_data.keys())
        correlation_matrix = {}

        # Align all data to same timeframe
        aligned_data = self._align_price_data(price_data)

        for pair1 in pairs:
            correlation_matrix[pair1] = {}
            for pair2 in pairs:
                if pair1 == pair2:
                    correlation_matrix[pair1][pair2] = 1.0
                else:
                    corr = self._calculate_correlation(
                        aligned_data[pair1]["close"], aligned_data[pair2]["close"]
                    )
                    correlation_matrix[pair1][pair2] = corr

        self.correlation_cache = correlation_matrix
        self.last_update = datetime.now()

        return correlation_matrix

    def assess_correlation_risk(
        self, target_pair: str, active_pairs: List[str]
    ) -> Dict[str, Any]:
        """
        Assess correlation risk for a target pair against active positions.

        Args:
            target_pair: Currency pair to assess
            active_pairs: List of pairs with active positions

        Returns:
            Risk assessment dictionary
        """
        if not self.correlation_cache:
            return {
                "risk_level": "unknown",
                "max_correlation": 0.0,
                "correlated_pairs": [],
                "recommendation": "insufficient_data",
            }

        if target_pair not in self.correlation_cache:
            return {
                "risk_level": "unknown",
                "max_correlation": 0.0,
                "correlated_pairs": [],
                "recommendation": "pair_not_found",
            }

        correlations = []
        correlated_pairs = []

        for active_pair in active_pairs:
            if active_pair in self.correlation_cache[target_pair]:
                corr = abs(self.correlation_cache[target_pair][active_pair])
                correlations.append(corr)

                if corr > self.correlation_threshold_medium:
                    correlated_pairs.append({"pair": active_pair, "correlation": corr})

        max_correlation = max(correlations) if correlations else 0.0

        # Determine risk level
        if max_correlation > self.correlation_threshold_high:
            risk_level = "high"
            recommendation = "reduce_exposure"
        elif max_correlation > self.correlation_threshold_medium:
            risk_level = "medium"
            recommendation = "monitor_closely"
        else:
            risk_level = "low"
            recommendation = "proceed"

        return {
            "risk_level": risk_level,
            "max_correlation": max_correlation,
            "correlated_pairs": correlated_pairs,
            "recommendation": recommendation,
            "correlation_count": len(correlated_pairs),
        }

    def get_currency_exposure(
        self, active_pairs: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate exposure by individual currency.

        Args:
            active_pairs: List of active currency pairs

        Returns:
            Currency exposure analysis
        """
        currency_exposure = {}

        for pair in active_pairs:
            if len(pair) == 6:  # Standard format like EURUSD
                base_currency = pair[:3]
                quote_currency = pair[3:]

                # Track base currency exposure
                if base_currency not in currency_exposure:
                    currency_exposure[base_currency] = {
                        "pairs": [],
                        "long_exposure": 0,
                        "short_exposure": 0,
                        "net_exposure": 0,
                    }
                currency_exposure[base_currency]["pairs"].append(pair)
                currency_exposure[base_currency]["long_exposure"] += 1

                # Track quote currency exposure
                if quote_currency not in currency_exposure:
                    currency_exposure[quote_currency] = {
                        "pairs": [],
                        "long_exposure": 0,
                        "short_exposure": 0,
                        "net_exposure": 0,
                    }
                currency_exposure[quote_currency]["pairs"].append(pair)
                currency_exposure[quote_currency]["short_exposure"] += 1

        # Calculate net exposure
        for currency, data in currency_exposure.items():
            data["net_exposure"] = data["long_exposure"] - data["short_exposure"]

        return currency_exposure

    def check_currency_concentration_risk(
        self, active_pairs: List[str]
    ) -> Dict[str, Any]:
        """
        Check for currency concentration risk.

        Args:
            active_pairs: List of active currency pairs

        Returns:
            Concentration risk assessment
        """
        currency_exposure = self.get_currency_exposure(active_pairs)

        max_exposure = 0
        max_currency = None
        risk_currencies = []

        for currency, data in currency_exposure.items():
            total_exposure = abs(data["long_exposure"]) + abs(data["short_exposure"])

            if total_exposure > max_exposure:
                max_exposure = total_exposure
                max_currency = currency

            # Flag currencies with high exposure
            if total_exposure > 3:  # More than 3 positions involving this currency
                risk_currencies.append(
                    {
                        "currency": currency,
                        "exposure": total_exposure,
                        "net_exposure": data["net_exposure"],
                        "pairs": data["pairs"],
                    }
                )

        # Determine risk level
        if max_exposure > 4:
            risk_level = "high"
            recommendation = "reduce_currency_exposure"
        elif max_exposure > 2:
            risk_level = "medium"
            recommendation = "monitor_concentration"
        else:
            risk_level = "low"
            recommendation = "acceptable"

        return {
            "risk_level": risk_level,
            "max_exposure": max_exposure,
            "max_currency": max_currency,
            "risk_currencies": risk_currencies,
            "recommendation": recommendation,
            "total_currencies": len(currency_exposure),
        }

    def suggest_diversification_pairs(
        self, active_pairs: List[str], available_pairs: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Suggest pairs for better diversification.

        Args:
            active_pairs: Currently active pairs
            available_pairs: All available pairs for trading

        Returns:
            List of suggested pairs with reasons
        """
        if not self.correlation_cache:
            return []

        suggestions = []

        for candidate_pair in available_pairs:
            if candidate_pair in active_pairs:
                continue

            if candidate_pair not in self.correlation_cache:
                continue

            # Calculate average correlation with active pairs
            correlations = []
            for active_pair in active_pairs:
                if active_pair in self.correlation_cache[candidate_pair]:
                    correlations.append(
                        abs(self.correlation_cache[candidate_pair][active_pair])
                    )

            if correlations:
                avg_correlation = sum(correlations) / len(correlations)
                max_correlation = max(correlations)

                # Suggest pairs with low correlation
                if avg_correlation < 0.3 and max_correlation < 0.5:
                    suggestions.append(
                        {
                            "pair": candidate_pair,
                            "avg_correlation": avg_correlation,
                            "max_correlation": max_correlation,
                            "diversification_score": 1.0 - avg_correlation,
                            "reason": "Low correlation with active pairs",
                        }
                    )

        # Sort by diversification score (lower correlation = better)
        suggestions.sort(key=lambda x: x["diversification_score"], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions

    def _align_price_data(
        self, price_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Align price data to common timeframe."""
        if not price_data:
            return {}

        # Find common date range
        all_dates = []
        for df in price_data.values():
            if "timestamp" in df.columns:
                all_dates.extend(df["timestamp"].tolist())
            elif df.index.name == "timestamp" or isinstance(df.index, pd.DatetimeIndex):
                all_dates.extend(df.index.tolist())

        if not all_dates:
            return price_data

        # Get last N days of data
        latest_date = max(all_dates)
        start_date = latest_date - timedelta(days=self.lookback_days)

        aligned_data = {}
        for pair, df in price_data.items():
            try:
                if "timestamp" in df.columns:
                    mask = (df["timestamp"] >= start_date) & (
                        df["timestamp"] <= latest_date
                    )
                    aligned_data[pair] = df[mask].copy()
                else:
                    mask = (df.index >= start_date) & (df.index <= latest_date)
                    aligned_data[pair] = df[mask].copy()
            except Exception as e:
                logger.warning(f"Failed to align data for {pair}: {e}")
                aligned_data[pair] = df.copy()

        return aligned_data

    def _calculate_correlation(self, series1: pd.Series, series2: pd.Series) -> float:
        """Calculate correlation between two price series."""
        try:
            # Calculate returns
            returns1 = series1.pct_change().dropna()
            returns2 = series2.pct_change().dropna()

            # Align series
            aligned_returns = pd.concat([returns1, returns2], axis=1, join="inner")

            if len(aligned_returns) < 10:  # Need minimum data points
                return 0.0

            correlation = aligned_returns.iloc[:, 0].corr(aligned_returns.iloc[:, 1])

            return correlation if not pd.isna(correlation) else 0.0

        except Exception as e:
            logger.warning(f"Failed to calculate correlation: {e}")
            return 0.0

    def get_correlation_summary(self) -> Dict[str, Any]:
        """Get summary of current correlation state."""
        if not self.correlation_cache:
            return {"status": "no_data", "last_update": None, "pairs_analyzed": 0}

        pairs = list(self.correlation_cache.keys())
        total_pairs = len(pairs)

        # Calculate statistics
        all_correlations = []
        high_correlations = 0

        for pair1 in pairs:
            for pair2 in pairs:
                if pair1 != pair2:
                    corr = abs(self.correlation_cache[pair1][pair2])
                    all_correlations.append(corr)
                    if corr > self.correlation_threshold_high:
                        high_correlations += 1

        avg_correlation = np.mean(all_correlations) if all_correlations else 0.0
        max_correlation = max(all_correlations) if all_correlations else 0.0

        return {
            "status": "active",
            "last_update": self.last_update,
            "pairs_analyzed": total_pairs,
            "avg_correlation": avg_correlation,
            "max_correlation": max_correlation,
            "high_correlations": high_correlations,
            "lookback_days": self.lookback_days,
        }
