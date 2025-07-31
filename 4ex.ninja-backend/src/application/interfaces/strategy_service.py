"""
Strategy Service Interface
Defines the interface for strategy management and execution.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from ...core.entities.strategy import Strategy, StrategyType, StrategyStatus
from ...core.entities.signal import Signal


class IStrategyService(ABC):
    """
    Strategy service interface for strategy management and execution.
    """

    @abstractmethod
    async def create_strategy(self, strategy_data: Dict[str, Any]) -> Strategy:
        """
        Create a new trading strategy.

        Args:
            strategy_data: Strategy configuration data

        Returns:
            Created strategy
        """
        pass

    @abstractmethod
    async def update_strategy(
        self, strategy_id: str, updates: Dict[str, Any]
    ) -> Strategy:
        """
        Update an existing strategy.

        Args:
            strategy_id: Strategy identifier
            updates: Updates to apply

        Returns:
            Updated strategy
        """
        pass

    @abstractmethod
    async def activate_strategy(self, strategy_id: str) -> bool:
        """
        Activate a strategy for live trading.

        Args:
            strategy_id: Strategy identifier

        Returns:
            True if activation successful
        """
        pass

    @abstractmethod
    async def deactivate_strategy(self, strategy_id: str) -> bool:
        """
        Deactivate a strategy.

        Args:
            strategy_id: Strategy identifier

        Returns:
            True if deactivation successful
        """
        pass

    @abstractmethod
    async def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.

        Args:
            strategy_id: Strategy identifier

        Returns:
            True if deletion successful
        """
        pass

    @abstractmethod
    async def clone_strategy(
        self,
        strategy_id: str,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Strategy:
        """
        Clone an existing strategy with optional modifications.

        Args:
            strategy_id: Strategy to clone
            new_name: Name for the cloned strategy
            modifications: Optional modifications to apply

        Returns:
            Cloned strategy
        """
        pass

    @abstractmethod
    async def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """
        Get strategy by ID.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Strategy if found
        """
        pass

    @abstractmethod
    async def get_active_strategies(self) -> List[Strategy]:
        """
        Get all active strategies.

        Returns:
            List of active strategies
        """
        pass

    @abstractmethod
    async def get_strategies_by_type(
        self, strategy_type: StrategyType
    ) -> List[Strategy]:
        """
        Get strategies by type.

        Args:
            strategy_type: Type of strategies to retrieve

        Returns:
            List of strategies
        """
        pass

    @abstractmethod
    async def backtest_strategy(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        initial_balance: Decimal = Decimal("10000"),
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy.

        Args:
            strategy: Strategy to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            initial_balance: Initial balance for backtest

        Returns:
            Backtest results
        """
        pass

    @abstractmethod
    async def optimize_strategy(
        self,
        strategy_id: str,
        parameters: Dict[str, Any],
        optimization_criteria: str = "profit_factor",
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            strategy_id: Strategy to optimize
            parameters: Parameter ranges for optimization
            optimization_criteria: Criteria to optimize for

        Returns:
            Optimization results
        """
        pass

    @abstractmethod
    async def generate_signals(self, strategy: Strategy) -> List[Signal]:
        """
        Generate trading signals using a strategy.

        Args:
            strategy: Strategy to use for signal generation

        Returns:
            List of generated signals
        """
        pass

    @abstractmethod
    async def evaluate_strategy_performance(
        self, strategy_id: str, time_period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate strategy performance metrics.

        Args:
            strategy_id: Strategy identifier
            time_period_days: Time period for evaluation (all time if None)

        Returns:
            Performance metrics
        """
        pass

    @abstractmethod
    async def get_strategy_statistics(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get comprehensive strategy statistics.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Strategy statistics
        """
        pass

    @abstractmethod
    async def validate_strategy_parameters(self, strategy: Strategy) -> Dict[str, Any]:
        """
        Validate strategy parameters and configuration.

        Args:
            strategy: Strategy to validate

        Returns:
            Validation results
        """
        pass

    @abstractmethod
    async def get_strategy_signals(
        self, strategy_id: str, limit: Optional[int] = None
    ) -> List[Signal]:
        """
        Get signals generated by a strategy.

        Args:
            strategy_id: Strategy identifier
            limit: Optional limit on number of signals

        Returns:
            List of signals
        """
        pass

    @abstractmethod
    async def update_strategy_performance(
        self, strategy_id: str, performance_data: Dict[str, Any]
    ) -> bool:
        """
        Update strategy performance metrics.

        Args:
            strategy_id: Strategy identifier
            performance_data: Performance data to update

        Returns:
            True if update successful
        """
        pass
