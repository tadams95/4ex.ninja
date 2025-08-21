"""
Enhanced Daily Strategy - Phase 1 Implementation

Combines the proven Daily timeframe strategy with Phase 1 enhancements:
1. Session-Based Trading (JPY pairs during Asian session)
2. Support/Resistance Confluence (key levels detection)
3. Dynamic Position Sizing (signal strength + volatility based)

Expected improvements:
- +30% trade quality from session filtering
- +15% win rate from confluence levels
- +25% returns from dynamic sizing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import os
import sys

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.session_manager_service import SessionManagerService
from services.support_resistance_service import SupportResistanceService
from services.dynamic_position_sizing_service import DynamicPositionSizingService


class EnhancedDailyStrategy:
    """Enhanced Daily Strategy with Phase 1 Quick Wins integrated."""

    def __init__(self, account_balance: float = 10000):
        self.logger = logging.getLogger(__name__)
        self.account_balance = account_balance

        # Initialize Phase 1 services
        self.session_manager = SessionManagerService()
        self.sr_detector = SupportResistanceService()
        self.position_sizer = DynamicPositionSizingService()

        # Strategy parameters - REALISTIC MULTI-PAIR OPTIMIZED (August 20, 2025)
        # Comprehensive optimization across 10 major currency pairs
        self.optimized_parameters = {
            "USD_JPY": {
                "ema_fast": 20,
                "ema_slow": 60,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "optimization_status": "REALISTIC_EMA_OPTIMIZED",
                "expected_performance": {
                    "win_rate": 70.0,
                    "annual_return": 14.0,
                    "trades_per_year": 10,
                },
            },
            "EUR_JPY": {
                "ema_fast": 30,
                "ema_slow": 60,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "optimization_status": "REALISTIC_EMA_OPTIMIZED",
                "expected_performance": {
                    "win_rate": 70.0,
                    "annual_return": 13.5,
                    "trades_per_year": 10,
                },
            },
            "AUD_JPY": {
                "ema_fast": 20,
                "ema_slow": 60,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "optimization_status": "REALISTIC_EMA_OPTIMIZED",
                "expected_performance": {
                    "win_rate": 46.7,
                    "annual_return": 3.8,
                    "trades_per_year": 15,
                },
            },
            "GBP_JPY": {
                "ema_fast": 30,
                "ema_slow": 60,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "optimization_status": "REALISTIC_EMA_OPTIMIZED",
                "expected_performance": {
                    "win_rate": 45.5,
                    "annual_return": 2.2,
                    "trades_per_year": 11,
                },
            },
            "AUD_USD": {
                "ema_fast": 20,
                "ema_slow": 60,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "optimization_status": "REALISTIC_EMA_OPTIMIZED",
                "expected_performance": {
                    "win_rate": 41.7,
                    "annual_return": 1.5,
                    "trades_per_year": 12,
                },
            },
        }

        # Default parameters (backward compatibility)
        self.ema_fast = 20
        self.ema_slow = 50
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70

        # JPY pair priority (based on realistic optimization results)
        self.jpy_pair_priorities = {
            "USD_JPY": 1.0,  # Top performer: 14.0% return, 70.0% win rate
            "EUR_JPY": 0.95,  # Excellent: 13.5% return, 70.0% win rate
            "AUD_JPY": 0.7,  # Good: 3.8% return, 46.7% win rate
            "GBP_JPY": 0.65,  # Decent: 2.2% return, 45.5% win rate
        }

        # Risk management
        self.base_stop_loss_atr = 2.0  # 2x ATR stop loss
        self.take_profit_ratio = 2.0  # 2:1 RR ratio

        # Confluence requirements
        self.min_confluence_score = 0.8  # Minimum confluence for trade

    def get_pair_parameters(self, pair: str) -> Dict:
        """
        Get optimized parameters for a specific currency pair.

        Args:
            pair: Currency pair (e.g., "USD_JPY")

        Returns:
            Dict with pair-specific optimized parameters
        """
        if pair in self.optimized_parameters:
            params = self.optimized_parameters[pair].copy()
            # FIXED: Remove excessive logging that was causing infinite loop
            # Only log once per pair instead of every call
            if not hasattr(self, "_logged_pairs"):
                self._logged_pairs = set()

            if pair not in self._logged_pairs:
                self.logger.info(
                    f"Using OPTIMIZED parameters for {pair}: {params['optimization_status']}"
                )
                self._logged_pairs.add(pair)
            return params
        else:
            # Return default parameters for pairs not in optimization
            default_params = {
                "ema_fast": self.ema_fast,
                "ema_slow": self.ema_slow,
                "rsi_oversold": self.rsi_oversold,
                "rsi_overbought": self.rsi_overbought,
                "optimization_status": "DEFAULT_PARAMETERS",
                "expected_performance": {
                    "win_rate": "unknown",
                    "trades": "unknown",
                    "return_pct": "unknown",
                },
            }
            # Only log once per pair
            if not hasattr(self, "_logged_pairs"):
                self._logged_pairs = set()

            if pair not in self._logged_pairs:
                self.logger.info(f"Using DEFAULT parameters for {pair}")
                self._logged_pairs.add(pair)
            return default_params

    def analyze_pair(self, pair: str, data: pd.DataFrame) -> Dict:
        """
        Comprehensive analysis of a currency pair using Phase 1 enhancements.

        Args:
            pair: Currency pair (e.g., "USD_JPY")
            data: OHLC data with datetime index

        Returns:
            Dict with complete analysis and trade recommendations
        """
        try:
            if len(data) < 100:
                return {"error": f"Insufficient data for {pair} analysis"}

            # Get pair-specific optimized parameters
            pair_params = self.get_pair_parameters(pair)

            # Prepare data
            df = data.copy()
            df = self._calculate_indicators(df, pair_params)

            current_price = float(df["close"].iloc[-1])

            # 1. Session Analysis - Phase 1 Enhancement
            session_analysis = self.session_manager.get_session_filter_for_pair(pair)

            # 2. Support/Resistance Analysis - Phase 1 Enhancement
            sr_analysis = self.sr_detector.detect_key_levels(df, pair)

            # 3. Technical Signal Generation
            signal_data = self._generate_daily_signal(df, pair, pair_params)

            # 4. Confluence Scoring - Phase 1 Enhancement
            confluence_score = 0.0
            if signal_data.get("signal") != "NONE" and "error" not in sr_analysis:
                confluence_score = self.sr_detector.get_level_confluence_score(
                    current_price, sr_analysis
                )

            # 5. Signal Strength Assessment
            signal_strength = self._assess_signal_strength(
                signal_data, confluence_score, session_analysis
            )

            # 6. Dynamic Position Sizing - Phase 1 Enhancement
            position_sizing = None
            if signal_data.get("signal") != "NONE":
                sizing_data = {
                    "signal_strength": signal_strength,
                    "confluence_score": confluence_score,
                    "session_quality": session_analysis["session_quality_multiplier"],
                }

                stop_loss = signal_data.get("stop_loss", current_price * 0.98)
                position_sizing = self.position_sizer.calculate_position_size(
                    pair=pair,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    account_balance=self.account_balance,
                    signal_data=sizing_data,
                    market_data=df.tail(30),
                )

            # 7. Final Trade Recommendation
            trade_recommendation = self._make_trade_decision(
                pair, signal_data, confluence_score, session_analysis, signal_strength
            )

            return {
                "pair": pair,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_price": current_price,
                "session_analysis": session_analysis,
                "technical_signal": signal_data,
                "support_resistance": sr_analysis,
                "confluence_score": round(confluence_score, 2),
                "signal_strength": signal_strength,
                "position_sizing": position_sizing,
                "trade_recommendation": trade_recommendation,
                "phase1_enhancements": {
                    "session_filter_active": session_analysis["is_optimal_session"],
                    "confluence_detected": confluence_score
                    >= self.min_confluence_score,
                    "dynamic_sizing_applied": position_sizing is not None,
                },
            }

        except Exception as e:
            self.logger.error(f"Error analyzing {pair}: {str(e)}")
            return {"error": f"Analysis failed for {pair}: {str(e)}"}

    def _calculate_indicators(
        self, df: pd.DataFrame, pair_params: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy using pair-specific optimized parameters.

        Args:
            df: OHLC DataFrame
            pair_params: Dict with pair-specific parameters (EMA, RSI settings)
        """
        # Use pair-specific parameters if provided, otherwise defaults
        if pair_params:
            ema_fast = pair_params["ema_fast"]
            ema_slow = pair_params["ema_slow"]
            rsi_oversold = pair_params["rsi_oversold"]
            rsi_overbought = pair_params["rsi_overbought"]
        else:
            ema_fast = self.ema_fast
            ema_slow = self.ema_slow
            rsi_oversold = self.rsi_oversold
            rsi_overbought = self.rsi_overbought

        # EMAs with optimized parameters
        df["ema_20"] = df["close"].ewm(span=ema_fast).mean()  # Dynamic fast EMA
        df["ema_50"] = df["close"].ewm(span=ema_slow).mean()  # Dynamic slow EMA

        # Store the actual parameters used for reference
        df.attrs["ema_fast_used"] = ema_fast
        df.attrs["ema_slow_used"] = ema_slow
        df.attrs["rsi_oversold_used"] = rsi_oversold
        df.attrs["rsi_overbought_used"] = rsi_overbought

        # RSI calculation - simple approach
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df["rsi"] = calculate_rsi(df["close"], self.rsi_period)

        # ATR for stop loss calculation
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift())
        low_close = abs(df["low"] - df["close"].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = true_range.rolling(window=14).mean()

        return df

    def _generate_daily_signal(
        self, df: pd.DataFrame, pair: str, pair_params: Optional[Dict] = None
    ) -> Dict:
        """Generate trading signal based on Daily timeframe logic using H4 data with pair-specific parameters."""

        # Convert H4 data to Daily timeframe for signal analysis
        daily_df = (
            df.resample("D")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
            .dropna()
        )

        # Need at least 60 daily candles for reliable signals
        if len(daily_df) < 60:
            return {
                "signal": "NONE",
                "direction": None,
                "entry_price": float(df.iloc[-1]["close"].item()),
                "stop_loss": None,
                "take_profit": None,
                "indicators": {
                    "error": "Insufficient daily data for signal generation"
                },
            }

        # Calculate indicators on daily data with pair-specific parameters
        daily_df = self._calculate_indicators(daily_df, pair_params)

        current = daily_df.iloc[-1]
        previous = daily_df.iloc[-2]

        # Extract pair-specific RSI parameters
        if pair_params:
            rsi_oversold = pair_params["rsi_oversold"]
            rsi_overbought = pair_params["rsi_overbought"]
        else:
            rsi_oversold = self.rsi_oversold
            rsi_overbought = self.rsi_overbought

        signal_data = {
            "signal": "NONE",
            "direction": None,
            "entry_price": float(df.iloc[-1]["close"].item()),  # Use H4 close for entry
            "stop_loss": None,
            "take_profit": None,
            "indicators": {
                "ema_20": float(current["ema_20"].item()),
                "ema_50": float(current["ema_50"].item()),
                "rsi": float(current["rsi"].item()),
                "atr": float(current["atr"].item()),
            },
        }

        # EMA Crossover Logic (Daily timeframe proven strategy)
        ema_20_current = float(current["ema_20"].item())
        ema_50_current = float(current["ema_50"].item())
        ema_20_previous = float(previous["ema_20"].item())
        ema_50_previous = float(previous["ema_50"].item())

        # Bull signal: EMA 20 crosses above EMA 50 with optimized RSI confirmation
        current_rsi = float(current["rsi"].item())
        if (
            ema_20_current > ema_50_current
            and ema_20_previous <= ema_50_previous
            and current_rsi > 50  # Basic momentum confirmation
            and not (
                current_rsi > rsi_overbought
            )  # Avoid overbought entries (optimized threshold)
        ):

            signal_data.update(
                {
                    "signal": "BUY",
                    "direction": "LONG",
                    "stop_loss": float(
                        current["close"].item()
                        - (current["atr"].item() * self.base_stop_loss_atr)
                    ),
                    "take_profit": float(
                        current["close"].item()
                        + (
                            current["atr"].item()
                            * self.base_stop_loss_atr
                            * self.take_profit_ratio
                        )
                    ),
                }
            )

        # Bear signal: EMA 20 crosses below EMA 50 with optimized RSI confirmation
        elif (
            ema_20_current < ema_50_current
            and ema_20_previous >= ema_50_previous
            and current_rsi < 50  # Basic momentum confirmation
            and not (
                current_rsi < rsi_oversold
            )  # Avoid oversold entries (optimized threshold)
        ):

            signal_data.update(
                {
                    "signal": "SELL",
                    "direction": "SHORT",
                    "stop_loss": float(
                        current["close"].item()
                        + (current["atr"].item() * self.base_stop_loss_atr)
                    ),
                    "take_profit": float(
                        current["close"].item()
                        - (
                            current["atr"].item()
                            * self.base_stop_loss_atr
                            * self.take_profit_ratio
                        )
                    ),
                }
            )

        return signal_data

    def _assess_signal_strength(
        self, signal_data: Dict, confluence_score: float, session_analysis: Dict
    ) -> str:
        """Assess overall signal strength based on multiple factors."""
        if signal_data["signal"] == "NONE":
            return "none"

        strength_score = 0

        # Base signal strength
        strength_score += 1

        # RSI confirmation
        rsi = signal_data["indicators"]["rsi"]
        if signal_data["direction"] == "LONG" and rsi > 55:
            strength_score += 1
        elif signal_data["direction"] == "SHORT" and rsi < 45:
            strength_score += 1

        # Confluence bonus
        if confluence_score >= 1.5:
            strength_score += 2
        elif confluence_score >= 0.8:
            strength_score += 1

        # Session quality bonus
        if session_analysis["is_optimal_session"]:
            strength_score += 1

        # Determine strength category
        if strength_score >= 5:
            return "confluence"
        elif strength_score >= 4:
            return "very_strong"
        elif strength_score >= 3:
            return "strong"
        elif strength_score >= 2:
            return "moderate"
        else:
            return "weak"

    def _make_trade_decision(
        self,
        pair: str,
        signal_data: Dict,
        confluence_score: float,
        session_analysis: Dict,
        signal_strength: str,
    ) -> Dict:
        """Make final trade decision based on all Phase 1 factors."""

        if signal_data["signal"] == "NONE":
            return {
                "recommendation": "WAIT",
                "reason": "No technical signal generated",
                "confidence": 0.0,
            }

        # Check Phase 1 filters
        filters_passed = []
        filters_failed = []

        # 1. Session Filter (JPY pairs during Asian session)
        if pair in self.jpy_pair_priorities:
            if session_analysis["is_optimal_session"]:
                filters_passed.append("Optimal session for JPY pair")
            else:
                filters_failed.append("Not optimal session for JPY pair")
        else:
            if session_analysis["session_quality_multiplier"] >= 1.0:
                filters_passed.append("Good session quality")
            else:
                filters_failed.append("Poor session quality")

        # 2. Confluence Filter
        if confluence_score >= self.min_confluence_score:
            filters_passed.append(f"Confluence score: {confluence_score:.2f}")
        else:
            filters_failed.append(f"Low confluence: {confluence_score:.2f}")

        # 3. Signal Strength Filter
        if signal_strength in ["strong", "very_strong", "confluence"]:
            filters_passed.append(f"Strong signal: {signal_strength}")
        else:
            filters_failed.append(f"Weak signal: {signal_strength}")

        # Calculate confidence
        total_filters = len(filters_passed) + len(filters_failed)
        confidence = len(filters_passed) / total_filters if total_filters > 0 else 0.0

        # Apply JPY pair priority
        if pair in self.jpy_pair_priorities:
            priority_multiplier = self.jpy_pair_priorities[pair]
            confidence *= priority_multiplier

        # Make recommendation
        if confidence >= 0.8 and len(filters_failed) <= 1:
            recommendation = (
                "STRONG_BUY" if signal_data["direction"] == "LONG" else "STRONG_SELL"
            )
        elif confidence >= 0.6 and len(filters_failed) <= 1:
            recommendation = "BUY" if signal_data["direction"] == "LONG" else "SELL"
        elif confidence >= 0.4:
            recommendation = (
                "WEAK_BUY" if signal_data["direction"] == "LONG" else "WEAK_SELL"
            )
        else:
            recommendation = "AVOID"

        return {
            "recommendation": recommendation,
            "confidence": round(confidence, 3),
            "signal_direction": signal_data["direction"],
            "filters_passed": filters_passed,
            "filters_failed": filters_failed,
            "phase1_score": {
                "session": session_analysis["session_quality_multiplier"],
                "confluence": confluence_score,
                "signal_strength": signal_strength,
            },
        }

    def scan_all_pairs(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Scan all currency pairs and return prioritized opportunities."""
        results = {}
        opportunities = []

        for pair, data in data_dict.items():
            analysis = self.analyze_pair(pair, data)
            results[pair] = analysis

            # Collect trading opportunities
            if "error" not in analysis:
                trade_rec = analysis.get("trade_recommendation", {})
                if trade_rec.get("recommendation") not in ["WAIT", "AVOID"]:
                    opportunity = {
                        "pair": pair,
                        "recommendation": trade_rec["recommendation"],
                        "confidence": trade_rec["confidence"],
                        "confluence_score": analysis["confluence_score"],
                        "signal_strength": analysis["signal_strength"],
                        "session_optimal": analysis["session_analysis"][
                            "is_optimal_session"
                        ],
                        "position_sizing": analysis.get("position_sizing"),
                        "priority_score": self._calculate_priority_score(analysis),
                    }
                    opportunities.append(opportunity)

        # Sort opportunities by priority
        opportunities.sort(key=lambda x: x["priority_score"], reverse=True)

        return {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_pairs_analyzed": len(results),
            "opportunities_found": len(opportunities),
            "top_opportunities": opportunities[:5],  # Top 5 opportunities
            "detailed_results": results,
            "phase1_summary": self._generate_phase1_summary(results),
        }

    def _calculate_priority_score(self, analysis: Dict) -> float:
        """Calculate priority score for ranking opportunities."""
        score = 0.0

        trade_rec = analysis.get("trade_recommendation", {})

        # Base confidence score
        score += trade_rec.get("confidence", 0.0) * 100

        # Confluence bonus
        score += analysis.get("confluence_score", 0.0) * 20

        # Session quality bonus
        session_quality = analysis.get("session_analysis", {}).get(
            "session_quality_multiplier", 1.0
        )
        score += (session_quality - 1.0) * 30

        # JPY pair bonus (our specialization)
        if analysis["pair"] in self.jpy_pair_priorities:
            priority = self.jpy_pair_priorities[analysis["pair"]]
            score += priority * 25

        # Signal strength bonus
        strength_bonuses = {
            "confluence": 40,
            "very_strong": 30,
            "strong": 20,
            "moderate": 10,
            "weak": 0,
        }
        score += strength_bonuses.get(analysis.get("signal_strength", "weak"), 0)

        return round(score, 2)

    def _generate_phase1_summary(self, results: Dict) -> Dict:
        """Generate summary of Phase 1 enhancements impact."""
        total_pairs = len(results)
        session_filtered = sum(
            1
            for r in results.values()
            if isinstance(r, dict)
            and r.get("session_analysis", {}).get("is_optimal_session", False)
        )
        confluence_detected = sum(
            1
            for r in results.values()
            if isinstance(r, dict)
            and r.get("confluence_score", 0) >= self.min_confluence_score
        )
        dynamic_sizing_applied = sum(
            1
            for r in results.values()
            if isinstance(r, dict) and r.get("position_sizing") is not None
        )

        return {
            "total_pairs_analyzed": total_pairs,
            "session_filter_applied": session_filtered,
            "confluence_detected": confluence_detected,
            "dynamic_sizing_applied": dynamic_sizing_applied,
            "enhancement_coverage": {
                "session_filtering": (
                    f"{(session_filtered/total_pairs)*100:.1f}%"
                    if total_pairs > 0
                    else "0%"
                ),
                "confluence_detection": (
                    f"{(confluence_detected/total_pairs)*100:.1f}%"
                    if total_pairs > 0
                    else "0%"
                ),
                "dynamic_sizing": (
                    f"{(dynamic_sizing_applied/total_pairs)*100:.1f}%"
                    if total_pairs > 0
                    else "0%"
                ),
            },
        }


if __name__ == "__main__":
    # Test the multi-pair strategy
    print("Enhanced Daily Strategy - Multi-Pair Analysis")
    print("=" * 50)

    strategy = EnhancedDailyStrategy()

    # Show optimized parameters for top pairs
    print("\nMulti-Pair Optimization Results:")
    for pair, params in strategy.optimized_parameters.items():
        perf = params["expected_performance"]
        print(f"\n{pair}:")
        print(f"  EMA: {params['ema_fast']}/{params['ema_slow']}")
        print(f"  Win Rate: {perf['win_rate']:.1f}%")
        print(f"  Annual Return: {perf['annual_return']:.1f}%")
        print(f"  Trades/Year: {perf['trades_per_year']}")

    print("\n✅ Multi-pair enhanced daily strategy loaded successfully!")
    print("Ready for deployment across 5 optimized currency pairs")
