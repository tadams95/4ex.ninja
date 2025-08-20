"""
Dynamic Position Sizing Service for 4ex.ninja

Implements intelligent position sizing based on:
- Signal strength and confluence
- Market volatility (ATR)
- Portfolio correlation and risk management
- Session quality multipliers
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging


class DynamicPositionSizingService:
    """Calculates optimal position sizes based on multiple risk factors."""

    def __init__(self, base_risk_percent: float = 1.5, max_risk_percent: float = 3.0):
        self.logger = logging.getLogger(__name__)
        self.base_risk_percent = base_risk_percent  # Base risk per trade
        self.max_risk_percent = max_risk_percent  # Maximum risk per trade

        # Risk multipliers based on different factors
        self.signal_strength_multipliers = {
            "weak": 0.5,  # 0.75% risk
            "moderate": 0.8,  # 1.2% risk
            "strong": 1.0,  # 1.5% risk (base)
            "very_strong": 1.3,  # 1.95% risk
            "confluence": 1.5,  # 2.25% risk
        }

        # Session quality multipliers (from session manager)
        self.session_multipliers = {
            0.7: 0.6,  # Poor session
            0.8: 0.8,  # Below average
            1.0: 1.0,  # Average
            1.1: 1.1,  # Good session
            1.2: 1.2,  # High quality
            1.3: 1.3,  # Premium overlap
        }

        # Volatility adjustment factors
        self.volatility_adjustments = {
            "very_low": 1.3,  # Increase size in low volatility
            "low": 1.1,
            "normal": 1.0,
            "high": 0.8,  # Reduce size in high volatility
            "very_high": 0.6,
        }

        # Currency correlation limits (max exposure per currency)
        self.currency_limits = {
            "USD": 6.0,  # Max 6% total USD exposure
            "EUR": 4.5,  # Max 4.5% total EUR exposure
            "GBP": 4.5,  # Max 4.5% total GBP exposure
            "JPY": 6.0,  # Max 6% total JPY exposure (our specialty)
            "AUD": 3.0,  # Max 3% total AUD exposure
            "CAD": 3.0,  # Max 3% total CAD exposure
            "CHF": 3.0,  # Max 3% total CHF exposure
        }

    def calculate_position_size(
        self,
        pair: str,
        entry_price: float,
        stop_loss: float,
        account_balance: float,
        signal_data: Dict,
        market_data: Optional[pd.DataFrame] = None,
        current_positions: Optional[Dict] = None,
    ) -> Dict:
        """
        Calculate optimal position size based on multiple risk factors.

        Args:
            pair: Currency pair (e.g., "USD_JPY")
            entry_price: Proposed entry price
            stop_loss: Stop loss price
            account_balance: Current account balance
            signal_data: Dict containing signal strength, confluence score, session quality
            market_data: Recent OHLC data for volatility calculations
            current_positions: Dict of current open positions

        Returns:
            Dict with position sizing recommendations
        """
        try:
            # 1. Calculate base position size
            risk_amount = account_balance * (self.base_risk_percent / 100)
            stop_distance = abs(entry_price - stop_loss)

            if stop_distance == 0:
                return {"error": "Invalid stop loss: distance cannot be zero"}

            base_position_size = risk_amount / stop_distance

            # 2. Apply signal strength multiplier
            signal_strength = signal_data.get("signal_strength", "moderate")
            signal_multiplier = self.signal_strength_multipliers.get(
                signal_strength, 1.0
            )

            # 3. Apply confluence score multiplier
            confluence_score = signal_data.get("confluence_score", 0.0)
            confluence_multiplier = 1.0 + (
                confluence_score * 0.2
            )  # +20% per confluence point

            # 4. Apply session quality multiplier
            session_quality = signal_data.get("session_quality", 1.0)
            session_multiplier = self._get_session_multiplier(session_quality)

            # 5. Apply volatility adjustment
            volatility_multiplier = self._calculate_volatility_multiplier(
                market_data, pair
            )

            # 6. Check currency exposure limits
            currency_multiplier = self._check_currency_limits(pair, current_positions)

            # 7. Calculate final position size
            total_multiplier = (
                signal_multiplier
                * confluence_multiplier
                * session_multiplier
                * volatility_multiplier
                * currency_multiplier
            )

            final_position_size = base_position_size * total_multiplier

            # 8. Apply maximum risk limit
            max_position_size = (
                account_balance * (self.max_risk_percent / 100)
            ) / stop_distance
            final_position_size = min(final_position_size, max_position_size)

            # 9. Calculate risk percentages
            final_risk_amount = final_position_size * stop_distance
            final_risk_percent = (final_risk_amount / account_balance) * 100

            return {
                "pair": pair,
                "recommended_position_size": round(final_position_size, 2),
                "risk_amount": round(final_risk_amount, 2),
                "risk_percent": round(final_risk_percent, 2),
                "stop_distance_pips": self._calculate_pips(stop_distance, pair),
                "multipliers": {
                    "signal_strength": signal_multiplier,
                    "confluence_score": confluence_multiplier,
                    "session_quality": session_multiplier,
                    "volatility": volatility_multiplier,
                    "currency_limit": currency_multiplier,
                    "total_multiplier": round(total_multiplier, 3),
                },
                "limits": {
                    "max_risk_percent": self.max_risk_percent,
                    "base_risk_percent": self.base_risk_percent,
                    "position_capped": final_position_size >= max_position_size,
                },
                "recommendation": self._get_sizing_recommendation(
                    final_risk_percent, total_multiplier
                ),
            }

        except Exception as e:
            self.logger.error(f"Error calculating position size for {pair}: {str(e)}")
            return {"error": f"Position sizing calculation failed: {str(e)}"}

    def _get_session_multiplier(self, session_quality: float) -> float:
        """Get session quality multiplier."""
        # Find closest session quality level
        closest_quality = min(
            self.session_multipliers.keys(), key=lambda x: abs(x - session_quality)
        )
        return self.session_multipliers[closest_quality]

    def _calculate_volatility_multiplier(
        self, market_data: Optional[pd.DataFrame], pair: str
    ) -> float:
        """Calculate volatility-based position size adjustment."""
        if market_data is None or len(market_data) < 20:
            return 1.0  # Default multiplier if no data

        try:
            # Calculate ATR (Average True Range)
            high = market_data["high"]
            low = market_data["low"]
            close = market_data["close"]
            prev_close = close.shift(1)

            true_range = pd.DataFrame(
                {
                    "hl": high - low,
                    "hc": abs(high - prev_close),
                    "lc": abs(low - prev_close),
                }
            ).max(axis=1)

            atr_14 = true_range.rolling(window=14).mean().iloc[-1]
            current_price = close.iloc[-1]

            # Calculate ATR as percentage of price
            atr_percent = (atr_14 / current_price) * 100

            # Determine volatility regime
            if atr_percent < 0.5:
                volatility_regime = "very_low"
            elif atr_percent < 0.8:
                volatility_regime = "low"
            elif atr_percent < 1.5:
                volatility_regime = "normal"
            elif atr_percent < 2.5:
                volatility_regime = "high"
            else:
                volatility_regime = "very_high"

            return self.volatility_adjustments[volatility_regime]

        except Exception as e:
            self.logger.warning(f"Error calculating volatility for {pair}: {str(e)}")
            return 1.0

    def _check_currency_limits(
        self, pair: str, current_positions: Optional[Dict]
    ) -> float:
        """Check currency exposure limits and adjust position size."""
        if not current_positions:
            return 1.0  # No current positions, no adjustment needed

        # Extract currencies from pair (e.g., "USD_JPY" -> ["USD", "JPY"])
        base_currency, quote_currency = pair.split("_")

        # Calculate current exposure for both currencies
        base_exposure = self._calculate_currency_exposure(
            base_currency, current_positions
        )
        quote_exposure = self._calculate_currency_exposure(
            quote_currency, current_positions
        )

        # Check against limits
        base_limit = self.currency_limits.get(base_currency, 3.0)
        quote_limit = self.currency_limits.get(quote_currency, 3.0)

        base_available = max(0, base_limit - base_exposure)
        quote_available = max(0, quote_limit - quote_exposure)

        # Calculate reduction multiplier based on available exposure
        if base_available <= 0.5 or quote_available <= 0.5:
            return 0.3  # Heavily reduce if near limits
        elif base_available <= 1.0 or quote_available <= 1.0:
            return 0.6  # Moderately reduce
        elif base_available <= 2.0 or quote_available <= 2.0:
            return 0.8  # Slightly reduce
        else:
            return 1.0  # No reduction needed

    def _calculate_currency_exposure(
        self, currency: str, current_positions: Dict
    ) -> float:
        """Calculate current exposure percentage for a specific currency."""
        total_exposure = 0.0

        for position_pair, position_data in current_positions.items():
            if currency in position_pair:
                risk_percent = position_data.get("risk_percent", 0.0)
                total_exposure += risk_percent

        return total_exposure

    def _calculate_pips(self, price_distance: float, pair: str) -> float:
        """Convert price distance to pips."""
        jpy_pairs = ["USD_JPY", "EUR_JPY", "GBP_JPY", "AUD_JPY", "CHF_JPY", "CAD_JPY"]

        if any(jpy in pair for jpy in jpy_pairs):
            return price_distance * 100  # JPY pairs: 0.01 = 1 pip
        else:
            return price_distance * 10000  # Other pairs: 0.0001 = 1 pip

    def _get_sizing_recommendation(
        self, risk_percent: float, total_multiplier: float
    ) -> str:
        """Get human-readable recommendation based on position sizing."""
        if risk_percent >= 2.5:
            return "HIGH_RISK - Consider reducing position size"
        elif risk_percent >= 2.0:
            return "MODERATE_RISK - Good opportunity with elevated risk"
        elif risk_percent >= 1.0:
            return "OPTIMAL - Well-balanced risk/reward"
        elif risk_percent >= 0.5:
            return "CONSERVATIVE - Lower risk, good for uncertain signals"
        else:
            return "MINIMAL - Very low risk, consider if opportunity is worth it"

    def get_portfolio_risk_analysis(
        self, current_positions: Dict, account_balance: float
    ) -> Dict:
        """Analyze current portfolio risk distribution."""
        if not current_positions:
            return {
                "total_risk_percent": 0.0,
                "currency_exposures": {},
                "position_count": 0,
                "risk_status": "CLEAR",
            }

        total_risk = sum(
            pos.get("risk_percent", 0.0) for pos in current_positions.values()
        )

        # Calculate currency exposures
        currency_exposures = {}
        all_currencies = set()

        for pair in current_positions.keys():
            base, quote = pair.split("_")
            all_currencies.update([base, quote])

        for currency in all_currencies:
            exposure = self._calculate_currency_exposure(currency, current_positions)
            currency_exposures[currency] = {
                "current_exposure": round(exposure, 2),
                "limit": self.currency_limits.get(currency, 3.0),
                "available": round(
                    self.currency_limits.get(currency, 3.0) - exposure, 2
                ),
            }

        # Determine risk status
        if total_risk >= 15.0:
            risk_status = "CRITICAL - Reduce positions"
        elif total_risk >= 10.0:
            risk_status = "HIGH - Monitor closely"
        elif total_risk >= 6.0:
            risk_status = "MODERATE - Good diversification"
        else:
            risk_status = "LOW - Room for more positions"

        return {
            "total_risk_percent": round(total_risk, 2),
            "currency_exposures": currency_exposures,
            "position_count": len(current_positions),
            "risk_status": risk_status,
            "max_portfolio_risk": 15.0,
            "recommendations": self._get_portfolio_recommendations(
                total_risk, currency_exposures
            ),
        }

    def _get_portfolio_recommendations(
        self, total_risk: float, currency_exposures: Dict
    ) -> List[str]:
        """Generate portfolio management recommendations."""
        recommendations = []

        if total_risk >= 12.0:
            recommendations.append(
                "Consider closing weakest positions to reduce total risk"
            )

        for currency, data in currency_exposures.items():
            if data["available"] <= 0.5:
                recommendations.append(
                    f"Avoid new {currency} positions - near exposure limit"
                )
            elif data["available"] <= 1.0:
                recommendations.append(
                    f"Limit new {currency} positions - approaching exposure limit"
                )

        if total_risk <= 3.0:
            recommendations.append(
                "Portfolio risk very low - consider increasing position sizes or adding positions"
            )

        return recommendations
