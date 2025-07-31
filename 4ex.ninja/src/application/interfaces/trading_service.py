"""
Trading Service Interface
Defines the interface for trading operations and coordination.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from ...core.entities.signal import Signal, SignalType
from ...core.entities.strategy import Strategy


class ITradingService(ABC):
    """
    Trading service interface for coordinating trading operations.
    """

    @abstractmethod
    async def execute_signal(self, signal: Signal) -> bool:
        """
        Execute a trading signal.

        Args:
            signal: The signal to execute

        Returns:
            True if execution successful
        """
        pass

    @abstractmethod
    async def close_position(
        self, signal_id: str, close_price: Optional[Decimal] = None
    ) -> bool:
        """
        Close an open position.

        Args:
            signal_id: Signal identifier
            close_price: Optional close price (uses market price if not provided)

        Returns:
            True if position closed successfully
        """
        pass

    @abstractmethod
    async def get_open_positions(self) -> List[Signal]:
        """
        Get all open trading positions.

        Returns:
            List of open signals/positions
        """
        pass

    @abstractmethod
    async def get_account_balance(self) -> Decimal:
        """
        Get current account balance.

        Returns:
            Current account balance
        """
        pass

    @abstractmethod
    async def calculate_position_size(
        self, signal: Signal, risk_amount: Decimal, account_balance: Decimal
    ) -> Decimal:
        """
        Calculate appropriate position size for a signal.

        Args:
            signal: The trading signal
            risk_amount: Amount to risk on this trade
            account_balance: Current account balance

        Returns:
            Calculated position size
        """
        pass

    @abstractmethod
    async def validate_signal(self, signal: Signal) -> Dict[str, Any]:
        """
        Validate a signal before execution.

        Args:
            signal: Signal to validate

        Returns:
            Validation result with any issues found
        """
        pass

    @abstractmethod
    async def get_market_hours(self, pair: str) -> Dict[str, Any]:
        """
        Get market hours for a trading pair.

        Args:
            pair: Currency pair

        Returns:
            Market hours information
        """
        pass

    @abstractmethod
    async def check_trading_conditions(self) -> Dict[str, bool]:
        """
        Check if trading conditions are met.

        Returns:
            Dictionary of trading condition checks
        """
        pass

    @abstractmethod
    async def get_daily_pnl(self, date: Optional[datetime] = None) -> Decimal:
        """
        Get daily profit/loss.

        Args:
            date: Optional date (defaults to today)

        Returns:
            Daily PnL
        """
        pass

    @abstractmethod
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.

        Returns:
            Risk metrics including exposure, drawdown, etc.
        """
        pass

    @abstractmethod
    async def emergency_close_all(self) -> Dict[str, bool]:
        """
        Emergency close all open positions.

        Returns:
            Results of closing each position
        """
        pass
