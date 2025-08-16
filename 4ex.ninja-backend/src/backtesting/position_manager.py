"""
Position Manager for Universal Backtesting Framework.

This module manages position sizing, risk management, and trade execution
for ANY strategy implementing the BaseStrategy interface.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from .strategy_interface import BaseStrategy, TradeSignal, AccountInfo

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Active position representation."""

    position_id: str
    pair: str
    direction: str  # "BUY" or "SELL"
    entry_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    strategy_name: str
    unrealized_pnl: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskParameters:
    """Risk management parameters."""

    max_risk_per_trade: float = 0.02  # 2% max risk per trade
    max_portfolio_risk: float = 0.06  # 6% max total portfolio risk
    max_positions: int = 5  # Maximum concurrent positions
    max_risk_per_pair: float = 0.04  # 4% max risk per currency pair
    max_correlation_positions: int = 3  # Max correlated positions
    position_size_method: str = "fixed_risk"  # "fixed_risk", "fixed_size", "kelly"


class PositionManager:
    """
    Universal position manager that works with ANY strategy.

    This manager handles position sizing, risk management, and position
    tracking for strategies implementing the BaseStrategy interface.
    """

    def __init__(self, risk_params: Optional[RiskParameters] = None):
        """
        Initialize position manager.

        Args:
            risk_params: Risk management parameters
        """
        self.risk_params = risk_params or RiskParameters()
        self.active_positions: Dict[str, Position] = {}
        self.position_counter = 0

        logger.info("PositionManager initialized")

    def calculate_position_size(
        self, signal: TradeSignal, account_info: AccountInfo, strategy: BaseStrategy
    ) -> float:
        """
        Calculate position size based on risk parameters and strategy logic.

        Args:
            signal: Trade signal
            account_info: Current account information
            strategy: Strategy instance for custom sizing logic

        Returns:
            Position size in base currency units
        """
        try:
            # First, use strategy's own position sizing logic
            strategy_size = strategy.calculate_position_size(signal, account_info)

            # Apply risk management constraints
            max_allowed_size = self._calculate_max_allowed_size(signal, account_info)

            # Use the smaller of strategy size and risk-limited size
            final_size = min(strategy_size, max_allowed_size)

            # Additional portfolio-level checks
            if not self._validate_portfolio_risk(signal, final_size, account_info):
                logger.warning(
                    f"Portfolio risk exceeded for {signal.pair}, reducing position"
                )
                final_size = self._calculate_risk_adjusted_size(signal, account_info)

            logger.debug(f"Position size calculated: {final_size} for {signal.pair}")
            return max(0.0, final_size)

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0

    def _calculate_max_allowed_size(
        self, signal: TradeSignal, account_info: AccountInfo
    ) -> float:
        """
        Calculate maximum allowed position size based on risk parameters.

        Args:
            signal: Trade signal
            account_info: Account information

        Returns:
            Maximum allowed position size
        """
        if self.risk_params.position_size_method == "fixed_risk":
            return self._calculate_fixed_risk_size(signal, account_info)
        elif self.risk_params.position_size_method == "fixed_size":
            return self._calculate_fixed_size(account_info)
        else:
            return self._calculate_fixed_risk_size(signal, account_info)

    def _calculate_fixed_risk_size(
        self, signal: TradeSignal, account_info: AccountInfo
    ) -> float:
        """
        Calculate position size based on fixed risk percentage.

        Args:
            signal: Trade signal
            account_info: Account information

        Returns:
            Position size for fixed risk
        """
        # Calculate risk amount
        risk_amount = account_info.balance * self.risk_params.max_risk_per_trade

        # Calculate stop loss distance in price terms
        if signal.direction == "BUY":
            stop_distance = signal.entry_price - signal.stop_loss
        else:
            stop_distance = signal.stop_loss - signal.entry_price

        if stop_distance <= 0:
            logger.warning(f"Invalid stop distance for {signal.pair}: {stop_distance}")
            return 0.0

        # Calculate position size
        # Risk amount = Position size * Stop distance
        position_size = risk_amount / stop_distance

        # Ensure position doesn't exceed account limits
        max_position_value = account_info.balance * 0.5  # Max 50% of balance per trade
        max_size_by_value = max_position_value / signal.entry_price

        return min(position_size, max_size_by_value)

    def _calculate_fixed_size(self, account_info: AccountInfo) -> float:
        """
        Calculate fixed position size.

        Args:
            account_info: Account information

        Returns:
            Fixed position size
        """
        # Use 10% of balance as standard position size
        return account_info.balance * 0.1

    def _validate_portfolio_risk(
        self, signal: TradeSignal, position_size: float, account_info: AccountInfo
    ) -> bool:
        """
        Validate that new position doesn't exceed portfolio risk limits.

        Args:
            signal: Trade signal
            position_size: Proposed position size
            account_info: Account information

        Returns:
            True if position is within risk limits
        """
        # Check maximum positions limit
        if len(self.active_positions) >= self.risk_params.max_positions:
            logger.warning(
                f"Maximum positions limit reached: {len(self.active_positions)}"
            )
            return False

        # Check pair-specific risk
        pair_exposure = self._calculate_pair_exposure(signal.pair)
        new_pair_risk = self._calculate_position_risk(
            signal, position_size, account_info
        )

        if pair_exposure + new_pair_risk > self.risk_params.max_risk_per_pair:
            logger.warning(f"Pair risk limit exceeded for {signal.pair}")
            return False

        # Check total portfolio risk
        total_risk = self._calculate_total_portfolio_risk(account_info)
        if total_risk + new_pair_risk > self.risk_params.max_portfolio_risk:
            logger.warning(
                f"Portfolio risk limit exceeded: {total_risk + new_pair_risk:.2%}"
            )
            return False

        return True

    def _calculate_risk_adjusted_size(
        self, signal: TradeSignal, account_info: AccountInfo
    ) -> float:
        """
        Calculate position size adjusted for current portfolio risk.

        Args:
            signal: Trade signal
            account_info: Account information

        Returns:
            Risk-adjusted position size
        """
        # Calculate remaining risk budget
        current_risk = self._calculate_total_portfolio_risk(account_info)
        remaining_risk = max(0, self.risk_params.max_portfolio_risk - current_risk)

        # Calculate position size for remaining risk
        if signal.direction == "BUY":
            stop_distance = signal.entry_price - signal.stop_loss
        else:
            stop_distance = signal.stop_loss - signal.entry_price

        if stop_distance <= 0:
            return 0.0

        risk_amount = account_info.balance * remaining_risk
        return risk_amount / stop_distance

    def _calculate_pair_exposure(self, pair: str) -> float:
        """
        Calculate current exposure to a currency pair.

        Args:
            pair: Currency pair

        Returns:
            Current exposure as percentage of account
        """
        pair_positions = [p for p in self.active_positions.values() if p.pair == pair]
        total_exposure = sum(abs(p.unrealized_pnl) for p in pair_positions)
        return total_exposure / 10000.0  # Simplified calculation

    def _calculate_position_risk(
        self, signal: TradeSignal, position_size: float, account_info: AccountInfo
    ) -> float:
        """
        Calculate risk of a single position.

        Args:
            signal: Trade signal
            position_size: Position size
            account_info: Account information

        Returns:
            Position risk as percentage of account
        """
        if signal.direction == "BUY":
            risk_distance = signal.entry_price - signal.stop_loss
        else:
            risk_distance = signal.stop_loss - signal.entry_price

        risk_amount = position_size * risk_distance
        return risk_amount / account_info.balance

    def _calculate_total_portfolio_risk(self, account_info: AccountInfo) -> float:
        """
        Calculate total portfolio risk from active positions.

        Args:
            account_info: Account information

        Returns:
            Total portfolio risk as percentage
        """
        total_risk = sum(abs(p.unrealized_pnl) for p in self.active_positions.values())
        return total_risk / account_info.balance

    def open_position(
        self, signal: TradeSignal, position_size: float, strategy_name: str
    ) -> Optional[Position]:
        """
        Open a new position.

        Args:
            signal: Trade signal
            position_size: Position size
            strategy_name: Name of the strategy

        Returns:
            Position object if successful, None otherwise
        """
        try:
            self.position_counter += 1
            position_id = f"{strategy_name}_{signal.pair}_{self.position_counter}"

            position = Position(
                position_id=position_id,
                pair=signal.pair,
                direction=signal.direction,
                entry_price=signal.entry_price,
                position_size=position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                entry_time=signal.signal_time,
                strategy_name=strategy_name,
                metadata=signal.metadata or {},
            )

            self.active_positions[position_id] = position
            logger.info(
                f"Opened position {position_id}: {signal.direction} {position_size} {signal.pair}"
            )

            return position

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return None

    def close_position(
        self, position_id: str, exit_price: float, exit_reason: str
    ) -> Optional[float]:
        """
        Close an active position.

        Args:
            position_id: Position identifier
            exit_price: Exit price
            exit_reason: Reason for exit

        Returns:
            Realized P&L if successful, None otherwise
        """
        try:
            if position_id not in self.active_positions:
                logger.warning(f"Position {position_id} not found")
                return None

            position = self.active_positions[position_id]

            # Calculate P&L
            if position.direction == "BUY":
                pnl = (exit_price - position.entry_price) * position.position_size
            else:
                pnl = (position.entry_price - exit_price) * position.position_size

            # Remove position
            del self.active_positions[position_id]

            logger.info(
                f"Closed position {position_id}: P&L = {pnl:.2f} ({exit_reason})"
            )
            return pnl

        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return None

    def update_positions(self, current_prices: Dict[str, float]) -> None:
        """
        Update unrealized P&L for all active positions.

        Args:
            current_prices: Current market prices by pair
        """
        for position in self.active_positions.values():
            if position.pair in current_prices:
                current_price = current_prices[position.pair]

                if position.direction == "BUY":
                    position.unrealized_pnl = (
                        current_price - position.entry_price
                    ) * position.position_size
                else:
                    position.unrealized_pnl = (
                        position.entry_price - current_price
                    ) * position.position_size

    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get summary of all active positions.

        Returns:
            Dictionary with position summary
        """
        return {
            "total_positions": len(self.active_positions),
            "positions_by_pair": {
                pair: len([p for p in self.active_positions.values() if p.pair == pair])
                for pair in set(p.pair for p in self.active_positions.values())
            },
            "total_unrealized_pnl": sum(
                p.unrealized_pnl for p in self.active_positions.values()
            ),
            "position_details": [
                {
                    "id": p.position_id,
                    "pair": p.pair,
                    "direction": p.direction,
                    "size": p.position_size,
                    "unrealized_pnl": p.unrealized_pnl,
                    "entry_time": p.entry_time,
                }
                for p in self.active_positions.values()
            ],
        }
