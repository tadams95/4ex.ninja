"""
Strategy Repository Interface - Domain-specific repository for Strategy entities

This module defines the Strategy repository interface with domain-specific
methods for Strategy entity operations.
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .repository import IBaseRepository
from ..entities.strategy import Strategy, StrategyType, StrategyStatus


class IStrategyRepository(IBaseRepository[Strategy]):
    """
    Strategy repository interface defining Strategy-specific data access methods.

    Extends the base repository with domain-specific operations for Strategy entities.
    """

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Strategy]:
        """
        Get a strategy by its name.

        Args:
            name: The strategy name

        Returns:
            Strategy if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_type(
        self, strategy_type: StrategyType, limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Get all strategies of a specific type.

        Args:
            strategy_type: The strategy type to filter by
            limit: Maximum number of strategies to return

        Returns:
            List of strategies of the specified type
        """
        pass

    @abstractmethod
    async def get_by_status(
        self, status: StrategyStatus, limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Get all strategies with a specific status.

        Args:
            status: The strategy status to filter by
            limit: Maximum number of strategies to return

        Returns:
            List of strategies with the specified status
        """
        pass

    @abstractmethod
    async def get_active_strategies(
        self, limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Get all currently active strategies.

        Args:
            limit: Maximum number of strategies to return

        Returns:
            List of active strategies
        """
        pass

    @abstractmethod
    async def get_by_pair(
        self, pair: str, limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Get all strategies for a specific currency pair.

        Args:
            pair: The currency pair (e.g., "EUR_USD")
            limit: Maximum number of strategies to return

        Returns:
            List of strategies for the pair
        """
        pass

    @abstractmethod
    async def get_by_timeframe(
        self, timeframe: str, limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Get all strategies for a specific timeframe.

        Args:
            timeframe: The timeframe (e.g., "H4", "D")
            limit: Maximum number of strategies to return

        Returns:
            List of strategies for the timeframe
        """
        pass

    @abstractmethod
    async def get_by_creator(
        self, creator: str, limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Get all strategies created by a specific user.

        Args:
            creator: The creator identifier
            limit: Maximum number of strategies to return

        Returns:
            List of strategies created by the user
        """
        pass

    @abstractmethod
    async def search_by_tags(
        self, tags: List[str], limit: Optional[int] = None
    ) -> List[Strategy]:
        """
        Search strategies by tags.

        Args:
            tags: List of tags to search for
            limit: Maximum number of strategies to return

        Returns:
            List of strategies matching any of the tags
        """
        pass

    @abstractmethod
    async def get_top_performing(
        self,
        metric: str = "total_pnl",
        limit: int = 10,
        time_period_days: Optional[int] = None,
    ) -> List[Strategy]:
        """
        Get top performing strategies based on a specific metric.

        Args:
            metric: The performance metric to sort by
            limit: Maximum number of strategies to return
            time_period_days: Optional time period to consider

        Returns:
            List of top performing strategies
        """
        pass

    @abstractmethod
    async def update_performance(
        self, strategy_id: str, performance_data: Dict[str, Any]
    ) -> bool:
        """
        Update performance metrics for a strategy.

        Args:
            strategy_id: The strategy identifier
            performance_data: Performance data to update

        Returns:
            True if update successful, False otherwise
        """
        pass

    @abstractmethod
    async def activate_strategy(self, strategy_id: str) -> bool:
        """
        Activate a strategy.

        Args:
            strategy_id: The strategy identifier

        Returns:
            True if activation successful, False otherwise
        """
        pass

    @abstractmethod
    async def deactivate_strategy(self, strategy_id: str) -> bool:
        """
        Deactivate a strategy.

        Args:
            strategy_id: The strategy identifier

        Returns:
            True if deactivation successful, False otherwise
        """
        pass

    @abstractmethod
    async def archive_strategy(self, strategy_id: str) -> bool:
        """
        Archive a strategy.

        Args:
            strategy_id: The strategy identifier

        Returns:
            True if archiving successful, False otherwise
        """
        pass

    @abstractmethod
    async def clone_strategy(
        self,
        strategy_id: str,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Optional[Strategy]:
        """
        Clone an existing strategy with optional modifications.

        Args:
            strategy_id: The strategy to clone
            new_name: Name for the new strategy
            modifications: Optional modifications to apply

        Returns:
            The cloned strategy if successful, None otherwise
        """
        pass

    @abstractmethod
    async def get_strategy_statistics(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a strategy.

        Args:
            strategy_id: The strategy identifier

        Returns:
            Dictionary containing strategy statistics
        """
        pass

    @abstractmethod
    async def validate_strategy_parameters(self, strategy: Strategy) -> Dict[str, Any]:
        """
        Validate strategy parameters and configuration.

        Args:
            strategy: The strategy to validate

        Returns:
            Dictionary with validation results and any issues found
        """
        pass
