"""
Repository Configuration for Dependency Injection Container

This module configures the repository implementations for the DI container,
mapping interfaces to their MongoDB implementations.
"""

import logging
from typing import Dict, Any, Optional

from ..container.dependency_injection import DIContainer
from ..database.connection import DatabaseManager
from ..database.schema import initialize_database_schema

# Repository interfaces
from ...core.interfaces.signal_repository import ISignalRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...core.interfaces.strategy_repository import IStrategyRepository

# Repository implementations
from ..repositories.mongo_signal_repository import MongoSignalRepository
from ..repositories.mongo_market_data_repository import MongoMarketDataRepository
from ..repositories.mongo_strategy_repository import MongoStrategyRepository
from ..repositories.factory import IRepositoryFactory, MongoRepositoryFactory

logger = logging.getLogger(__name__)


class RepositoryConfiguration:
    """
    Repository configuration manager for dependency injection setup.
    """

    @staticmethod
    async def configure_repositories(container: DIContainer) -> None:
        """
        Configure repository dependencies in the DI container.

        Args:
            container: The DI container to configure
        """
        logger.info("Configuring repository dependencies...")

        try:
            # Register database manager as singleton
            container.register_singleton(DatabaseManager)

            # Register repository factory as singleton
            container.register_singleton(
                IRepositoryFactory, implementation_type=MongoRepositoryFactory
            )

            # Register repository implementations as scoped
            # (one instance per request/transaction scope)
            container.register_scoped(
                ISignalRepository, implementation_type=MongoSignalRepository
            )

            container.register_scoped(
                IMarketDataRepository, implementation_type=MongoMarketDataRepository
            )

            container.register_scoped(
                IStrategyRepository, implementation_type=MongoStrategyRepository
            )

            logger.info("Repository dependencies configured successfully")

        except Exception as e:
            logger.error(f"Failed to configure repository dependencies: {e}")
            raise

    @staticmethod
    async def initialize_database(container: DIContainer) -> None:
        """
        Initialize database schema and connections.

        Args:
            container: The DI container with database manager
        """
        logger.info("Initializing database schema...")

        try:
            # Get database manager from container
            db_manager = container.get_service(DatabaseManager)
            if not db_manager:
                raise ValueError("DatabaseManager not found in container")

            # Connect to database
            await db_manager.connect()

            # Initialize schema
            database = db_manager.database
            schema_result = await initialize_database_schema(database)

            logger.info(
                f"Database schema initialized: {schema_result['total_indexes_created']} indexes created"
            )

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @staticmethod
    async def create_configured_container() -> DIContainer:
        """
        Create a fully configured DI container with repositories.

        Returns:
            Configured DI container ready for use
        """
        logger.info("Creating configured DI container...")

        container = DIContainer()

        # Configure repositories
        await RepositoryConfiguration.configure_repositories(container)

        # Initialize database
        await RepositoryConfiguration.initialize_database(container)

        logger.info("DI container created and configured successfully")
        return container


# Convenience functions for common repository access patterns
class RepositoryServiceProvider:
    """
    Service provider for easy repository access from the DI container.
    """

    def __init__(self, container: DIContainer):
        """
        Initialize with DI container.

        Args:
            container: The configured DI container
        """
        self._container = container

    async def get_signal_repository(self, session=None) -> ISignalRepository:
        """
        Get signal repository instance.

        Args:
            session: Optional MongoDB session for transactions

        Returns:
            Signal repository instance
        """
        repository = self._container.get_service(ISignalRepository)
        if not repository:
            raise ValueError("ISignalRepository not found in container")

        # Cast to concrete implementation for session support
        if session and hasattr(repository, "set_session"):
            # Type ignore since we're checking hasattr for session support
            repository.set_session(session)  # type: ignore
        return repository

    async def get_market_data_repository(self, session=None) -> IMarketDataRepository:
        """
        Get market data repository instance.

        Args:
            session: Optional MongoDB session for transactions

        Returns:
            Market data repository instance
        """
        repository = self._container.get_service(IMarketDataRepository)
        if not repository:
            raise ValueError("IMarketDataRepository not found in container")

        # Cast to concrete implementation for session support
        if session and hasattr(repository, "set_session"):
            # Type ignore since we're checking hasattr for session support
            repository.set_session(session)  # type: ignore
        return repository

    async def get_strategy_repository(self, session=None) -> IStrategyRepository:
        """
        Get strategy repository instance.

        Args:
            session: Optional MongoDB session for transactions

        Returns:
            Strategy repository instance
        """
        repository = self._container.get_service(IStrategyRepository)
        if not repository:
            raise ValueError("IStrategyRepository not found in container")

        # Cast to concrete implementation for session support
        if session and hasattr(repository, "set_session"):
            # Type ignore since we're checking hasattr for session support
            repository.set_session(session)  # type: ignore
        return repository

    async def get_repository_factory(self) -> IRepositoryFactory:
        """
        Get repository factory instance.

        Returns:
            Repository factory instance
        """
        factory = self._container.get_service(IRepositoryFactory)
        if not factory:
            raise ValueError("IRepositoryFactory not found in container")
        return factory

    async def get_database_manager(self) -> DatabaseManager:
        """
        Get database manager instance.

        Returns:
            Database manager instance
        """
        manager = self._container.get_service(DatabaseManager)
        if not manager:
            raise ValueError("DatabaseManager not found in container")
        return manager
