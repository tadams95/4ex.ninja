"""
Risk Calculator

This module provides comprehensive risk assessment capabilities including:
- Value-at-Risk (VaR) calculations
- Monte Carlo simulations for worst-case scenarios
- Maximum drawdown analysis
- Position sizing validation
- Risk-adjusted performance metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

# Note: scipy import removed for compatibility - using numpy alternatives

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class RiskCalculator:
    """
    Comprehensive risk calculator for trading strategies.
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize risk calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculations
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)

    def calculate_max_drawdown_potential(
        self,
        strategy_params: Dict,
        historical_data: pd.DataFrame,
        n_simulations: int = 1000,
    ) -> Dict:
        """
        Analyze worst-case scenarios and calculate value-at-risk metrics.

        Args:
            strategy_params: Strategy parameters (MA periods, ATR multipliers, etc.)
            historical_data: Historical price data for simulation
            n_simulations: Number of Monte Carlo simulations to run

        Returns:
            Dictionary containing VaR metrics and drawdown analysis
        """
        try:
            self.logger.info(
                f"Running {n_simulations} Monte Carlo simulations for risk analysis"
            )

            # Run Monte Carlo simulation for worst-case scenarios
            simulations = self.run_monte_carlo_simulation(
                strategy_params, historical_data, n_simulations
            )

            if not simulations or "final_returns" not in simulations:
                self.logger.error("Monte Carlo simulation failed")
                return {"error": "Simulation failed"}

            final_returns = simulations["final_returns"]

            # Calculate VaR at different confidence levels
            var_95 = np.percentile(final_returns, 5)
            var_99 = np.percentile(final_returns, 1)

            # Calculate Conditional VaR (Expected Shortfall)
            cvar_95 = (
                final_returns[final_returns <= var_95].mean()
                if len(final_returns[final_returns <= var_95]) > 0
                else var_95
            )
            cvar_99 = (
                final_returns[final_returns <= var_99].mean()
                if len(final_returns[final_returns <= var_99]) > 0
                else var_99
            )

            # Calculate maximum drawdown from simulations
            max_drawdowns = []
            for sim in simulations["simulations"]:
                if "equity_curve" in sim and len(sim["equity_curve"]) > 0:
                    drawdown = self.calculate_max_drawdown(sim["equity_curve"])
                    max_drawdowns.append(drawdown)

            if not max_drawdowns:
                self.logger.warning("No valid drawdowns calculated")
                max_drawdowns = [0.0]

            worst_case_drawdown = (
                np.percentile(max_drawdowns, 95) if max_drawdowns else 0.0
            )

            risk_metrics = {
                "value_at_risk_95": float(var_95),
                "value_at_risk_99": float(var_99),
                "conditional_var_95": float(cvar_95),
                "conditional_var_99": float(cvar_99),
                "worst_case_drawdown_95": float(worst_case_drawdown),
                "max_simulated_drawdown": (
                    float(max(max_drawdowns)) if max_drawdowns else 0.0
                ),
                "drawdown_distribution": {
                    "mean": float(np.mean(max_drawdowns)) if max_drawdowns else 0.0,
                    "std": float(np.std(max_drawdowns)) if max_drawdowns else 0.0,
                    "percentiles": {
                        "50": (
                            float(np.percentile(max_drawdowns, 50))
                            if max_drawdowns
                            else 0.0
                        ),
                        "75": (
                            float(np.percentile(max_drawdowns, 75))
                            if max_drawdowns
                            else 0.0
                        ),
                        "90": (
                            float(np.percentile(max_drawdowns, 90))
                            if max_drawdowns
                            else 0.0
                        ),
                        "95": (
                            float(np.percentile(max_drawdowns, 95))
                            if max_drawdowns
                            else 0.0
                        ),
                        "99": (
                            float(np.percentile(max_drawdowns, 99))
                            if max_drawdowns
                            else 0.0
                        ),
                    },
                },
                "simulation_summary": {
                    "total_simulations": n_simulations,
                    "successful_simulations": len(simulations["simulations"]),
                    "average_final_return": (
                        float(np.mean(final_returns)) if len(final_returns) > 0 else 0.0
                    ),
                    "return_volatility": (
                        float(np.std(final_returns)) if len(final_returns) > 0 else 0.0
                    ),
                },
            }

            self.logger.info(
                f"Risk analysis completed: VaR 95%={var_95:.4f}, Max DD={worst_case_drawdown:.4f}"
            )
            return risk_metrics

        except Exception as e:
            self.logger.error(f"Error in drawdown potential calculation: {str(e)}")
            return {"error": str(e)}

    def run_monte_carlo_simulation(
        self, strategy_params: Dict, historical_data: pd.DataFrame, n_simulations: int
    ) -> Dict:
        """
        Run Monte Carlo simulations to test strategy under various scenarios.

        Args:
            strategy_params: Strategy parameters
            historical_data: Historical price data
            n_simulations: Number of simulations

        Returns:
            Dictionary containing simulation results
        """
        try:
            simulations = []
            final_returns = []

            # Prepare historical data for simulation
            if len(historical_data) < 100:
                self.logger.warning(
                    "Insufficient historical data for robust simulation"
                )

            # Calculate historical returns and volatility
            historical_data = historical_data.copy()
            historical_data["returns"] = historical_data["close"].pct_change().dropna()

            if historical_data["returns"].empty:
                return {"error": "No valid returns data"}

            mean_return = historical_data["returns"].mean()
            volatility = historical_data["returns"].std()

            for i in range(n_simulations):
                # Generate random price path
                simulation_length = min(
                    252, len(historical_data)
                )  # 1 year or available data
                random_returns = np.random.normal(
                    mean_return, volatility, simulation_length
                )

                # Create synthetic price data
                initial_price = historical_data["close"].iloc[-1]
                synthetic_prices = [initial_price]

                for ret in random_returns:
                    next_price = synthetic_prices[-1] * (1 + ret)
                    synthetic_prices.append(next_price)

                # Create synthetic DataFrame
                synthetic_df = pd.DataFrame(
                    {
                        "close": synthetic_prices[1:],
                        "high": [
                            p * 1.002 for p in synthetic_prices[1:]
                        ],  # Approximate high
                        "low": [
                            p * 0.998 for p in synthetic_prices[1:]
                        ],  # Approximate low
                    }
                )

                # Run strategy simulation on synthetic data
                equity_curve = self.simulate_strategy_performance(
                    synthetic_df, strategy_params
                )

                if equity_curve:
                    final_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[
                        0
                    ]
                    final_returns.append(final_return)

                    simulations.append(
                        {"equity_curve": equity_curve, "final_return": final_return}
                    )

            return {
                "simulations": simulations,
                "final_returns": np.array(final_returns),
            }

        except Exception as e:
            self.logger.error(f"Monte Carlo simulation error: {str(e)}")
            return {"error": str(e)}

    def simulate_strategy_performance(
        self, price_data: pd.DataFrame, strategy_params: Dict
    ) -> List[float]:
        """
        Simulate strategy performance on given price data.

        Args:
            price_data: Price data for simulation
            strategy_params: Strategy parameters

        Returns:
            Equity curve as list of values
        """
        try:
            # Extract strategy parameters with defaults
            slow_ma = strategy_params.get("slow_ma", 140)
            fast_ma = strategy_params.get("fast_ma", 40)
            atr_period = strategy_params.get("atr_period", 14)
            sl_atr_multiplier = strategy_params.get("sl_atr_multiplier", 1.5)
            tp_atr_multiplier = strategy_params.get("tp_atr_multiplier", 2.0)
            risk_per_trade = strategy_params.get(
                "risk_per_trade", 0.02
            )  # 2% risk per trade

            # Calculate indicators
            df = price_data.copy()
            df["slow_ma"] = df["close"].rolling(window=slow_ma).mean()
            df["fast_ma"] = df["close"].rolling(window=fast_ma).mean()

            # Calculate ATR
            df["atr"] = self.calculate_atr(df, atr_period)

            # Generate signals
            df["signal"] = 0
            df.loc[df["fast_ma"] > df["slow_ma"], "signal"] = 1  # Buy signal
            df.loc[df["fast_ma"] < df["slow_ma"], "signal"] = -1  # Sell signal

            # Simulate trades
            equity_curve = [10000.0]  # Starting with $10,000
            current_position = 0
            entry_price = 0
            stop_loss = 0
            take_profit = 0

            for i in range(1, len(df)):
                current_equity = equity_curve[-1]
                current_price = df["close"].iloc[i]
                signal = df["signal"].iloc[i]
                atr = df["atr"].iloc[i]

                # Check for position exit
                if current_position != 0:
                    exit_signal = False
                    pnl = 0

                    # Check stop loss and take profit
                    if current_position == 1:  # Long position
                        if current_price <= stop_loss or current_price >= take_profit:
                            exit_signal = True
                            pnl = (current_price - entry_price) / entry_price
                    elif current_position == -1:  # Short position
                        if current_price >= stop_loss or current_price <= take_profit:
                            exit_signal = True
                            pnl = (entry_price - current_price) / entry_price

                    # Check for signal reversal
                    if signal != current_position:
                        exit_signal = True
                        if current_position == 1:
                            pnl = (current_price - entry_price) / entry_price
                        else:
                            pnl = (entry_price - current_price) / entry_price

                    if exit_signal:
                        # Calculate position size based on risk
                        position_size = (
                            current_equity
                            * risk_per_trade
                            / abs(entry_price - stop_loss)
                            * entry_price
                        )
                        trade_pnl = position_size * pnl
                        current_equity += trade_pnl
                        current_position = 0

                # Check for new position entry
                if (
                    current_position == 0
                    and signal != 0
                    and not pd.isna(atr)
                    and atr > 0
                ):
                    current_position = signal
                    entry_price = current_price

                    if signal == 1:  # Long position
                        stop_loss = entry_price - (atr * sl_atr_multiplier)
                        take_profit = entry_price + (atr * tp_atr_multiplier)
                    else:  # Short position
                        stop_loss = entry_price + (atr * sl_atr_multiplier)
                        take_profit = entry_price - (atr * tp_atr_multiplier)

                equity_curve.append(current_equity)

            return equity_curve

        except Exception as e:
            self.logger.error(f"Strategy simulation error: {str(e)}")
            return [10000.0]  # Return flat equity curve on error

    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
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

    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        Calculate maximum drawdown from equity curve.

        Args:
            equity_curve: List of equity values

        Returns:
            Maximum drawdown as a percentage
        """
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

    def validate_position_sizing(self, strategy_params: Dict) -> Dict:
        """
        Test ATR-based sizing under extreme conditions.

        Args:
            strategy_params: Strategy parameters to validate

        Returns:
            Dictionary containing position sizing validation results
        """
        try:
            validation_results = {
                "position_sizing_safety": "UNKNOWN",
                "leverage_risk": "UNKNOWN",
                "correlation_exposure": "UNKNOWN",
                "atr_multiplier_analysis": {},
                "risk_per_trade_analysis": {},
                "recommendations": [],
            }

            # Extract position sizing parameters
            atr_multiplier = strategy_params.get("sl_atr_multiplier", 2.0)
            tp_atr_multiplier = strategy_params.get("tp_atr_multiplier", 2.0)
            max_risk_per_trade = strategy_params.get("risk_per_trade", 0.02)  # 2%

            # Validate ATR multiplier for stop loss
            validation_results["atr_multiplier_analysis"] = {
                "sl_multiplier": atr_multiplier,
                "tp_multiplier": tp_atr_multiplier,
                "risk_reward_ratio": (
                    tp_atr_multiplier / atr_multiplier if atr_multiplier > 0 else 0
                ),
            }

            if atr_multiplier > 3.0:
                validation_results["position_sizing_safety"] = "HIGH_RISK"
                validation_results["recommendations"].append(
                    f"Stop loss ATR multiplier ({atr_multiplier}) too high - may result in excessive losses"
                )
            elif atr_multiplier < 0.5:
                validation_results["position_sizing_safety"] = "HIGH_RISK"
                validation_results["recommendations"].append(
                    f"Stop loss ATR multiplier ({atr_multiplier}) too low - insufficient risk protection"
                )
            else:
                validation_results["position_sizing_safety"] = "ACCEPTABLE"

            # Validate maximum risk per trade
            validation_results["risk_per_trade_analysis"] = {
                "current_risk_per_trade": max_risk_per_trade,
                "risk_percentage": max_risk_per_trade * 100,
            }

            if max_risk_per_trade > 0.05:  # 5%
                validation_results["leverage_risk"] = "HIGH_RISK"
                validation_results["recommendations"].append(
                    f"Risk per trade ({max_risk_per_trade*100:.1f}%) exceeds 5% - too aggressive"
                )
            elif max_risk_per_trade < 0.005:  # 0.5%
                validation_results["leverage_risk"] = "LOW_RETURN"
                validation_results["recommendations"].append(
                    f"Risk per trade ({max_risk_per_trade*100:.1f}%) below 0.5% - may limit returns"
                )
            else:
                validation_results["leverage_risk"] = "ACCEPTABLE"

            # Risk-Reward Ratio Analysis
            rr_ratio = tp_atr_multiplier / atr_multiplier if atr_multiplier > 0 else 0
            if rr_ratio < 1.5:
                validation_results["recommendations"].append(
                    f"Risk-reward ratio ({rr_ratio:.2f}) below 1.5 - consider increasing take profit or reducing stop loss"
                )
            elif rr_ratio > 4.0:
                validation_results["recommendations"].append(
                    f"Risk-reward ratio ({rr_ratio:.2f}) very high - may reduce win rate significantly"
                )

            # Overall assessment
            high_risk_factors = [
                factor
                for factor in [
                    validation_results["position_sizing_safety"],
                    validation_results["leverage_risk"],
                ]
                if factor == "HIGH_RISK"
            ]

            if len(high_risk_factors) > 0:
                validation_results["overall_risk_level"] = "HIGH"
            elif validation_results["leverage_risk"] == "LOW_RETURN":
                validation_results["overall_risk_level"] = "LOW_RETURN"
            else:
                validation_results["overall_risk_level"] = "ACCEPTABLE"

            self.logger.info(
                f"Position sizing validation completed: {validation_results['overall_risk_level']}"
            )
            return validation_results

        except Exception as e:
            self.logger.error(f"Position sizing validation error: {str(e)}")
            return {"error": str(e)}

    def calculate_risk_metrics(
        self, equity_curve: List[float], trades: List[Dict]
    ) -> Dict:
        """
        Calculate comprehensive risk metrics.

        Args:
            equity_curve: Equity curve values
            trades: List of trade results

        Returns:
            Dictionary containing risk metrics
        """
        try:
            if not equity_curve or len(equity_curve) < 2:
                return {"error": "Insufficient equity data"}

            # Convert to returns
            returns = []
            for i in range(1, len(equity_curve)):
                ret = (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
                returns.append(ret)

            returns = np.array(returns)

            # Basic metrics
            total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            sharpe_ratio = (
                (np.mean(returns) * 252 - self.risk_free_rate) / volatility
                if volatility > 0
                else 0
            )

            # Risk metrics
            max_drawdown = self.calculate_max_drawdown(equity_curve)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)

            # Trade-based metrics
            if trades:
                winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
                losing_trades = [t for t in trades if t.get("pnl", 0) < 0]

                win_rate = len(winning_trades) / len(trades)
                avg_win = (
                    np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
                )
                avg_loss = (
                    np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
                )
                profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            else:
                win_rate = 0
                profit_factor = 0

            risk_metrics = {
                "total_return": float(total_return),
                "annualized_volatility": float(volatility),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "value_at_risk_95": float(var_95),
                "value_at_risk_99": float(var_99),
                "win_rate": float(win_rate),
                "profit_factor": float(profit_factor),
                "calmar_ratio": (
                    float(total_return / max_drawdown) if max_drawdown > 0 else 0
                ),
                "sortino_ratio": self.calculate_sortino_ratio(returns),
            }

            return risk_metrics

        except Exception as e:
            self.logger.error(f"Risk metrics calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        try:
            downside_returns = returns[returns < 0]
            if len(downside_returns) == 0:
                return 0.0

            downside_std = np.std(downside_returns) * np.sqrt(252)
            excess_return = np.mean(returns) * 252 - self.risk_free_rate

            return excess_return / downside_std if downside_std > 0 else 0.0

        except Exception as e:
            return 0.0

    def save_risk_assessment(self, risk_data: Dict, strategy_name: str) -> str:
        """
        Save risk assessment results to file.

        Args:
            risk_data: Risk assessment data
            strategy_name: Name of the strategy

        Returns:
            Path to saved file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_assessment_{strategy_name}_{timestamp}.json"

            # Create reports directory if it doesn't exist
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)

            filepath = reports_dir / filename

            with open(filepath, "w") as f:
                json.dump(risk_data, f, indent=2)

            self.logger.info(f"Risk assessment saved to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Error saving risk assessment: {str(e)}")
            return ""
