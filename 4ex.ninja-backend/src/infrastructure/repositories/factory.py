"""
Repository Factory Pattern Implementation

This module provides a factory pattern interface for creating repository instances
with proper dependency injection and configuration management.

Note: This is a foundational implementation. Concrete repository classes
will be implemented when entity classes are available.
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

from ...core.interfaces.repository import IBaseRepository
from ...core.interfaces.signal_repository import ISignalRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...core.interfaces.strategy_repository import IStrategyRepository

from .mongo_base_repository import MongoBaseRepository
from ..database.connection import DatabaseManager
from ..database.config import DatabaseConfigurationManager

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for repository types
T = TypeVar("T")
RepositoryType = TypeVar("RepositoryType", bound=IBaseRepository)


class IRepositoryFactory(ABC):
    """
    Interface for repository factory pattern.

    Defines the contract for creating repository instances with proper
    dependency injection and configuration.
    """

    @abstractmethod
    async def create_signal_repository(
        self, session: Optional[Any] = None
    ) -> ISignalRepository:
        """Create a signal repository instance."""
        pass

    @abstractmethod
    async def create_market_data_repository(
        self, session: Optional[Any] = None
    ) -> IMarketDataRepository:
        """Create a market data repository instance."""
        pass

    @abstractmethod
    async def create_strategy_repository(
        self, session: Optional[Any] = None
    ) -> IStrategyRepository:
        """Create a strategy repository instance."""
        pass

    @abstractmethod
    async def create_repository(
        self, repository_interface: Type[RepositoryType], session: Optional[Any] = None
    ) -> RepositoryType:
        """Create a generic repository instance."""
        pass

    @abstractmethod
    async def get_database_manager(self) -> DatabaseManager:
        """Get the database manager instance."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up factory resources."""
        pass


class MongoRepositoryFactory(IRepositoryFactory):
    """
    MongoDB implementation of the repository factory pattern.

    Creates MongoDB-based repository instances with proper configuration
    and dependency injection.

    Note: Concrete implementations will be added when entity classes are available.
    """

    def __init__(self, config_manager: Optional[DatabaseConfigurationManager] = None):
        """
        Initialize the repository factory.

        Args:
            config_manager: Optional database configuration manager
        """
        self._config_manager = config_manager or DatabaseConfigurationManager()
        self._database_manager: Optional[DatabaseManager] = None
        self._repositories: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the factory and database connections."""
        if self._initialized:
            return

        try:
            # Get database configuration
            config = self._config_manager.get_database_config()

            # Initialize database manager
            self._database_manager = DatabaseManager(config)
            await self._database_manager.connect()

            self._initialized = True
            logger.info("Repository factory initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize repository factory: {e}")
            raise

    async def create_signal_repository(
        self, session: Optional[Any] = None
    ) -> ISignalRepository:
        """Create a signal repository instance."""
        await self._ensure_initialized()

        # TODO: Implement when Signal entity class is available
        # For now, this is a placeholder that will raise NotImplementedError
        raise NotImplementedError(
            "Signal repository implementation pending entity class availability"
        )

    async def create_market_data_repository(
        self, session: Optional[Any] = None
    ) -> IMarketDataRepository:
        """Create a market data repository instance."""
        await self._ensure_initialized()

        # TODO: Implement when MarketData entity class is available
        # For now, this is a placeholder that will raise NotImplementedError
        raise NotImplementedError(
            "Market data repository implementation pending entity class availability"
        )

    async def create_strategy_repository(
        self, session: Optional[Any] = None
    ) -> IStrategyRepository:
        """Create a strategy repository instance."""
        await self._ensure_initialized()

        # TODO: Implement when Strategy entity class is available
        # For now, this is a placeholder that will raise NotImplementedError
        raise NotImplementedError(
            "Strategy repository implementation pending entity class availability"
        )

    async def create_repository(
        self, repository_interface: Type[RepositoryType], session: Optional[Any] = None
    ) -> RepositoryType:
        """Create a generic repository instance."""
        await self._ensure_initialized()

        # Map interfaces to implementations
        repository_map = {
            ISignalRepository: self.create_signal_repository,
            IMarketDataRepository: self.create_market_data_repository,
            IStrategyRepository: self.create_strategy_repository,
        }

        if repository_interface in repository_map:
            return await repository_map[repository_interface](session)

        raise ValueError(f"Unknown repository interface: {repository_interface}")

    async def get_database_manager(self) -> DatabaseManager:
        """Get the database manager instance."""
        await self._ensure_initialized()
        if self._database_manager is None:
            raise RuntimeError("Database manager not initialized")
        return self._database_manager

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        try:
            # Clear repository cache
            self._repositories.clear()

            # Disconnect database manager
            if self._database_manager:
                await self._database_manager.disconnect()
                self._database_manager = None

            self._initialized = False
            logger.info("Repository factory cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during factory cleanup: {e}")

    async def _ensure_initialized(self) -> None:
        """Ensure the factory is initialized."""
        if not self._initialized:
            await self.initialize()


# Factory singleton instance
_factory_instance: Optional[MongoRepositoryFactory] = None


async def get_repository_factory() -> MongoRepositoryFactory:
    """
    Get the singleton repository factory instance.

    Returns:
        Repository factory instance
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = MongoRepositoryFactory()
        await _factory_instance.initialize()

    return _factory_instance


async def cleanup_repository_factory() -> None:
    """Clean up the repository factory singleton."""
    global _factory_instance

    if _factory_instance:
        await _factory_instance.cleanup()
        _factory_instance = None
