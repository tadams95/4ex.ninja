"""
Volatility Impact Analyzer

This module analyzes how different volatility conditions affect strategy performance,
including ATR-based position sizing effectiveness and market regime detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class VolatilityImpactAnalyzer:
    """
    Analyzer for volatility impact on strategy performance.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.volatility_regimes = {
            "low": {"threshold": 0.25, "description": "Low volatility - calm markets"},
            "medium": {
                "threshold": 0.75,
                "description": "Medium volatility - normal conditions",
            },
            "high": {
                "threshold": 1.5,
                "description": "High volatility - stressed markets",
            },
            "extreme": {
                "threshold": float("inf"),
                "description": "Extreme volatility - crisis conditions",
            },
        }

    def analyze_volatility_impact(
        self, strategy_params: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """
        Comprehensive analysis of volatility impact on strategy performance.

        Args:
            strategy_params: Strategy parameters
            historical_data: Historical price data

        Returns:
            Dictionary containing volatility impact analysis
        """
        try:
            self.logger.info("Starting volatility impact analysis")

            analysis_results = {
                "volatility_regimes": {},
                "atr_effectiveness": {},
                "position_sizing_analysis": {},
                "regime_performance": {},
                "volatility_timing": {},
                "recommendations": [],
            }

            # Classify volatility regimes in historical data
            volatility_data = self._classify_volatility_regimes(historical_data)
            analysis_results["volatility_regimes"] = volatility_data

            # Analyze ATR effectiveness across different volatility conditions
            analysis_results["atr_effectiveness"] = self._analyze_atr_effectiveness(
                strategy_params, historical_data, volatility_data
            )

            # Analyze position sizing effectiveness
            analysis_results["position_sizing_analysis"] = (
                self._analyze_position_sizing_impact(
                    strategy_params, historical_data, volatility_data
                )
            )

            # Test performance in different volatility regimes
            analysis_results["regime_performance"] = self._test_regime_performance(
                strategy_params, historical_data, volatility_data
            )

            # Analyze volatility timing and prediction
            analysis_results["volatility_timing"] = self._analyze_volatility_timing(
                historical_data, volatility_data
            )

            # Generate recommendations
            analysis_results["recommendations"] = (
                self._generate_volatility_recommendations(analysis_results)
            )

            self.logger.info("Volatility impact analysis completed")
            return analysis_results

        except Exception as e:
            self.logger.error(f"Volatility impact analysis error: {str(e)}")
            return {"error": str(e)}

    def _classify_volatility_regimes(self, historical_data: pd.DataFrame) -> Dict:
        """Classify historical data into volatility regimes."""
        try:
            data = historical_data.copy()

            # Calculate returns and rolling volatility
            data["returns"] = data["close"].pct_change()
            data["rolling_vol"] = data["returns"].rolling(window=20).std() * np.sqrt(
                252
            )  # Annualized

            # Calculate ATR-based volatility measure
            data["atr"] = self._calculate_atr(data, 14)
            data["atr_pct"] = (
                data["atr"] / data["close"] * 100
            )  # ATR as percentage of price

            # Classify regimes based on volatility percentiles
            vol_data = data["rolling_vol"].dropna()
            if vol_data.empty:
                return {"error": "No valid volatility data"}

            vol_25 = vol_data.quantile(0.25)
            vol_50 = vol_data.quantile(0.50)
            vol_75 = vol_data.quantile(0.75)
            vol_90 = vol_data.quantile(0.90)

            # Classify each period
            conditions = [
                data["rolling_vol"] <= vol_25,
                (data["rolling_vol"] > vol_25) & (data["rolling_vol"] <= vol_50),
                (data["rolling_vol"] > vol_50) & (data["rolling_vol"] <= vol_75),
                (data["rolling_vol"] > vol_75) & (data["rolling_vol"] <= vol_90),
                data["rolling_vol"] > vol_90,
            ]

            choices = ["very_low", "low", "medium", "high", "extreme"]
            data["vol_regime"] = np.select(conditions, choices, default="medium")

            # Calculate regime statistics
            regime_stats = {}
            for regime in choices:
                regime_data = data[data["vol_regime"] == regime]
                if len(regime_data) > 0:
                    regime_stats[regime] = {
                        "periods": len(regime_data),
                        "percentage": len(regime_data) / len(data) * 100,
                        "avg_volatility": regime_data["rolling_vol"].mean(),
                        "avg_atr_pct": regime_data["atr_pct"].mean(),
                        "max_volatility": regime_data["rolling_vol"].max(),
                        "price_range": {
                            "min": regime_data["close"].min(),
                            "max": regime_data["close"].max(),
                            "avg": regime_data["close"].mean(),
                        },
                    }

            return {
                "regime_classification": data[
                    ["close", "rolling_vol", "atr_pct", "vol_regime"]
                ].to_dict("records"),
                "regime_statistics": regime_stats,
                "volatility_thresholds": {
                    "vol_25": float(vol_25),
                    "vol_50": float(vol_50),
                    "vol_75": float(vol_75),
                    "vol_90": float(vol_90),
                },
                "overall_statistics": {
                    "mean_volatility": float(vol_data.mean()),
                    "volatility_std": float(vol_data.std()),
                    "min_volatility": float(vol_data.min()),
                    "max_volatility": float(vol_data.max()),
                },
            }

        except Exception as e:
            self.logger.error(f"Volatility regime classification error: {str(e)}")
            return {"error": str(e)}

    def _analyze_atr_effectiveness(
        self,
        strategy_params: Dict,
        historical_data: pd.DataFrame,
        volatility_data: Dict,
    ) -> Dict:
        """Analyze how ATR-based stop losses perform in different volatility regimes."""
        try:
            atr_period = strategy_params.get("atr_period", 14)
            sl_atr_multiplier = strategy_params.get("sl_atr_multiplier", 1.5)
            tp_atr_multiplier = strategy_params.get("tp_atr_multiplier", 2.0)

            data = historical_data.copy()
            data["atr"] = self._calculate_atr(data, atr_period)
            data["atr_pct"] = data["atr"] / data["close"] * 100

            # Add volatility regime information
            regime_data = volatility_data.get("regime_classification", [])
            if regime_data:
                regime_df = pd.DataFrame(regime_data)
                data["vol_regime"] = regime_df["vol_regime"].values[: len(data)]
            else:
                data["vol_regime"] = "medium"  # Default if no regime data

            atr_analysis = {}

            # Analyze ATR effectiveness by regime
            for regime in ["very_low", "low", "medium", "high", "extreme"]:
                regime_subset = data[data["vol_regime"] == regime]
                if len(regime_subset) < 10:  # Need minimum data
                    continue

                # Calculate ATR statistics for this regime
                atr_stats = {
                    "avg_atr_pct": regime_subset["atr_pct"].mean(),
                    "atr_volatility": regime_subset["atr_pct"].std(),
                    "min_atr_pct": regime_subset["atr_pct"].min(),
                    "max_atr_pct": regime_subset["atr_pct"].max(),
                }

                # Simulate stop loss effectiveness
                sl_effectiveness = self._test_stop_loss_effectiveness(
                    regime_subset, sl_atr_multiplier, tp_atr_multiplier
                )

                atr_analysis[regime] = {
                    "atr_statistics": atr_stats,
                    "stop_loss_effectiveness": sl_effectiveness,
                    "data_points": len(regime_subset),
                }

            # Overall ATR effectiveness assessment
            overall_assessment = {
                "atr_stability_across_regimes": self._calculate_atr_stability(
                    atr_analysis
                ),
                "recommended_atr_adjustments": self._recommend_atr_adjustments(
                    atr_analysis
                ),
                "risk_assessment": self._assess_atr_risk(atr_analysis),
            }

            return {
                "regime_analysis": atr_analysis,
                "overall_assessment": overall_assessment,
            }

        except Exception as e:
            self.logger.error(f"ATR effectiveness analysis error: {str(e)}")
            return {"error": str(e)}

    def _test_stop_loss_effectiveness(
        self, data: pd.DataFrame, sl_multiplier: float, tp_multiplier: float
    ) -> Dict:
        """Test stop loss effectiveness in given data."""
        try:
            if len(data) < 20:
                return {"error": "Insufficient data"}

            # Simulate trades with current ATR-based stops
            trades_hit_sl = 0
            trades_hit_tp = 0
            total_simulated_trades = 0

            for i in range(10, len(data) - 10):  # Leave buffer
                entry_price = data["close"].iloc[i]
                atr = data["atr"].iloc[i]

                if pd.isna(atr) or atr <= 0:
                    continue

                # Set stop loss and take profit levels
                stop_loss = entry_price - (atr * sl_multiplier)  # Assuming long trades
                take_profit = entry_price + (atr * tp_multiplier)

                # Check next 10 periods for hits
                future_prices = data["close"].iloc[i + 1 : i + 11]

                sl_hit = any(future_prices <= stop_loss)
                tp_hit = any(future_prices >= take_profit)

                total_simulated_trades += 1
                if sl_hit:
                    trades_hit_sl += 1
                if tp_hit:
                    trades_hit_tp += 1

            if total_simulated_trades == 0:
                return {"error": "No valid trades simulated"}

            return {
                "total_trades": total_simulated_trades,
                "stop_loss_hit_rate": trades_hit_sl / total_simulated_trades,
                "take_profit_hit_rate": trades_hit_tp / total_simulated_trades,
                "neither_hit_rate": 1
                - (trades_hit_sl + trades_hit_tp) / total_simulated_trades,
                "effectiveness_score": (trades_hit_tp - trades_hit_sl)
                / total_simulated_trades,
            }

        except Exception as e:
            self.logger.error(f"Stop loss effectiveness test error: {str(e)}")
            return {"error": str(e)}

    def _analyze_position_sizing_impact(
        self,
        strategy_params: Dict,
        historical_data: pd.DataFrame,
        volatility_data: Dict,
    ) -> Dict:
        """Analyze how position sizing performs across volatility regimes."""
        try:
            risk_per_trade = strategy_params.get("risk_per_trade", 0.02)
            sl_atr_multiplier = strategy_params.get("sl_atr_multiplier", 1.5)

            data = historical_data.copy()
            data["atr"] = self._calculate_atr(data, 14)

            # Add regime data
            regime_data = volatility_data.get("regime_classification", [])
            if regime_data:
                regime_df = pd.DataFrame(regime_data)
                data["vol_regime"] = regime_df["vol_regime"].values[: len(data)]
            else:
                data["vol_regime"] = "medium"

            position_analysis = {}

            for regime in ["very_low", "low", "medium", "high", "extreme"]:
                regime_subset = data[data["vol_regime"] == regime]
                if len(regime_subset) < 10:
                    continue

                # Calculate position sizes for this regime
                position_sizes = []
                for i, row in regime_subset.iterrows():
                    if pd.notna(row["atr"]) and row["atr"] > 0:
                        # Position size = Risk Amount / Stop Loss Distance
                        stop_distance = row["atr"] * sl_atr_multiplier
                        position_size = (
                            risk_per_trade * 10000
                        ) / stop_distance  # Assuming $10k account
                        position_sizes.append(position_size)

                if position_sizes:
                    position_analysis[regime] = {
                        "avg_position_size": np.mean(position_sizes),
                        "position_size_volatility": np.std(position_sizes),
                        "min_position_size": np.min(position_sizes),
                        "max_position_size": np.max(position_sizes),
                        "position_size_range": np.max(position_sizes)
                        - np.min(position_sizes),
                        "relative_volatility": (
                            np.std(position_sizes) / np.mean(position_sizes)
                            if np.mean(position_sizes) > 0
                            else 0
                        ),
                    }

            # Position sizing stability analysis
            stability_analysis = {
                "position_size_stability": self._calculate_position_size_stability(
                    position_analysis
                ),
                "regime_adaptability": self._assess_regime_adaptability(
                    position_analysis
                ),
                "risk_consistency": self._assess_risk_consistency(position_analysis),
            }

            return {
                "regime_position_analysis": position_analysis,
                "stability_analysis": stability_analysis,
            }

        except Exception as e:
            self.logger.error(f"Position sizing analysis error: {str(e)}")
            return {"error": str(e)}

    def _test_regime_performance(
        self,
        strategy_params: Dict,
        historical_data: pd.DataFrame,
        volatility_data: Dict,
    ) -> Dict:
        """Test strategy performance in different volatility regimes."""
        try:
            data = historical_data.copy()

            # Add regime data
            regime_data = volatility_data.get("regime_classification", [])
            if regime_data:
                regime_df = pd.DataFrame(regime_data)
                data["vol_regime"] = regime_df["vol_regime"].values[: len(data)]
            else:
                return {"error": "No regime data available"}

            regime_performance = {}

            for regime in ["very_low", "low", "medium", "high", "extreme"]:
                regime_subset = data[data["vol_regime"] == regime]
                if (
                    len(regime_subset) < 50
                ):  # Need sufficient data for meaningful backtest
                    continue

                # Run simplified strategy simulation on this regime
                performance = self._simulate_strategy_in_regime(
                    regime_subset, strategy_params
                )

                regime_performance[regime] = {
                    "regime": regime,
                    "data_periods": len(regime_subset),
                    "performance_metrics": performance,
                    "regime_characteristics": {
                        "avg_volatility": regime_subset["close"].pct_change().std()
                        * np.sqrt(252),
                        "price_trend": (
                            regime_subset["close"].iloc[-1]
                            - regime_subset["close"].iloc[0]
                        )
                        / regime_subset["close"].iloc[0],
                        "max_price_swing": (
                            regime_subset["close"].max() - regime_subset["close"].min()
                        )
                        / regime_subset["close"].mean(),
                    },
                }

            # Compare performance across regimes
            performance_comparison = self._compare_regime_performance(
                regime_performance
            )

            return {
                "regime_performance": regime_performance,
                "performance_comparison": performance_comparison,
            }

        except Exception as e:
            self.logger.error(f"Regime performance testing error: {str(e)}")
            return {"error": str(e)}

    def _simulate_strategy_in_regime(
        self, data: pd.DataFrame, strategy_params: Dict
    ) -> Dict:
        """Simulate strategy performance in specific volatility regime."""
        try:
            slow_ma = strategy_params.get("slow_ma", 140)
            fast_ma = strategy_params.get("fast_ma", 40)

            df = data.copy()

            # Calculate indicators
            df["slow_ma"] = (
                df["close"].rolling(window=min(slow_ma, len(df) // 2)).mean()
            )
            df["fast_ma"] = (
                df["close"].rolling(window=min(fast_ma, len(df) // 3)).mean()
            )

            # Generate signals
            df["signal"] = 0
            df.loc[df["fast_ma"] > df["slow_ma"], "signal"] = 1
            df.loc[df["fast_ma"] < df["slow_ma"], "signal"] = -1

            # Count signals and estimate performance
            signals = df["signal"].diff().fillna(0)
            signal_changes = len(signals[signals != 0])

            # Calculate basic metrics
            total_return = (df["close"].iloc[-1] - df["close"].iloc[0]) / df[
                "close"
            ].iloc[0]
            volatility = df["close"].pct_change().std() * np.sqrt(252)

            # Estimate win rate based on signal direction vs price movement
            correct_signals = 0
            total_signals = 0

            for i in range(1, len(df) - 1):
                if df["signal"].iloc[i] != df["signal"].iloc[i - 1]:  # Signal change
                    signal_direction = df["signal"].iloc[i]
                    # Check next period price movement
                    if i + 1 < len(df):
                        price_movement = (
                            df["close"].iloc[i + 1] - df["close"].iloc[i]
                        ) / df["close"].iloc[i]
                        if (signal_direction > 0 and price_movement > 0) or (
                            signal_direction < 0 and price_movement < 0
                        ):
                            correct_signals += 1
                        total_signals += 1

            estimated_win_rate = (
                correct_signals / total_signals if total_signals > 0 else 0.5
            )

            return {
                "estimated_total_return": total_return,
                "volatility": volatility,
                "signal_frequency": signal_changes / len(df),
                "estimated_win_rate": estimated_win_rate,
                "total_signals": total_signals,
                "sharpe_estimate": total_return / volatility if volatility > 0 else 0,
            }

        except Exception as e:
            self.logger.error(f"Regime strategy simulation error: {str(e)}")
            return {"error": str(e)}

    def _analyze_volatility_timing(
        self, historical_data: pd.DataFrame, volatility_data: Dict
    ) -> Dict:
        """Analyze volatility timing and transition patterns."""
        try:
            regime_data = volatility_data.get("regime_classification", [])
            if not regime_data:
                return {"error": "No regime data available"}

            regime_df = pd.DataFrame(regime_data)

            # Analyze regime transitions
            regime_series = regime_df["vol_regime"]
            transitions = []

            for i in range(1, len(regime_series)):
                if regime_series.iloc[i] != regime_series.iloc[i - 1]:
                    transitions.append(
                        {
                            "from": regime_series.iloc[i - 1],
                            "to": regime_series.iloc[i],
                            "period": i,
                        }
                    )

            # Calculate transition probabilities
            transition_matrix = {}
            regimes = ["very_low", "low", "medium", "high", "extreme"]

            for from_regime in regimes:
                transition_matrix[from_regime] = {}
                from_transitions = [t for t in transitions if t["from"] == from_regime]

                for to_regime in regimes:
                    to_count = len(
                        [t for t in from_transitions if t["to"] == to_regime]
                    )
                    transition_matrix[from_regime][to_regime] = (
                        to_count / len(from_transitions) if from_transitions else 0
                    )

            # Analyze regime persistence
            regime_durations = {}
            current_regime = regime_series.iloc[0]
            current_duration = 1

            for i in range(1, len(regime_series)):
                if regime_series.iloc[i] == current_regime:
                    current_duration += 1
                else:
                    if current_regime not in regime_durations:
                        regime_durations[current_regime] = []
                    regime_durations[current_regime].append(current_duration)
                    current_regime = regime_series.iloc[i]
                    current_duration = 1

            # Calculate persistence statistics
            persistence_stats = {}
            for regime, durations in regime_durations.items():
                if durations:
                    persistence_stats[regime] = {
                        "avg_duration": np.mean(durations),
                        "max_duration": np.max(durations),
                        "min_duration": np.min(durations),
                        "duration_volatility": np.std(durations),
                    }

            return {
                "transition_analysis": {
                    "total_transitions": len(transitions),
                    "transition_frequency": len(transitions) / len(regime_series),
                    "transition_matrix": transition_matrix,
                },
                "regime_persistence": persistence_stats,
                "volatility_clustering": self._analyze_volatility_clustering(regime_df),
            }

        except Exception as e:
            self.logger.error(f"Volatility timing analysis error: {str(e)}")
            return {"error": str(e)}

    def _analyze_volatility_clustering(self, regime_df: pd.DataFrame) -> Dict:
        """Analyze volatility clustering patterns."""
        try:
            vol_values = regime_df["rolling_vol"].dropna()

            # Calculate autocorrelation of volatility
            autocorr_1 = vol_values.autocorr(lag=1)
            autocorr_5 = vol_values.autocorr(lag=5)
            autocorr_10 = vol_values.autocorr(lag=10)

            # Identify volatility clusters
            high_vol_threshold = vol_values.quantile(0.8)
            high_vol_periods = vol_values > high_vol_threshold

            # Calculate cluster statistics
            cluster_lengths = []
            in_cluster = False
            current_cluster_length = 0

            for is_high_vol in high_vol_periods:
                if is_high_vol:
                    if not in_cluster:
                        in_cluster = True
                        current_cluster_length = 1
                    else:
                        current_cluster_length += 1
                else:
                    if in_cluster:
                        cluster_lengths.append(current_cluster_length)
                        in_cluster = False
                        current_cluster_length = 0

            return {
                "autocorrelation": {
                    "lag_1": float(autocorr_1) if not pd.isna(autocorr_1) else 0.0,
                    "lag_5": float(autocorr_5) if not pd.isna(autocorr_5) else 0.0,
                    "lag_10": float(autocorr_10) if not pd.isna(autocorr_10) else 0.0,
                },
                "clustering_statistics": {
                    "avg_cluster_length": (
                        np.mean(cluster_lengths) if cluster_lengths else 0
                    ),
                    "max_cluster_length": (
                        np.max(cluster_lengths) if cluster_lengths else 0
                    ),
                    "total_clusters": len(cluster_lengths),
                    "clustering_tendency": (
                        "HIGH"
                        if autocorr_1 > 0.3
                        else "MODERATE" if autocorr_1 > 0.1 else "LOW"
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Volatility clustering analysis error: {str(e)}")
            return {"error": str(e)}

    def _generate_volatility_recommendations(self, analysis_results: Dict) -> List[str]:
        """Generate recommendations based on volatility analysis."""
        try:
            recommendations = []

            # ATR effectiveness recommendations
            atr_analysis = analysis_results.get("atr_effectiveness", {}).get(
                "overall_assessment", {}
            )
            atr_stability = atr_analysis.get("atr_stability_across_regimes", {})

            if atr_stability.get("stability_score", 0.5) < 0.3:
                recommendations.append(
                    "LOW ATR STABILITY: Consider using adaptive ATR multipliers that adjust based on volatility regime."
                )

            # Position sizing recommendations
            position_analysis = analysis_results.get(
                "position_sizing_analysis", {}
            ).get("stability_analysis", {})
            if (
                position_analysis.get("position_size_stability", {}).get(
                    "is_stable", True
                )
                == False
            ):
                recommendations.append(
                    "POSITION SIZE INSTABILITY: Implement maximum position size limits to prevent excessive exposure during low volatility periods."
                )

            # Regime performance recommendations
            regime_perf = analysis_results.get("regime_performance", {}).get(
                "performance_comparison", {}
            )
            worst_regime = regime_perf.get("worst_performing_regime", "")
            if worst_regime:
                recommendations.append(
                    f"POOR REGIME PERFORMANCE: Strategy performs poorly during {worst_regime} volatility. Consider disabling trading or reducing position sizes in this regime."
                )

            # Volatility timing recommendations
            timing_analysis = analysis_results.get("volatility_timing", {})
            clustering = timing_analysis.get("volatility_clustering", {}).get(
                "clustering_statistics", {}
            )
            if clustering.get("clustering_tendency") == "HIGH":
                recommendations.append(
                    "HIGH VOLATILITY CLUSTERING: Implement dynamic risk management that reduces exposure after high volatility periods."
                )

            # General recommendations
            recommendations.extend(
                [
                    "Monitor volatility regime changes and adjust strategy parameters accordingly.",
                    "Consider implementing volatility filters to avoid trading during extreme conditions.",
                    "Use rolling volatility measures to adapt position sizing in real-time.",
                    "Backtest strategy performance across different volatility environments regularly.",
                ]
            )

            return recommendations

        except Exception as e:
            self.logger.error(f"Volatility recommendations generation error: {str(e)}")
            return [f"Error generating recommendations: {str(e)}"]

    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        try:
            high = df["high"]
            low = df["low"]
            close = df["close"].shift(1)

            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()

            return atr
        except Exception as e:
            self.logger.error(f"ATR calculation error: {str(e)}")
            return pd.Series(index=df.index)

    def _calculate_atr_stability(self, atr_analysis: Dict) -> Dict:
        """Calculate ATR stability across regimes."""
        try:
            atr_means = []
            for regime, data in atr_analysis.items():
                if "atr_statistics" in data:
                    atr_means.append(data["atr_statistics"].get("avg_atr_pct", 0))

            if len(atr_means) < 2:
                return {"stability_score": 1.0, "is_stable": True}

            atr_cv = (
                np.std(atr_means) / np.mean(atr_means)
                if np.mean(atr_means) > 0
                else 1.0
            )
            stability_score = max(0.0, 1.0 - float(atr_cv))

            return {
                "stability_score": stability_score,
                "coefficient_of_variation": atr_cv,
                "is_stable": stability_score > 0.5,
            }

        except Exception as e:
            return {"stability_score": 0.5, "is_stable": False}

    def _recommend_atr_adjustments(self, atr_analysis: Dict) -> Dict:
        """Recommend ATR adjustments based on analysis."""
        try:
            recommendations = {}

            for regime, data in atr_analysis.items():
                if "atr_statistics" in data and "stop_loss_effectiveness" in data:
                    effectiveness = data["stop_loss_effectiveness"].get(
                        "effectiveness_score", 0
                    )

                    if effectiveness < -0.2:  # More losses than wins
                        recommendations[regime] = {
                            "action": "TIGHTEN_STOPS",
                            "suggested_multiplier_change": -0.2,
                            "reason": "High stop loss hit rate",
                        }
                    elif effectiveness > 0.3:  # Much better performance
                        recommendations[regime] = {
                            "action": "LOOSEN_STOPS",
                            "suggested_multiplier_change": 0.2,
                            "reason": "Low stop loss hit rate, room for improvement",
                        }
                    else:
                        recommendations[regime] = {
                            "action": "MAINTAIN",
                            "suggested_multiplier_change": 0.0,
                            "reason": "Balanced performance",
                        }

            return recommendations

        except Exception as e:
            return {}

    def _assess_atr_risk(self, atr_analysis: Dict) -> Dict:
        """Assess overall ATR-based risk."""
        try:
            high_risk_regimes = 0
            total_regimes = 0

            for regime, data in atr_analysis.items():
                if "stop_loss_effectiveness" in data:
                    total_regimes += 1
                    effectiveness = data["stop_loss_effectiveness"].get(
                        "effectiveness_score", 0
                    )
                    if effectiveness < -0.3:
                        high_risk_regimes += 1

            risk_ratio = high_risk_regimes / total_regimes if total_regimes > 0 else 0

            if risk_ratio > 0.5:
                risk_level = "HIGH"
            elif risk_ratio > 0.2:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            return {
                "overall_risk_level": risk_level,
                "high_risk_regimes": high_risk_regimes,
                "total_regimes_analyzed": total_regimes,
                "risk_ratio": risk_ratio,
            }

        except Exception as e:
            return {"overall_risk_level": "UNKNOWN"}

    def _calculate_position_size_stability(self, position_analysis: Dict) -> Dict:
        """Calculate position size stability across regimes."""
        try:
            relative_volatilities = []
            for regime, data in position_analysis.items():
                rel_vol = data.get("relative_volatility", 0)
                relative_volatilities.append(rel_vol)

            if not relative_volatilities:
                return {"is_stable": True, "stability_score": 1.0}

            avg_rel_vol = np.mean(relative_volatilities)
            stability_score = max(0.0, 1.0 - float(avg_rel_vol))

            return {
                "is_stable": stability_score > 0.5,
                "stability_score": stability_score,
                "average_relative_volatility": avg_rel_vol,
            }

        except Exception as e:
            return {"is_stable": False, "stability_score": 0.0}

    def _assess_regime_adaptability(self, position_analysis: Dict) -> Dict:
        """Assess how well position sizing adapts to different regimes."""
        try:
            position_ranges = []
            for regime, data in position_analysis.items():
                pos_range = data.get("position_size_range", 0)
                position_ranges.append(pos_range)

            if not position_ranges:
                return {"adaptability": "UNKNOWN"}

            max_range = max(position_ranges)
            adaptability = (
                "HIGH" if max_range > 1000 else "MODERATE" if max_range > 500 else "LOW"
            )

            return {
                "adaptability": adaptability,
                "max_position_range": max_range,
                "regime_sensitivity": "GOOD" if adaptability == "HIGH" else "MODERATE",
            }

        except Exception as e:
            return {"adaptability": "UNKNOWN"}

    def _assess_risk_consistency(self, position_analysis: Dict) -> Dict:
        """Assess risk consistency across regimes."""
        try:
            # Risk consistency is good if position sizes adjust appropriately
            # (larger in low vol, smaller in high vol)
            regime_order = ["very_low", "low", "medium", "high", "extreme"]
            position_sizes = []

            for regime in regime_order:
                if regime in position_analysis:
                    avg_size = position_analysis[regime].get("avg_position_size", 0)
                    position_sizes.append(avg_size)

            if len(position_sizes) < 3:
                return {"consistency": "INSUFFICIENT_DATA"}

            # Check if position sizes generally decrease with higher volatility
            decreasing_trend = all(
                position_sizes[i] >= position_sizes[i + 1]
                for i in range(len(position_sizes) - 1)
            )

            return {
                "consistency": "GOOD" if decreasing_trend else "NEEDS_IMPROVEMENT",
                "follows_expected_pattern": decreasing_trend,
                "position_size_progression": position_sizes,
            }

        except Exception as e:
            return {"consistency": "UNKNOWN"}

    def _compare_regime_performance(self, regime_performance: Dict) -> Dict:
        """Compare performance across different volatility regimes."""
        try:
            performance_scores = {}

            for regime, data in regime_performance.items():
                if "performance_metrics" in data:
                    metrics = data["performance_metrics"]
                    # Simple performance score based on return and win rate
                    return_score = metrics.get("estimated_total_return", 0) * 100
                    win_rate_score = (
                        metrics.get("estimated_win_rate", 0.5) - 0.5
                    ) * 200
                    performance_scores[regime] = return_score + win_rate_score

            if not performance_scores:
                return {"error": "No performance data available"}

            best_regime = max(
                performance_scores.keys(), key=lambda k: performance_scores[k]
            )
            worst_regime = min(
                performance_scores.keys(), key=lambda k: performance_scores[k]
            )

            return {
                "best_performing_regime": best_regime,
                "worst_performing_regime": worst_regime,
                "performance_scores": performance_scores,
                "performance_spread": performance_scores[best_regime]
                - performance_scores[worst_regime],
            }

        except Exception as e:
            return {"error": str(e)}

    def save_volatility_analysis(self, analysis_data: Dict, strategy_name: str) -> str:
        """
        Save volatility impact analysis results to file.

        Args:
            analysis_data: Analysis results
            strategy_name: Name of the strategy

        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"volatility_analysis_{strategy_name}_{timestamp}.json"

            # Create reports directory if it doesn't exist
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)

            filepath = reports_dir / filename

            with open(filepath, "w") as f:
                json.dump(analysis_data, f, indent=2)

            self.logger.info(f"Volatility analysis saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Error saving volatility analysis: {str(e)}")
            return ""
