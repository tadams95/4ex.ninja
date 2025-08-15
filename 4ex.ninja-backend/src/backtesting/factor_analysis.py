"""
Factor Analysis Engine for Swing Trading Performance Attribution.

This module analyzes the contribution of various market factors to strategy
performance, enabling factor-based optimization for forex swing trading.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FactorAnalyzer:
    """
    Analyzes factor attribution for swing trading strategy performance.

    Provides insights into how different market factors contribute to
    strategy returns and risk.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the factor analyzer."""
        self.config = config or self._get_default_config()
        logger.info("FactorAnalyzer initialized successfully")

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "factor_analysis": {
                "lookback_periods": 252,  # 1 year
                "correlation_threshold": 0.3,
                "factor_significance_threshold": 0.05,
                "attribution_window_days": 30,
            },
            "factors": {
                "currency_factors": [
                    "EUR",
                    "USD",
                    "GBP",
                    "JPY",
                    "CHF",
                    "AUD",
                    "CAD",
                    "NZD",
                ],
                "style_factors": ["carry", "momentum", "value", "volatility"],
                "macro_factors": [
                    "interest_rate_differential",
                    "inflation_differential",
                    "gdp_growth_differential",
                    "risk_sentiment",
                ],
            },
        }

    async def analyze_factor_attribution(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Analyze factor attribution for strategy performance.

        Args:
            strategy_results: DataFrame with strategy trades and returns
            market_data: Dictionary of market data by currency pair

        Returns:
            Dictionary of factor attributions
        """
        try:
            logger.info("Starting factor attribution analysis")

            if strategy_results.empty:
                return {}

            # Calculate strategy returns
            strategy_returns = self._calculate_strategy_returns(strategy_results)

            # Extract factor exposures
            factor_exposures = await self._extract_factor_exposures(
                strategy_results, market_data
            )

            # Calculate factor attributions
            factor_attributions = self._calculate_factor_attributions(
                strategy_returns, factor_exposures
            )

            logger.info(
                f"Factor attribution analysis completed for {len(factor_attributions)} factors"
            )
            return factor_attributions

        except Exception as e:
            logger.error(f"Error in factor attribution analysis: {e}")
            return {}

    def _calculate_strategy_returns(self, strategy_results: pd.DataFrame) -> pd.Series:
        """Calculate time series of strategy returns."""
        try:
            if "pnl_pct" in strategy_results.columns:
                returns = strategy_results.set_index("timestamp")["pnl_pct"]
            elif (
                "pnl" in strategy_results.columns
                and "account_balance" in strategy_results.columns
            ):
                # Calculate percentage returns from PnL
                returns = strategy_results["pnl"] / strategy_results["account_balance"]
                returns = returns.fillna(0)
                # Create a new Series with the correct index instead of assigning to .index
                returns = pd.Series(returns.values, index=strategy_results["timestamp"])
            else:
                logger.warning(
                    "Unable to calculate strategy returns - missing required columns"
                )
                return pd.Series(dtype=float)

            return returns.fillna(0)

        except Exception as e:
            logger.error(f"Error calculating strategy returns: {e}")
            return pd.Series(dtype=float)

    async def _extract_factor_exposures(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.Series]:
        """Extract factor exposures from market data and strategy positions."""
        try:
            factor_exposures = {}

            # Currency pair exposures
            currency_exposures = self._calculate_currency_exposures(strategy_results)
            factor_exposures.update(currency_exposures)

            # Style factor exposures
            style_exposures = await self._calculate_style_factor_exposures(
                strategy_results, market_data
            )
            factor_exposures.update(style_exposures)

            # Macro factor exposures
            macro_exposures = await self._calculate_macro_factor_exposures(
                strategy_results, market_data
            )
            factor_exposures.update(macro_exposures)

            return factor_exposures

        except Exception as e:
            logger.error(f"Error extracting factor exposures: {e}")
            return {}

    def _calculate_currency_exposures(
        self, strategy_results: pd.DataFrame
    ) -> Dict[str, pd.Series]:
        """Calculate exposure to individual currencies."""
        try:
            currency_exposures = {}

            if "currency_pair" not in strategy_results.columns:
                return currency_exposures

            # Initialize currency exposure series
            currencies = self.config["factors"]["currency_factors"]
            for currency in currencies:
                currency_exposures[f"{currency}_exposure"] = pd.Series(
                    0.0, index=strategy_results["timestamp"]
                )

            # Calculate exposures based on trades
            for _, trade in strategy_results.iterrows():
                pair = trade["currency_pair"]
                timestamp = trade["timestamp"]
                position_size = trade.get("position_size", 0)

                if len(pair) >= 6:  # Standard currency pair format
                    base_currency = pair[:3]
                    quote_currency = pair[3:6]

                    # Long position: long base currency, short quote currency
                    # Short position: short base currency, long quote currency
                    direction = 1 if position_size > 0 else -1

                    if f"{base_currency}_exposure" in currency_exposures:
                        currency_exposures[f"{base_currency}_exposure"].loc[
                            timestamp
                        ] += direction * abs(position_size)

                    if f"{quote_currency}_exposure" in currency_exposures:
                        currency_exposures[f"{quote_currency}_exposure"].loc[
                            timestamp
                        ] -= direction * abs(position_size)

            return currency_exposures

        except Exception as e:
            logger.error(f"Error calculating currency exposures: {e}")
            return {}

    async def _calculate_style_factor_exposures(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.Series]:
        """Calculate exposure to style factors (carry, momentum, value, volatility)."""
        try:
            style_exposures = {}

            # Initialize style factor series
            timestamps = (
                strategy_results["timestamp"]
                if not strategy_results.empty
                else pd.Series(dtype="datetime64[ns]")
            )

            style_exposures["carry_exposure"] = pd.Series(0.0, index=timestamps)
            style_exposures["momentum_exposure"] = pd.Series(0.0, index=timestamps)
            style_exposures["value_exposure"] = pd.Series(0.0, index=timestamps)
            style_exposures["volatility_exposure"] = pd.Series(0.0, index=timestamps)

            # Calculate style factor exposures for each trade
            for _, trade in strategy_results.iterrows():
                pair = trade["currency_pair"]
                timestamp = trade["timestamp"]
                position_size = trade.get("position_size", 0)

                if pair in market_data and not market_data[pair].empty:
                    # Get market data around trade time
                    pair_data = market_data[pair]

                    # Find closest data point
                    if "timestamp" in pair_data.columns:
                        time_diffs = abs(pair_data["timestamp"] - timestamp)
                        closest_idx = time_diffs.idxmin()

                        # Calculate style factors
                        style_factors = self._calculate_style_factors(
                            pair_data, closest_idx
                        )

                        # Apply position size weighting
                        for factor, value in style_factors.items():
                            if f"{factor}_exposure" in style_exposures:
                                style_exposures[f"{factor}_exposure"].loc[
                                    timestamp
                                ] += value * abs(position_size)

            return style_exposures

        except Exception as e:
            logger.error(f"Error calculating style factor exposures: {e}")
            return {}

    def _calculate_style_factors(
        self, pair_data: pd.DataFrame, idx: int
    ) -> Dict[str, float]:
        """Calculate style factor values for a specific time point."""
        try:
            factors = {}

            if "close" not in pair_data.columns:
                return factors

            # Momentum factor (price change over lookback period)
            lookback = min(20, idx)
            if lookback > 0:
                current_price = pair_data["close"].iloc[idx]
                past_price = pair_data["close"].iloc[idx - lookback]
                momentum = (
                    (current_price - past_price) / past_price if past_price != 0 else 0
                )
                factors["momentum"] = float(momentum)
            else:
                factors["momentum"] = 0.0

            # Volatility factor (realized volatility)
            vol_window = min(20, idx)
            if vol_window > 1:
                returns = (
                    pair_data["close"]
                    .iloc[idx - vol_window + 1 : idx + 1]
                    .pct_change()
                    .dropna()
                )
                if not returns.empty:
                    volatility = float(returns.std())
                    factors["volatility"] = volatility
                else:
                    factors["volatility"] = 0.0
            else:
                factors["volatility"] = 0.0

            # Carry factor (simplified - would need interest rate data in production)
            # For now, use a proxy based on currency pair characteristics
            factors["carry"] = 0.0  # Placeholder

            # Value factor (simplified - would need fundamental data in production)
            # For now, use relative price position
            if "high" in pair_data.columns and "low" in pair_data.columns:
                high_52w = pair_data["high"].iloc[max(0, idx - 252) : idx + 1].max()
                low_52w = pair_data["low"].iloc[max(0, idx - 252) : idx + 1].min()
                current_price = pair_data["close"].iloc[idx]

                if high_52w != low_52w:
                    price_position = (current_price - low_52w) / (high_52w - low_52w)
                    factors["value"] = float(
                        1 - price_position
                    )  # Inverse of price position
                else:
                    factors["value"] = 0.0
            else:
                factors["value"] = 0.0

            return factors

        except Exception as e:
            logger.error(f"Error calculating style factors: {e}")
            return {}

    async def _calculate_macro_factor_exposures(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.Series]:
        """Calculate exposure to macro factors."""
        try:
            macro_exposures = {}

            # Initialize macro factor series
            timestamps = (
                strategy_results["timestamp"]
                if not strategy_results.empty
                else pd.Series(dtype="datetime64[ns]")
            )

            macro_exposures["interest_rate_differential_exposure"] = pd.Series(
                0.0, index=timestamps
            )
            macro_exposures["risk_sentiment_exposure"] = pd.Series(
                0.0, index=timestamps
            )

            # Calculate macro exposures (simplified implementation)
            for _, trade in strategy_results.iterrows():
                timestamp = trade["timestamp"]
                position_size = trade.get("position_size", 0)

                # Risk sentiment exposure (proxy using overall market volatility)
                risk_sentiment = self._calculate_risk_sentiment_proxy(
                    market_data, timestamp
                )
                macro_exposures["risk_sentiment_exposure"].loc[
                    timestamp
                ] += risk_sentiment * abs(position_size)

                # Interest rate differential (placeholder - would need economic data)
                macro_exposures["interest_rate_differential_exposure"].loc[
                    timestamp
                ] += 0.0

            return macro_exposures

        except Exception as e:
            logger.error(f"Error calculating macro factor exposures: {e}")
            return {}

    def _calculate_risk_sentiment_proxy(
        self, market_data: Dict[str, pd.DataFrame], timestamp: datetime
    ) -> float:
        """Calculate risk sentiment proxy from market data."""
        try:
            # Use average volatility across major pairs as risk sentiment proxy
            volatilities = []

            major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"]

            for pair in major_pairs:
                if pair in market_data and not market_data[pair].empty:
                    pair_data = market_data[pair]

                    if (
                        "timestamp" in pair_data.columns
                        and "close" in pair_data.columns
                    ):
                        # Find closest data point
                        time_diffs = abs(pair_data["timestamp"] - timestamp)
                        closest_idx = time_diffs.idxmin()

                        # Get integer position instead of label
                        try:
                            closest_pos = pair_data.index.get_loc(closest_idx)
                            # Handle case where get_loc returns slice or boolean array
                            if isinstance(closest_pos, (slice, np.ndarray)):
                                closest_pos = 0  # Default to start if ambiguous
                            closest_pos = int(closest_pos)
                        except (KeyError, TypeError):
                            closest_pos = 0

                        # Calculate recent volatility
                        window_size = min(20, closest_pos)
                        if window_size > 1:
                            recent_data = pair_data.iloc[
                                closest_pos - window_size + 1 : closest_pos + 1
                            ]
                            returns = recent_data["close"].pct_change().dropna()
                            if not returns.empty:
                                volatility = returns.std()
                                volatilities.append(volatility)

            if volatilities:
                return float(np.mean(volatilities))
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating risk sentiment proxy: {e}")
            return 0.0

    def _calculate_factor_attributions(
        self, strategy_returns: pd.Series, factor_exposures: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """Calculate factor attributions using simplified regression approach."""
        try:
            if strategy_returns.empty or not factor_exposures:
                return {}

            attributions = {}

            # Align time series
            common_dates = strategy_returns.index

            # Calculate attribution for each factor
            for factor_name, exposure_series in factor_exposures.items():
                try:
                    # Align exposure series with strategy returns
                    aligned_exposure = exposure_series.reindex(
                        common_dates, fill_value=0
                    )

                    # Calculate correlation-based attribution
                    if len(aligned_exposure) > 1 and aligned_exposure.std() > 0:
                        correlation = np.corrcoef(
                            np.array(strategy_returns.values),
                            np.array(aligned_exposure.values),
                        )[0, 1]

                        # Attribution = correlation * exposure_contribution
                        avg_exposure = aligned_exposure.mean()
                        attribution = (
                            correlation * avg_exposure * strategy_returns.std()
                        )

                        # Normalize attribution
                        attributions[factor_name] = float(attribution)
                    else:
                        attributions[factor_name] = 0.0

                except Exception as factor_error:
                    logger.warning(
                        f"Error calculating attribution for {factor_name}: {factor_error}"
                    )
                    attributions[factor_name] = 0.0

            # Normalize attributions to sum to 1
            total_attribution = sum(abs(attr) for attr in attributions.values())
            if total_attribution > 0:
                attributions = {
                    factor: attr / total_attribution
                    for factor, attr in attributions.items()
                }

            return attributions

        except Exception as e:
            logger.error(f"Error calculating factor attributions: {e}")
            return {}

    async def analyze_factor_correlation(
        self, strategy_results: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze correlations between different factors."""
        try:
            logger.info("Starting factor correlation analysis")

            # Extract factor exposures
            factor_exposures = await self._extract_factor_exposures(
                strategy_results, market_data
            )

            if not factor_exposures:
                return {}

            # Calculate correlation matrix
            factor_names = list(factor_exposures.keys())
            correlation_matrix = {}

            for factor1 in factor_names:
                correlation_matrix[factor1] = {}
                for factor2 in factor_names:
                    if factor1 == factor2:
                        correlation_matrix[factor1][factor2] = 1.0
                    else:
                        exposure1 = factor_exposures[factor1]
                        exposure2 = factor_exposures[factor2]

                        # Align series
                        common_index = exposure1.index.intersection(exposure2.index)  # type: ignore
                        if len(common_index) > 1:
                            aligned1 = exposure1.loc[common_index]
                            aligned2 = exposure2.loc[common_index]

                            if aligned1.std() > 0 and aligned2.std() > 0:
                                correlation = np.corrcoef(
                                    np.array(aligned1.values), np.array(aligned2.values)
                                )[0, 1]
                                correlation_matrix[factor1][factor2] = float(
                                    correlation
                                )
                            else:
                                correlation_matrix[factor1][factor2] = 0.0
                        else:
                            correlation_matrix[factor1][factor2] = 0.0

            logger.info("Factor correlation analysis completed")
            return correlation_matrix

        except Exception as e:
            logger.error(f"Error in factor correlation analysis: {e}")
            return {}
