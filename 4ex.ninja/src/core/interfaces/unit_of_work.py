"""
Unit of Work Interface - Transaction management for repository operations

This module defines the Unit of Work pattern interface for managing
transactions across multiple repository operations, ensuring data consistency
and ACID compliance.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, AsyncContextManager
from contextlib import asynccontextmanager

from .signal_repository import ISignalRepository
from .market_data_repository import IMarketDataRepository
from .strategy_repository import IStrategyRepository


class IUnitOfWork(ABC):
    """
    Unit of Work interface for managing transactions across repositories.

    This interface provides a way to group multiple repository operations
    into a single transaction, ensuring atomicity and consistency.
    """

    # Repository properties - these will be injected by the concrete implementation
    signals: ISignalRepository
    market_data: IMarketDataRepository
    strategies: IStrategyRepository

    @abstractmethod
    async def __aenter__(self):
        """
        Async context manager entry - start transaction.

        Returns:
            Self for use in async with statement
        """
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit - commit or rollback transaction.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        pass

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit the current transaction.

        Persists all changes made within the unit of work to the database.

        Raises:
            UnitOfWorkError: If commit fails
        """
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback the current transaction.

        Reverts all changes made within the unit of work.

        Raises:
            UnitOfWorkError: If rollback fails
        """
        pass

    @abstractmethod
    async def begin(self) -> None:
        """
        Begin a new transaction.

        Raises:
            UnitOfWorkError: If transaction start fails
        """
        pass

    @abstractmethod
    async def is_active(self) -> bool:
        """
        Check if a transaction is currently active.

        Returns:
            True if transaction is active, False otherwise
        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """
        Flush pending changes without committing the transaction.

        This is useful for ensuring changes are visible within the same
        transaction (e.g., for getting generated IDs).

        Raises:
            UnitOfWorkError: If flush fails
        """
        pass

    @abstractmethod
    async def refresh(self, entity: Any) -> None:
        """
        Refresh an entity from the database.

        Args:
            entity: The entity to refresh

        Raises:
            UnitOfWorkError: If refresh fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear the session/context without committing changes.

        This removes all pending changes and clears the session state.
        """
        pass


class IUnitOfWorkFactory(ABC):
    """
    Factory interface for creating Unit of Work instances.

    This allows for different implementations of Unit of Work
    (e.g., different database providers) while maintaining
    the same interface.
    """

    @abstractmethod
    def create(self) -> IUnitOfWork:
        """
        Create a new Unit of Work instance.

        Returns:
            A new Unit of Work instance
        """
        pass

    @abstractmethod
    def create_context(self) -> AsyncContextManager[IUnitOfWork]:
        """
        Create a Unit of Work instance as an async context manager.

        This is the preferred way to use Unit of Work as it ensures
        proper cleanup and transaction management.

        Returns:
            Async context manager for Unit of Work
        """
        pass


class UnitOfWorkError(Exception):
    """
    Custom exception for Unit of Work operations.

    This exception should be raised when Unit of Work operations fail,
    providing clear information about transaction management issues.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message}. Original error: {str(self.original_error)}"
        return self.message


# Convenience type for async context manager usage
UnitOfWorkContext = AsyncContextManager[IUnitOfWork]
