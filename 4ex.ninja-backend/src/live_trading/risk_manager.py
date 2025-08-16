"""
Risk Manager

Manages trading risk including position sizing, exposure limits,
and portfolio-level risk controls.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.backtesting.strategy_interface import TradeSignal, AccountInfo
from .position_manager import Position, PositionManager


class RiskLevel(Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio assessment."""

    total_exposure: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    sharpe_ratio: float
    risk_level: RiskLevel
    risk_score: float  # 0-100 scale
    warnings: List[str]


class RiskManager:
    """
    Comprehensive risk management system for live trading.
    """

    def __init__(
        self,
        max_risk_per_trade: float = 0.02,  # 2% per trade
        max_total_risk: float = 0.10,  # 10% total portfolio
        max_correlation: float = 0.7,  # Max correlation between positions
        max_drawdown_limit: float = 0.15,
    ):  # 15% max drawdown
        """
        Initialize risk manager with risk parameters.

        Args:
            max_risk_per_trade: Maximum risk per individual trade
            max_total_risk: Maximum total portfolio risk
            max_correlation: Maximum correlation between positions
            max_drawdown_limit: Maximum acceptable drawdown
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_total_risk = max_total_risk
        self.max_correlation = max_correlation
        self.max_drawdown_limit = max_drawdown_limit

        # Risk tracking
        self.daily_pnl_history: List[float] = []
        self.max_balance: float = 0.0
        self.risk_warnings: List[str] = []

    def validate_signal_risk(
        self,
        signal: TradeSignal,
        account_info: AccountInfo,
        open_positions: List[Position],
    ) -> Tuple[bool, List[str]]:
        """
        Validate if a signal passes risk management checks.

        Args:
            signal: Trade signal to validate
            account_info: Current account information
            open_positions: List of open positions

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []
        is_valid = True

        # Check individual trade risk
        if signal.stop_loss and signal.entry_price:
            risk_amount = abs(signal.entry_price - signal.stop_loss)
            risk_percentage = risk_amount / signal.entry_price

            if risk_percentage > self.max_risk_per_trade:
                warnings.append(
                    f"Trade risk {risk_percentage:.1%} exceeds maximum {self.max_risk_per_trade:.1%}"
                )
                is_valid = False

        # Check portfolio exposure
        current_exposure = self._calculate_total_exposure(
            open_positions, account_info.balance
        )

        # Estimate new position size (simplified)
        estimated_position_value = account_info.balance * self.max_risk_per_trade
        new_exposure = (
            current_exposure * account_info.balance + estimated_position_value
        ) / account_info.balance

        if new_exposure > self.max_total_risk:
            warnings.append(
                f"Portfolio exposure would exceed {self.max_total_risk:.1%} limit"
            )
            is_valid = False

        # Check correlation (simplified - same instrument check)
        same_instrument_positions = [
            pos for pos in open_positions if pos.instrument == signal.pair
        ]
        if len(same_instrument_positions) >= 2:
            warnings.append(f"Multiple positions already open for {signal.pair}")
            is_valid = False

        # Check account health
        if account_info.margin_used / account_info.equity > 0.8:  # 80% margin usage
            warnings.append("High margin usage - account at risk")
            is_valid = False

        # Check signal quality
        if signal.signal_strength < 0.6:  # Require minimum 60% confidence
            warnings.append(f"Low signal strength: {signal.signal_strength:.1%}")
            # Don't invalidate, just warn

        return is_valid, warnings

    def calculate_position_size(
        self, signal: TradeSignal, account_info: AccountInfo
    ) -> int:
        """
        Calculate optimal position size based on risk management.

        Args:
            signal: Trade signal
            account_info: Account information

        Returns:
            Position size in units
        """
        try:
            # Base risk amount
            risk_amount = account_info.balance * self.max_risk_per_trade

            if signal.stop_loss and signal.entry_price:
                # Risk-based sizing
                stop_distance = abs(signal.entry_price - signal.stop_loss)
                if stop_distance > 0:
                    position_value = risk_amount / stop_distance
                    units = int(position_value / signal.entry_price)
                else:
                    units = int(risk_amount / signal.entry_price)
            else:
                # Default sizing (1% of balance)
                units = int((account_info.balance * 0.01) / signal.entry_price)

            # Apply limits
            min_units = 1
            max_units = int(
                (account_info.balance * 0.05) / signal.entry_price
            )  # Max 5% of balance

            units = max(min_units, min(units, max_units))

            # Adjust for signal strength
            units = int(units * signal.signal_strength)
            units = max(1, units)  # Minimum 1 unit

            # Make negative for sell orders
            if signal.direction == "SELL":
                units = -units

            return units

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return 1 if signal.direction == "BUY" else -1

    def assess_portfolio_risk(
        self, account_info: AccountInfo, open_positions: List[Position]
    ) -> RiskMetrics:
        """
        Assess current portfolio risk level.

        Args:
            account_info: Current account information
            open_positions: List of open positions

        Returns:
            Risk metrics assessment
        """
        warnings = []

        # Calculate total exposure
        total_exposure = self._calculate_total_exposure(
            open_positions, account_info.balance
        )

        # Calculate current drawdown
        current_drawdown = self._calculate_current_drawdown(account_info)

        # Calculate Value at Risk (simplified)
        var_95 = self._calculate_var_95(open_positions, account_info.balance)

        # Calculate Sharpe ratio (if we have enough history)
        sharpe_ratio = self._calculate_sharpe_ratio()

        # Determine risk level
        risk_score = 0

        # Exposure factor (0-25 points)
        risk_score += min(25, (total_exposure / self.max_total_risk) * 25)

        # Drawdown factor (0-25 points)
        if current_drawdown > 0:
            risk_score += min(25, (current_drawdown / self.max_drawdown_limit) * 25)

        # Margin factor (0-25 points)
        margin_usage = (
            account_info.margin_used / account_info.equity
            if account_info.equity > 0
            else 0
        )
        risk_score += min(25, margin_usage * 25)

        # Concentration factor (0-25 points)
        concentration_risk = self._calculate_concentration_risk(open_positions)
        risk_score += min(25, concentration_risk * 25)

        # Determine risk level
        if risk_score < 25:
            risk_level = RiskLevel.LOW
        elif risk_score < 50:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 75:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        # Generate warnings
        if total_exposure > self.max_total_risk * 0.8:
            warnings.append(f"High portfolio exposure: {total_exposure:.1%}")

        if current_drawdown > self.max_drawdown_limit * 0.8:
            warnings.append(f"High drawdown: {current_drawdown:.1%}")

        if margin_usage > 0.7:
            warnings.append(f"High margin usage: {margin_usage:.1%}")

        if len(open_positions) > 10:
            warnings.append(f"Many open positions: {len(open_positions)}")

        return RiskMetrics(
            total_exposure=total_exposure,
            max_drawdown=current_drawdown,
            var_95=var_95,
            sharpe_ratio=sharpe_ratio,
            risk_level=risk_level,
            risk_score=risk_score,
            warnings=warnings,
        )

    def should_stop_trading(
        self, account_info: AccountInfo, open_positions: List[Position]
    ) -> Tuple[bool, str]:
        """
        Determine if trading should be stopped due to risk.

        Args:
            account_info: Current account information
            open_positions: List of open positions

        Returns:
            Tuple of (should_stop, reason)
        """
        # Check drawdown limit
        current_drawdown = self._calculate_current_drawdown(account_info)
        if current_drawdown > self.max_drawdown_limit:
            return True, f"Drawdown limit exceeded: {current_drawdown:.1%}"

        # Check margin call risk
        margin_usage = (
            account_info.margin_used / account_info.equity
            if account_info.equity > 0
            else 0
        )
        if margin_usage > 0.9:
            return True, f"Margin call risk: {margin_usage:.1%} margin used"

        # Check total exposure
        total_exposure = self._calculate_total_exposure(
            open_positions, account_info.balance
        )
        if total_exposure > self.max_total_risk * 1.2:  # 20% buffer exceeded
            return True, f"Total exposure exceeded: {total_exposure:.1%}"

        # Check account balance
        if account_info.balance < account_info.equity * 0.5:  # Lost more than 50%
            return True, f"Significant account loss detected"

        return False, ""

    def update_daily_pnl(self, current_balance: float):
        """
        Update daily P&L tracking for risk calculations.

        Args:
            current_balance: Current account balance
        """
        if self.max_balance == 0:
            self.max_balance = current_balance
        else:
            self.max_balance = max(self.max_balance, current_balance)

        # Calculate daily P&L if we have previous data
        if len(self.daily_pnl_history) > 0:
            daily_pnl = current_balance - (
                self.daily_pnl_history[-1]
                if self.daily_pnl_history
                else current_balance
            )
            self.daily_pnl_history.append(daily_pnl)
        else:
            self.daily_pnl_history.append(0.0)

        # Keep only last 30 days
        if len(self.daily_pnl_history) > 30:
            self.daily_pnl_history = self.daily_pnl_history[-30:]

    def _calculate_total_exposure(
        self, positions: List[Position], balance: float
    ) -> float:
        """Calculate total portfolio exposure as percentage of balance."""
        if not positions or balance <= 0:
            return 0.0

        total_value = sum(abs(pos.units * pos.current_price) for pos in positions)
        return total_value / balance

    def _calculate_current_drawdown(self, account_info: AccountInfo) -> float:
        """Calculate current drawdown from peak balance."""
        if self.max_balance <= 0:
            return 0.0

        return (self.max_balance - account_info.balance) / self.max_balance

    def _calculate_var_95(self, positions: List[Position], balance: float) -> float:
        """Calculate Value at Risk at 95% confidence (simplified)."""
        if not self.daily_pnl_history or len(self.daily_pnl_history) < 5:
            return 0.0

        # Simple VaR calculation using historical method
        sorted_pnl = sorted(self.daily_pnl_history)
        var_index = int(len(sorted_pnl) * 0.05)  # 5th percentile

        if var_index < len(sorted_pnl):
            return abs(sorted_pnl[var_index]) / balance if balance > 0 else 0.0

        return 0.0

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio from daily P&L history."""
        if len(self.daily_pnl_history) < 10:
            return 0.0

        import statistics

        try:
            mean_return = statistics.mean(self.daily_pnl_history)
            std_return = statistics.stdev(self.daily_pnl_history)

            if std_return > 0:
                return mean_return / std_return

        except Exception:
            pass

        return 0.0

    def _calculate_concentration_risk(self, positions: List[Position]) -> float:
        """Calculate concentration risk (0-1 scale)."""
        if not positions:
            return 0.0

        # Count positions by instrument
        instrument_counts = {}
        for pos in positions:
            instrument_counts[pos.instrument] = (
                instrument_counts.get(pos.instrument, 0) + 1
            )

        # Find maximum concentration
        max_concentration = max(instrument_counts.values()) if instrument_counts else 0
        total_positions = len(positions)

        return max_concentration / total_positions if total_positions > 0 else 0.0


if __name__ == "__main__":
    # Test risk manager
    print("🧪 Testing Risk Manager...")

    rm = RiskManager()

    # Create test account info
    account_info = AccountInfo(
        balance=10000.0,
        equity=9800.0,
        margin_used=1000.0,
        free_margin=8800.0,
        max_position_size=1000.0,
    )

    # Create test signal
    from datetime import datetime
    from src.backtesting.strategy_interface import TradeSignal

    test_signal = TradeSignal(
        pair="EUR_USD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        signal_strength=0.8,
        signal_time=datetime.utcnow(),
        strategy_name="test",
    )

    # Test signal validation
    is_valid, warnings = rm.validate_signal_risk(test_signal, account_info, [])
    print(f"✅ Signal valid: {is_valid}")
    if warnings:
        print(f"⚠️  Warnings: {warnings}")

    # Test position sizing
    position_size = rm.calculate_position_size(test_signal, account_info)
    print(f"✅ Position size: {position_size} units")

    # Test portfolio risk assessment
    risk_metrics = rm.assess_portfolio_risk(account_info, [])
    print(f"✅ Risk level: {risk_metrics.risk_level.value}")
    print(f"✅ Risk score: {risk_metrics.risk_score:.1f}/100")

    # Test stop trading check
    should_stop, reason = rm.should_stop_trading(account_info, [])
    print(f"✅ Should stop trading: {should_stop}")
    if reason:
        print(f"📛 Reason: {reason}")

    print("🎯 Risk Manager test completed!")
