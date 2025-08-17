"""
VaR Monitor - Real-time Value-at-Risk monitoring for Phase 2
Target: 0.31% daily VaR at 95% confidence level based on backtesting validation

This module implements sophisticated VaR calculation methods:
- Historical VaR (percentile-based)
- Parametric VaR (normal distribution)
- Monte Carlo VaR (simulation-based)
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Use existing imports from the project
from .emergency_risk_manager import EmergencyRiskManager
from ..backtesting.portfolio_manager import PortfolioState

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class VaRResult:
    """Data class for VaR calculation results"""

    method: str
    value: float
    confidence_level: float
    timestamp: datetime
    currency_pair: str
    position_size: float
    volatility: float

    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "value": self.value,
            "confidence_level": self.confidence_level,
            "timestamp": self.timestamp.isoformat(),
            "currency_pair": self.currency_pair,
            "position_size": self.position_size,
            "volatility": self.volatility,
        }


class VaRCalculationMethod(ABC):
    """Abstract base class for VaR calculation methods"""

    @abstractmethod
    async def calculate(
        self, returns: pd.Series, position_value: float, confidence_level: float
    ) -> float:
        """Calculate VaR using specific method"""
        pass


class HistoricalVaR(VaRCalculationMethod):
    """Historical VaR calculation using percentile method"""

    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days

    async def calculate(
        self, returns: pd.Series, position_value: float, confidence_level: float
    ) -> float:
        """
        Calculate historical VaR using percentile method

        Args:
            returns: Historical returns series
            position_value: Current position value
            confidence_level: Confidence level (e.g., 0.95)

        Returns:
            VaR value as positive number (loss amount)
        """
        if len(returns) < 30:  # Minimum data requirement
            logger.warning(
                f"Insufficient data for VaR calculation: {len(returns)} observations"
            )
            return 0.0

        # Use most recent data up to lookback period
        recent_returns = returns.tail(self.lookback_days)

        # Calculate percentile (for 95% confidence, use 5th percentile)
        percentile = (1 - confidence_level) * 100
        var_return = np.percentile(recent_returns, percentile)

        # Convert to monetary VaR (positive for loss)
        var_value = abs(var_return * position_value)

        logger.debug(
            f"Historical VaR calculated: {var_value:.6f} "
            f"(return: {var_return:.6f}, position: {position_value:.2f})"
        )

        return var_value


class ParametricVaR(VaRCalculationMethod):
    """Parametric VaR assuming normal distribution"""

    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days

    async def calculate(
        self, returns: pd.Series, position_value: float, confidence_level: float
    ) -> float:
        """
        Calculate parametric VaR assuming normal distribution

        Args:
            returns: Historical returns series
            position_value: Current position value
            confidence_level: Confidence level (e.g., 0.95)

        Returns:
            VaR value as positive number (loss amount)
        """
        if len(returns) < 30:
            logger.warning(
                f"Insufficient data for parametric VaR: {len(returns)} observations"
            )
            return 0.0

        # Use most recent data
        recent_returns = returns.tail(self.lookback_days)

        # Calculate mean and standard deviation
        mean_return = recent_returns.mean()
        std_return = recent_returns.std()

        # Calculate z-score for confidence level (approximation for normal distribution)
        # For 95% confidence: z ≈ -1.645, for 99%: z ≈ -2.326
        if confidence_level == 0.95:
            z_score = -1.645
        elif confidence_level == 0.99:
            z_score = -2.326
        else:
            # Linear approximation for other confidence levels
            z_score = -1.0 - (confidence_level - 0.5) * 3.0

        # Calculate VaR (negative z_score for loss)
        var_return = mean_return + (z_score * std_return)
        var_value = float(abs(var_return * position_value))

        logger.debug(
            f"Parametric VaR calculated: {var_value:.6f} "
            f"(mean: {mean_return:.6f}, std: {std_return:.6f}, z: {z_score:.3f})"
        )

        return var_value


class MonteCarloVaR(VaRCalculationMethod):
    """Monte Carlo VaR using simulation"""

    def __init__(self, num_simulations: int = 10000, lookback_days: int = 252):
        self.num_simulations = num_simulations
        self.lookback_days = lookback_days

    async def calculate(
        self, returns: pd.Series, position_value: float, confidence_level: float
    ) -> float:
        """
        Calculate Monte Carlo VaR using random simulation

        Args:
            returns: Historical returns series
            position_value: Current position value
            confidence_level: Confidence level (e.g., 0.95)

        Returns:
            VaR value as positive number (loss amount)
        """
        if len(returns) < 30:
            logger.warning(
                f"Insufficient data for Monte Carlo VaR: {len(returns)} observations"
            )
            return 0.0

        # Use most recent data
        recent_returns = returns.tail(self.lookback_days)

        # Calculate parameters for simulation
        mean_return = recent_returns.mean()
        std_return = recent_returns.std()

        # Generate random scenarios
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(
            mean_return, std_return, self.num_simulations
        )

        # Calculate simulated P&L
        simulated_pnl = simulated_returns * position_value

        # Calculate VaR as percentile of simulated losses
        percentile = (1 - confidence_level) * 100
        var_value = float(abs(np.percentile(simulated_pnl, percentile)))

        logger.debug(
            f"Monte Carlo VaR calculated: {var_value:.6f} "
            f"({self.num_simulations} simulations)"
        )

        return var_value


class VaRMonitor:
    """
    Real-time Value-at-Risk monitoring based on backtesting validation
    Target: 0.31% daily VaR at 95% confidence level
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        emergency_manager: Optional[EmergencyRiskManager] = None,
    ):
        """
        Initialize VaR Monitor

        Args:
            confidence_level: VaR confidence level (default 95%)
            emergency_manager: Emergency risk manager for breach handling
        """
        self.confidence_level = confidence_level
        self.target_daily_var = 0.0031  # 0.31% from backtesting
        self.lookback_period = 252  # 1 year of trading days

        # VaR calculation methods
        self.var_methods = {
            "historical": HistoricalVaR(self.lookback_period),
            "parametric": ParametricVaR(self.lookback_period),
            "monte_carlo": MonteCarloVaR(10000, self.lookback_period),
        }

        # Dependencies
        self.emergency_manager = emergency_manager

        # VaR breach tracking
        self.var_breach_count = 0
        self.var_breach_threshold = 5  # Max breaches per month
        self.last_var_calculation = {}

        logger.info(
            f"VaRMonitor initialized with {confidence_level*100}% confidence level"
        )

    async def calculate_portfolio_var(
        self, portfolio_state: PortfolioState
    ) -> Dict[str, VaRResult]:
        """
        Calculate portfolio VaR using multiple methods

        Args:
            portfolio_state: Current portfolio state

        Returns:
            Dictionary of VaR results by method
        """
        try:
            var_results = {}

            # Get active positions from portfolio state
            active_positions = (
                portfolio_state.active_positions
                if hasattr(portfolio_state, "active_positions")
                else {}
            )

            if not active_positions:
                logger.warning("No active positions for VaR calculation")
                return var_results

            # Calculate VaR for each position
            for pair, position in active_positions.items():
                pair_results = await self._calculate_position_var(pair, position)

                # Aggregate results by method
                for method, result in pair_results.items():
                    if method not in var_results:
                        var_results[method] = []
                    var_results[method].append(result)

            # Calculate portfolio-level VaR
            portfolio_var = {}
            for method in self.var_methods.keys():
                if method in var_results:
                    total_var = sum(result.value for result in var_results[method])

                    # Create portfolio VaR result
                    portfolio_var[method] = VaRResult(
                        method=method,
                        value=total_var,
                        confidence_level=self.confidence_level,
                        timestamp=datetime.now(),
                        currency_pair="PORTFOLIO",
                        position_size=sum(
                            abs(getattr(pos, "position_size", 0))
                            for pos in active_positions.values()
                        ),
                        volatility=0.0,  # Portfolio volatility calculation would go here
                    )

            # Store for breach checking
            self.last_var_calculation = portfolio_var

            logger.info(
                f"Portfolio VaR calculated for {len(active_positions)} positions"
            )
            return portfolio_var

        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {e}")
            return {}

    async def _calculate_position_var(
        self, currency_pair: str, position
    ) -> Dict[str, VaRResult]:
        """Calculate VaR for individual position"""
        try:
            results = {}

            # Get price history for the pair
            price_history = await self._get_price_history(currency_pair)

            if price_history is None or len(price_history) < 30:
                logger.warning(f"Insufficient price history for {currency_pair}")
                return results

            # Calculate returns
            returns = price_history.pct_change().dropna()

            # Current position value (using position attributes from Position class)
            position_size = getattr(position, "position_size", 0)
            entry_price = getattr(position, "entry_price", 1.0)
            position_value = abs(position_size * entry_price)

            # Calculate VaR using each method
            for method_name, method in self.var_methods.items():
                try:
                    var_value = await method.calculate(
                        returns, position_value, self.confidence_level
                    )

                    results[method_name] = VaRResult(
                        method=method_name,
                        value=var_value,
                        confidence_level=self.confidence_level,
                        timestamp=datetime.now(),
                        currency_pair=currency_pair,
                        position_size=position_size,
                        volatility=returns.std(),
                    )

                except Exception as e:
                    logger.error(
                        f"Error calculating {method_name} VaR for {currency_pair}: {e}"
                    )

            return results

        except Exception as e:
            logger.error(f"Error calculating position VaR: {e}")
            return {}

    async def check_var_breaches(self) -> Dict[str, bool]:
        """
        Monitor for VaR threshold breaches

        Returns:
            Dictionary indicating breaches by method
        """
        try:
            breaches = {}

            if not self.last_var_calculation:
                return breaches

            # Check each VaR method against target
            for method, var_result in self.last_var_calculation.items():
                # Convert VaR to percentage of portfolio value
                # Assuming portfolio value calculation would be available
                portfolio_value = (
                    100000  # Placeholder - should be actual portfolio value
                )
                var_percentage = var_result.value / portfolio_value

                # Check if VaR exceeds target (0.31%)
                is_breach = var_percentage > self.target_daily_var
                breaches[method] = is_breach

                if is_breach:
                    logger.warning(
                        f"VaR breach detected - {method}: {var_percentage:.4f}% "
                        f"(target: {self.target_daily_var:.4f}%)"
                    )
                    self.var_breach_count += 1

            return breaches

        except Exception as e:
            logger.error(f"Error checking VaR breaches: {e}")
            return {}

    async def generate_var_alerts(self, breaches: Dict[str, bool]) -> List[Dict]:
        """
        Send alerts when VaR limits exceeded

        Args:
            breaches: VaR breach status by method

        Returns:
            List of alert dictionaries
        """
        alerts = []

        try:
            for method, is_breach in breaches.items():
                if is_breach and method in self.last_var_calculation:
                    var_result = self.last_var_calculation[method]

                    alert = {
                        "type": "VAR_BREACH",
                        "severity": (
                            "HIGH"
                            if var_result.value > self.target_daily_var * 1.5
                            else "MEDIUM"
                        ),
                        "method": method,
                        "current_var": var_result.value,
                        "target_var": self.target_daily_var,
                        "timestamp": datetime.now().isoformat(),
                        "message": f"VaR breach detected using {method} method: "
                        f"{var_result.value:.6f} exceeds target {self.target_daily_var:.6f}",
                    }

                    alerts.append(alert)
                    logger.warning(f"VaR alert generated: {alert['message']}")

            # Check if emergency protocols should be triggered
            if len(alerts) >= 2:  # Multiple methods showing breach
                if self.emergency_manager:
                    # Use emergency manager's existing alert system
                    logger.error(
                        "MULTIPLE VaR BREACH DETECTED - Consider emergency protocols"
                    )

            return alerts

        except Exception as e:
            logger.error(f"Error generating VaR alerts: {e}")
            return []

    async def _get_price_history(self, currency_pair: str) -> Optional[pd.Series]:
        """Get price history for currency pair"""
        try:
            # For Phase 2 initial implementation, we'll use mock data
            # This will be replaced with actual data integration
            logger.warning(f"Using mock data for {currency_pair} VaR calculation")
            dates = pd.date_range(
                end=datetime.now(), periods=self.lookback_period, freq="D"
            )

            # Generate realistic forex price movements
            np.random.seed(hash(currency_pair) % 2**32)
            initial_price = 1.1000 if "EUR" in currency_pair else 1.2500
            returns = np.random.normal(0, 0.01, len(dates))  # 1% daily volatility
            prices = [initial_price]

            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))

            return pd.Series(prices, index=dates)

        except Exception as e:
            logger.error(f"Error getting price history for {currency_pair}: {e}")
            return None

    def get_var_summary(self) -> Dict:
        """Get current VaR summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "target_var": self.target_daily_var,
            "confidence_level": self.confidence_level,
            "breach_count": self.var_breach_count,
            "methods_available": list(self.var_methods.keys()),
            "last_calculation": {},
        }

        if self.last_var_calculation:
            for method, result in self.last_var_calculation.items():
                summary["last_calculation"][method] = result.to_dict()

        return summary


# Example usage and testing
if __name__ == "__main__":

    async def test_var_monitor():
        """Test VaR monitoring functionality"""
        print("Testing VaR Monitor...")

        # Initialize monitor
        var_monitor = VaRMonitor(confidence_level=0.95)

        # Create mock portfolio state for testing
        from ..backtesting.position_manager import Position

        # Create mock position
        mock_position = Position(
            position_id="test_001",
            pair="EUR_USD",
            direction="BUY",
            entry_price=1.1000,
            position_size=1000.0,
            stop_loss=1.0950,
            take_profit=1.1100,
            entry_time=datetime.now(),
            strategy_name="test_strategy",
            unrealized_pnl=50.0,
        )

        # Create mock portfolio state
        portfolio_state = PortfolioState(
            total_balance=100000.0,
            available_balance=90000.0,
            total_risk=0.02,
            active_positions={"EUR_USD": mock_position},
            strategy_allocations={},
        )

        # Calculate VaR
        var_results = await var_monitor.calculate_portfolio_var(portfolio_state)

        print("VaR Results:")
        for method, result in var_results.items():
            print(f"{method}: {result.value:.6f}")

        # Check for breaches
        breaches = await var_monitor.check_var_breaches()
        print(f"Breaches: {breaches}")

        # Generate alerts if needed
        alerts = await var_monitor.generate_var_alerts(breaches)
        if alerts:
            print(f"Alerts generated: {len(alerts)}")
            for alert in alerts:
                print(f"  - {alert['message']}")

        # Get summary
        summary = var_monitor.get_var_summary()
        print(f"VaR Summary: {summary}")

    # Run test
    asyncio.run(test_var_monitor())
