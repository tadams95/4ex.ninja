"""
Max Loss Analyzer

This module provides analysis of maximum potential losses and worst-case scenarios
for trading strategies. It focuses on stress testing and crisis period analysis.
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


class MaxLossAnalyzer:
    """
    Analyzer for maximum loss scenarios and stress testing.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.crisis_periods = self._define_crisis_periods()

    def _define_crisis_periods(self) -> List[Dict]:
        """Define known financial crisis periods for stress testing."""
        return [
            {
                "name": "COVID-19 Market Crash",
                "start": "2020-02-20",
                "end": "2020-04-30",
                "description": "Pandemic-induced market volatility",
            },
            {
                "name": "Brexit Referendum",
                "start": "2016-06-23",
                "end": "2016-07-15",
                "description": "Brexit vote market reaction",
            },
            {
                "name": "Flash Crash",
                "start": "2015-01-15",
                "end": "2015-01-30",
                "description": "Swiss Franc flash crash",
            },
            {
                "name": "High Volatility Period",
                "start": "2022-02-01",
                "end": "2022-04-30",
                "description": "Ukraine conflict market impact",
            },
        ]

    def analyze_maximum_loss_scenarios(
        self, strategy_params: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """
        Analyze maximum potential losses under various market conditions.

        Args:
            strategy_params: Strategy parameters
            historical_data: Historical price data

        Returns:
            Dictionary containing maximum loss analysis
        """
        try:
            self.logger.info("Starting maximum loss scenario analysis")

            analysis_results = {
                "worst_case_scenarios": {},
                "stress_test_results": {},
                "crisis_period_analysis": {},
                "maximum_consecutive_losses": {},
                "portfolio_impact": {},
                "risk_recommendations": [],
            }

            # Analyze worst-case single trade scenarios
            analysis_results["worst_case_scenarios"] = self._analyze_worst_case_trades(
                strategy_params, historical_data
            )

            # Stress test with extreme market conditions
            analysis_results["stress_test_results"] = self._run_stress_tests(
                strategy_params, historical_data
            )

            # Analyze performance during known crisis periods
            analysis_results["crisis_period_analysis"] = self._analyze_crisis_periods(
                strategy_params, historical_data
            )

            # Analyze consecutive losing streaks
            analysis_results["maximum_consecutive_losses"] = (
                self._analyze_consecutive_losses(strategy_params, historical_data)
            )

            # Calculate portfolio-level impact
            analysis_results["portfolio_impact"] = self._calculate_portfolio_impact(
                analysis_results
            )

            # Generate risk recommendations
            analysis_results["risk_recommendations"] = (
                self._generate_risk_recommendations(analysis_results)
            )

            self.logger.info("Maximum loss analysis completed")
            return analysis_results

        except Exception as e:
            self.logger.error(f"Maximum loss analysis error: {str(e)}")
            return {"error": str(e)}

    def _analyze_worst_case_trades(
        self, strategy_params: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """Analyze worst-case single trade scenarios."""
        try:
            # Extract parameters
            sl_atr_multiplier = strategy_params.get("sl_atr_multiplier", 1.5)
            risk_per_trade = strategy_params.get("risk_per_trade", 0.02)
            atr_period = strategy_params.get("atr_period", 14)

            # Calculate ATR for the dataset
            historical_data = historical_data.copy()
            historical_data["atr"] = self._calculate_atr(historical_data, atr_period)

            # Find periods of highest volatility (potential worst trades)
            valid_atr = historical_data["atr"].dropna()
            if valid_atr.empty:
                return {"error": "No valid ATR data"}

            max_atr = valid_atr.max()
            min_atr = valid_atr.min()
            avg_atr = valid_atr.mean()
            atr_95_percentile = valid_atr.quantile(0.95)

            # Calculate worst-case loss scenarios
            worst_case_loss_pips = max_atr * sl_atr_multiplier
            typical_loss_pips = avg_atr * sl_atr_multiplier
            extreme_loss_pips = atr_95_percentile * sl_atr_multiplier

            # Convert to account percentage impact
            # Assuming risk_per_trade represents the maximum intended risk
            worst_case_account_impact = risk_per_trade  # This is the designed max loss

            # Calculate gap risk scenarios (when price gaps beyond stop loss)
            gap_risk_multiplier = 2.0  # Assume gaps could be 2x normal ATR
            gap_scenario_loss = worst_case_loss_pips * gap_risk_multiplier
            gap_account_impact = risk_per_trade * gap_risk_multiplier

            return {
                "atr_statistics": {
                    "max_atr": float(max_atr),
                    "min_atr": float(min_atr),
                    "avg_atr": float(avg_atr),
                    "atr_95_percentile": float(atr_95_percentile),
                },
                "loss_scenarios": {
                    "typical_loss_pips": float(typical_loss_pips),
                    "worst_case_loss_pips": float(worst_case_loss_pips),
                    "extreme_loss_pips": float(extreme_loss_pips),
                    "gap_scenario_loss_pips": float(gap_scenario_loss),
                },
                "account_impact": {
                    "designed_max_loss_pct": float(risk_per_trade * 100),
                    "gap_risk_loss_pct": float(gap_account_impact * 100),
                    "theoretical_max_single_trade_loss_pct": float(
                        gap_account_impact * 100
                    ),
                },
                "risk_assessment": {
                    "stop_loss_effectiveness": (
                        "HIGH" if sl_atr_multiplier >= 1.5 else "MODERATE"
                    ),
                    "gap_risk_level": (
                        "HIGH" if gap_account_impact > 0.05 else "MODERATE"
                    ),
                    "position_sizing_safety": (
                        "GOOD" if risk_per_trade <= 0.02 else "RISKY"
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Worst case trade analysis error: {str(e)}")
            return {"error": str(e)}

    def _run_stress_tests(
        self, strategy_params: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """Run stress tests with extreme market conditions."""
        try:
            stress_scenarios = [
                {
                    "name": "Extreme Volatility",
                    "volatility_multiplier": 3.0,
                    "trend_strength": 0.5,
                },
                {
                    "name": "High Trend Market",
                    "volatility_multiplier": 1.5,
                    "trend_strength": 2.0,
                },
                {
                    "name": "Choppy Market",
                    "volatility_multiplier": 2.0,
                    "trend_strength": 0.1,
                },
                {
                    "name": "Flash Crash",
                    "volatility_multiplier": 5.0,
                    "trend_strength": 3.0,
                },
            ]

            stress_results = {}

            for scenario in stress_scenarios:
                self.logger.info(f"Running stress test: {scenario['name']}")

                # Modify historical data based on stress scenario
                stressed_data = self._apply_stress_scenario(historical_data, scenario)

                # Run strategy simulation on stressed data
                simulation_result = self._simulate_strategy_on_stressed_data(
                    stressed_data, strategy_params
                )

                stress_results[scenario["name"]] = {
                    "scenario_parameters": scenario,
                    "simulation_results": simulation_result,
                    "max_drawdown": simulation_result.get("max_drawdown", 0),
                    "total_return": simulation_result.get("total_return", 0),
                    "worst_losing_streak": simulation_result.get(
                        "worst_losing_streak", 0
                    ),
                    "stress_impact_score": self._calculate_stress_impact_score(
                        simulation_result
                    ),
                }

            return stress_results

        except Exception as e:
            self.logger.error(f"Stress test error: {str(e)}")
            return {"error": str(e)}

    def _apply_stress_scenario(
        self, historical_data: pd.DataFrame, scenario: Dict
    ) -> pd.DataFrame:
        """Apply stress scenario modifications to historical data."""
        try:
            data = historical_data.copy()
            volatility_mult = scenario["volatility_multiplier"]
            trend_strength = scenario["trend_strength"]

            # Calculate base returns
            data["returns"] = data["close"].pct_change()

            # Apply volatility stress
            data["stressed_returns"] = data["returns"] * volatility_mult

            # Apply trend stress
            if trend_strength > 1.0:
                # Amplify trends
                data["trend_component"] = data["returns"].rolling(window=10).mean() * (
                    trend_strength - 1.0
                )
                data["stressed_returns"] += data["trend_component"]
            elif trend_strength < 1.0:
                # Reduce trends (more choppy)
                data["stressed_returns"] *= trend_strength

            # Reconstruct price series
            initial_price = data["close"].iloc[0]
            stressed_prices = [initial_price]

            for ret in data["stressed_returns"].fillna(0):
                next_price = stressed_prices[-1] * (1 + ret)
                stressed_prices.append(next_price)

            # Update OHLC data
            data["close"] = stressed_prices[1:]
            data["high"] = data["close"] * 1.005  # Approximate high
            data["low"] = data["close"] * 0.995  # Approximate low
            data["open"] = data["close"].shift(1).fillna(data["close"].iloc[0])

            return data[["open", "high", "low", "close"]].dropna()

        except Exception as e:
            self.logger.error(f"Stress scenario application error: {str(e)}")
            return historical_data

    def _simulate_strategy_on_stressed_data(
        self, stressed_data: pd.DataFrame, strategy_params: Dict
    ) -> Dict:
        """Simulate strategy performance on stress-tested data."""
        try:
            # Extract strategy parameters
            slow_ma = strategy_params.get("slow_ma", 140)
            fast_ma = strategy_params.get("fast_ma", 40)
            atr_period = strategy_params.get("atr_period", 14)
            sl_atr_multiplier = strategy_params.get("sl_atr_multiplier", 1.5)
            tp_atr_multiplier = strategy_params.get("tp_atr_multiplier", 2.0)
            risk_per_trade = strategy_params.get("risk_per_trade", 0.02)

            # Calculate indicators
            df = stressed_data.copy()
            df["slow_ma"] = df["close"].rolling(window=slow_ma).mean()
            df["fast_ma"] = df["close"].rolling(window=fast_ma).mean()
            df["atr"] = self._calculate_atr(df, atr_period)

            # Generate signals
            df["signal"] = 0
            df.loc[df["fast_ma"] > df["slow_ma"], "signal"] = 1
            df.loc[df["fast_ma"] < df["slow_ma"], "signal"] = -1

            # Simulate trades
            trades = []
            equity_curve = [10000.0]
            current_position = 0
            losing_streak = 0
            max_losing_streak = 0

            for i in range(1, len(df)):
                current_equity = equity_curve[-1]
                current_price = df["close"].iloc[i]
                signal = df["signal"].iloc[i]
                atr = df["atr"].iloc[i]

                # Simple signal-based trading simulation
                if current_position == 0 and signal != 0 and not pd.isna(atr):
                    # Enter position
                    current_position = signal
                    entry_price = current_price

                elif current_position != 0 and signal != current_position:
                    # Exit position
                    if current_position == 1:
                        pnl_pct = (current_price - entry_price) / entry_price
                    else:
                        pnl_pct = (entry_price - current_price) / entry_price

                    position_size = (
                        current_equity * risk_per_trade / 0.01
                    )  # Simplified position sizing
                    trade_pnl = position_size * pnl_pct
                    new_equity = current_equity + trade_pnl

                    trades.append(
                        {
                            "entry_price": entry_price,
                            "exit_price": current_price,
                            "pnl_pct": pnl_pct,
                            "pnl_amount": trade_pnl,
                        }
                    )

                    # Track losing streaks
                    if trade_pnl < 0:
                        losing_streak += 1
                        max_losing_streak = max(max_losing_streak, losing_streak)
                    else:
                        losing_streak = 0

                    equity_curve.append(new_equity)
                    current_position = 0
                else:
                    equity_curve.append(current_equity)

            # Calculate metrics
            total_return = (
                (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
                if len(equity_curve) > 1
                else 0
            )
            max_drawdown = self._calculate_max_drawdown(equity_curve)

            return {
                "total_trades": len(trades),
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "worst_losing_streak": max_losing_streak,
                "final_equity": equity_curve[-1] if equity_curve else 10000.0,
                "equity_curve": equity_curve,
            }

        except Exception as e:
            self.logger.error(f"Stressed data simulation error: {str(e)}")
            return {"error": str(e)}

    def _analyze_crisis_periods(
        self, strategy_params: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """Analyze strategy performance during known crisis periods."""
        try:
            crisis_analysis = {}

            # Ensure we have datetime index
            if "timestamp" in historical_data.columns:
                historical_data["datetime"] = pd.to_datetime(
                    historical_data["timestamp"]
                )
            elif historical_data.index.name == "timestamp" or isinstance(
                historical_data.index, pd.DatetimeIndex
            ):
                historical_data["datetime"] = historical_data.index
            else:
                # If no timestamp, create a synthetic one for demonstration
                historical_data["datetime"] = pd.date_range(
                    start="2015-01-01", periods=len(historical_data), freq="H"
                )

            for crisis in self.crisis_periods:
                try:
                    start_date = pd.to_datetime(crisis["start"])
                    end_date = pd.to_datetime(crisis["end"])

                    # Filter data for crisis period
                    crisis_data = historical_data[
                        (historical_data["datetime"] >= start_date)
                        & (historical_data["datetime"] <= end_date)
                    ].copy()

                    if len(crisis_data) < 10:  # Need minimum data points
                        crisis_analysis[crisis["name"]] = {
                            "status": "INSUFFICIENT_DATA",
                            "data_points": len(crisis_data),
                        }
                        continue

                    # Simulate strategy during crisis
                    crisis_simulation = self._simulate_strategy_on_stressed_data(
                        crisis_data[["open", "high", "low", "close"]], strategy_params
                    )

                    crisis_analysis[crisis["name"]] = {
                        "period": f"{crisis['start']} to {crisis['end']}",
                        "description": crisis["description"],
                        "data_points": len(crisis_data),
                        "performance": crisis_simulation,
                        "volatility_during_period": crisis_data["close"]
                        .pct_change()
                        .std()
                        * np.sqrt(252),
                        "max_price_movement": {
                            "high": crisis_data["close"].max(),
                            "low": crisis_data["close"].min(),
                            "range_pct": (
                                crisis_data["close"].max() - crisis_data["close"].min()
                            )
                            / crisis_data["close"].mean(),
                        },
                    }

                except Exception as e:
                    crisis_analysis[crisis["name"]] = {
                        "status": "ANALYSIS_FAILED",
                        "error": str(e),
                    }

            return crisis_analysis

        except Exception as e:
            self.logger.error(f"Crisis period analysis error: {str(e)}")
            return {"error": str(e)}

    def _analyze_consecutive_losses(
        self, strategy_params: Dict, historical_data: pd.DataFrame
    ) -> Dict:
        """Analyze maximum consecutive losing streaks."""
        try:
            # Run a simplified simulation to get trade results
            simulation = self._simulate_strategy_on_stressed_data(
                historical_data, strategy_params
            )

            if "error" in simulation:
                return simulation

            # Simulate multiple scenarios to find worst consecutive losses
            scenarios = []
            for i in range(10):  # Run 10 different starting points
                start_idx = min(i * 50, len(historical_data) - 100)
                end_idx = min(start_idx + 200, len(historical_data))

                if end_idx - start_idx < 50:
                    continue

                scenario_data = historical_data.iloc[start_idx:end_idx].copy()
                scenario_sim = self._simulate_strategy_on_stressed_data(
                    scenario_data, strategy_params
                )
                scenarios.append(scenario_sim)

            # Extract losing streak statistics
            max_losing_streaks = [
                s.get("worst_losing_streak", 0)
                for s in scenarios
                if "worst_losing_streak" in s
            ]

            if not max_losing_streaks:
                max_losing_streaks = [0]

            # Calculate potential cumulative loss from consecutive losses
            risk_per_trade = strategy_params.get("risk_per_trade", 0.02)
            worst_streak = max(max_losing_streaks)

            # Calculate compound loss (assuming losses don't compound exactly due to position sizing)
            cumulative_loss_linear = worst_streak * risk_per_trade
            cumulative_loss_compound = 1 - (1 - risk_per_trade) ** worst_streak

            return {
                "maximum_consecutive_losses": int(worst_streak),
                "average_consecutive_losses": float(np.mean(max_losing_streaks)),
                "loss_impact_analysis": {
                    "linear_cumulative_loss_pct": float(cumulative_loss_linear * 100),
                    "compound_cumulative_loss_pct": float(
                        cumulative_loss_compound * 100
                    ),
                    "account_survival_probability": float(1 - cumulative_loss_compound),
                },
                "risk_assessment": {
                    "streak_risk_level": (
                        "HIGH"
                        if worst_streak > 10
                        else "MODERATE" if worst_streak > 5 else "LOW"
                    ),
                    "recovery_difficulty": (
                        "HIGH"
                        if cumulative_loss_compound > 0.2
                        else "MODERATE" if cumulative_loss_compound > 0.1 else "LOW"
                    ),
                },
                "scenario_statistics": {
                    "scenarios_analyzed": len(scenarios),
                    "streak_distribution": {
                        "min": int(min(max_losing_streaks)),
                        "max": int(max(max_losing_streaks)),
                        "median": float(np.median(max_losing_streaks)),
                        "std": float(np.std(max_losing_streaks)),
                    },
                },
            }

        except Exception as e:
            self.logger.error(f"Consecutive losses analysis error: {str(e)}")
            return {"error": str(e)}

    def _calculate_portfolio_impact(self, analysis_results: Dict) -> Dict:
        """Calculate portfolio-level impact of maximum loss scenarios."""
        try:
            # Extract key metrics from analysis
            worst_case = analysis_results.get("worst_case_scenarios", {})
            stress_tests = analysis_results.get("stress_test_results", {})
            consecutive_losses = analysis_results.get("maximum_consecutive_losses", {})

            # Calculate portfolio impact metrics
            single_trade_max_loss = worst_case.get("account_impact", {}).get(
                "gap_risk_loss_pct", 4.0
            )
            consecutive_loss_impact = consecutive_losses.get(
                "loss_impact_analysis", {}
            ).get("compound_cumulative_loss_pct", 10.0)

            # Find worst stress test result
            worst_stress_drawdown = 0.0
            for test_name, test_results in stress_tests.items():
                if isinstance(test_results, dict) and "max_drawdown" in test_results:
                    drawdown = test_results["max_drawdown"]
                    if drawdown > worst_stress_drawdown:
                        worst_stress_drawdown = drawdown

            worst_stress_drawdown_pct = worst_stress_drawdown * 100

            # Portfolio-level assessment
            portfolio_impact = {
                "maximum_single_event_loss_pct": float(single_trade_max_loss),
                "maximum_consecutive_loss_pct": float(consecutive_loss_impact),
                "worst_stress_test_drawdown_pct": float(worst_stress_drawdown_pct),
                "theoretical_maximum_loss_pct": float(
                    max(
                        single_trade_max_loss,
                        consecutive_loss_impact,
                        worst_stress_drawdown_pct,
                    )
                ),
                "portfolio_risk_levels": {
                    "conservative_allocation": "5-10% of portfolio",
                    "moderate_allocation": "10-20% of portfolio",
                    "aggressive_allocation": "20%+ of portfolio",
                },
                "capital_requirements": {
                    "minimum_account_size_conservative": "Account should be 10x the maximum loss amount",
                    "minimum_account_size_moderate": "Account should be 5x the maximum loss amount",
                    "stop_trading_threshold": "Consider stopping if account drops below 3x maximum loss amount",
                },
            }

            # Risk categorization
            max_loss = portfolio_impact["theoretical_maximum_loss_pct"]
            if max_loss > 30:
                portfolio_impact["overall_risk_category"] = "VERY_HIGH"
            elif max_loss > 20:
                portfolio_impact["overall_risk_category"] = "HIGH"
            elif max_loss > 10:
                portfolio_impact["overall_risk_category"] = "MODERATE"
            else:
                portfolio_impact["overall_risk_category"] = "LOW"

            return portfolio_impact

        except Exception as e:
            self.logger.error(f"Portfolio impact calculation error: {str(e)}")
            return {"error": str(e)}

    def _generate_risk_recommendations(self, analysis_results: Dict) -> List[str]:
        """Generate actionable risk management recommendations."""
        try:
            recommendations = []

            # Analyze results and generate recommendations
            worst_case = analysis_results.get("worst_case_scenarios", {})
            portfolio_impact = analysis_results.get("portfolio_impact", {})
            consecutive_losses = analysis_results.get("maximum_consecutive_losses", {})

            # Single trade risk recommendations
            gap_risk = worst_case.get("account_impact", {}).get("gap_risk_loss_pct", 0)
            if gap_risk > 5:
                recommendations.append(
                    f"HIGH PRIORITY: Gap risk of {gap_risk:.1f}% exceeds 5%. Consider tighter stop losses or smaller position sizes."
                )

            # Consecutive loss recommendations
            max_streak = consecutive_losses.get("maximum_consecutive_losses", 0)
            if max_streak > 8:
                recommendations.append(
                    f"RISK WARNING: Maximum consecutive losses of {max_streak} could severely impact account. Consider implementing daily/weekly loss limits."
                )

            cumulative_loss = consecutive_losses.get("loss_impact_analysis", {}).get(
                "compound_cumulative_loss_pct", 0
            )
            if cumulative_loss > 15:
                recommendations.append(
                    f"CRITICAL: Potential cumulative loss of {cumulative_loss:.1f}% from consecutive losses. Implement position size reduction after 3-4 consecutive losses."
                )

            # Portfolio allocation recommendations
            overall_risk = portfolio_impact.get("overall_risk_category", "UNKNOWN")
            if overall_risk == "VERY_HIGH":
                recommendations.append(
                    "URGENT: Overall risk category is VERY HIGH. Reduce position sizes by 50% or limit allocation to 5% of total portfolio."
                )
            elif overall_risk == "HIGH":
                recommendations.append(
                    "WARNING: High risk detected. Limit allocation to 10-15% of total portfolio and implement strict daily loss limits."
                )

            # Stress test recommendations
            stress_tests = analysis_results.get("stress_test_results", {})
            for test_name, results in stress_tests.items():
                if isinstance(results, dict) and "max_drawdown" in results:
                    if results["max_drawdown"] > 0.25:  # 25% drawdown
                        recommendations.append(
                            f"STRESS TEST ALERT: {test_name} scenario shows {results['max_drawdown']*100:.1f}% drawdown. Strategy may not be robust during {test_name.lower()} conditions."
                        )

            # General recommendations
            recommendations.extend(
                [
                    "Implement a maximum daily loss limit of 5-10% of account balance.",
                    "Use dynamic position sizing that reduces after consecutive losses.",
                    "Monitor correlation with other trading strategies to avoid concentration risk.",
                    "Consider implementing a 'circuit breaker' that stops trading after significant losses.",
                    "Regularly update risk parameters based on changing market conditions.",
                ]
            )

            return recommendations

        except Exception as e:
            self.logger.error(f"Risk recommendations generation error: {str(e)}")
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

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown from equity curve."""
        try:
            if not equity_curve or len(equity_curve) < 2:
                return 0.0

            peak = equity_curve[0]
            max_drawdown = 0.0

            for value in equity_curve:
                if value > peak:
                    peak = value

                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            return max_drawdown

        except Exception as e:
            self.logger.error(f"Max drawdown calculation error: {str(e)}")
            return 0.0

    def _calculate_stress_impact_score(self, simulation_result: Dict) -> float:
        """Calculate a stress impact score (0-100, higher = worse impact)."""
        try:
            max_drawdown = simulation_result.get("max_drawdown", 0)
            total_return = simulation_result.get("total_return", 0)
            losing_streak = simulation_result.get("worst_losing_streak", 0)

            # Combine metrics into a stress score
            drawdown_score = min(max_drawdown * 100, 50)  # Cap at 50 points
            return_score = max(-total_return * 100, 0)  # Negative returns add to score
            streak_score = min(losing_streak * 2, 30)  # Cap at 30 points

            total_score = drawdown_score + return_score + streak_score
            return min(total_score, 100)  # Cap at 100

        except Exception as e:
            return 50.0  # Default moderate score on error

    def save_max_loss_analysis(self, analysis_data: Dict, strategy_name: str) -> str:
        """
        Save maximum loss analysis results to file.

        Args:
            analysis_data: Analysis results
            strategy_name: Name of the strategy

        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"max_loss_analysis_{strategy_name}_{timestamp}.json"

            # Create reports directory if it doesn't exist
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)

            filepath = reports_dir / filename

            with open(filepath, "w") as f:
                json.dump(analysis_data, f, indent=2)

            self.logger.info(f"Max loss analysis saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Error saving max loss analysis: {str(e)}")
            return ""
