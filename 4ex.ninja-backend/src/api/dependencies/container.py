"""
Dependency Injection Container

FastAPI dependency injection setup for repositories and services.
"""

from functools import lru_cache
import os
import sys
from typing import Optional, Any

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Track if dependencies are available
DEPENDENCIES_AVAILABLE = False

# Try to import dependencies, but allow graceful fallback
try:
    # Add infrastructure path
    infrastructure_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "infrastructure"
    )
    if infrastructure_path not in sys.path:
        sys.path.append(infrastructure_path)

    from infrastructure.database.connection import DatabaseManager
    from infrastructure.repositories.factory import MongoRepositoryFactory

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some dependencies not available: {e}")
    print("FastAPI will start with mock dependencies")
    DatabaseManager = None
    MongoRepositoryFactory = None


class Container:
    """
    Dependency injection container for the application.
    """

    def __init__(self):
        self._database_manager: Optional[Any] = None
        self._repository_factory: Optional[Any] = None
        self._signal_repository: Optional[Any] = None
        self._market_data_repository: Optional[Any] = None
        self._strategy_repository: Optional[Any] = None
        self._initialized = False

    async def initialize(self):
        """Initialize all dependencies."""
        if self._initialized:
            return

        if not DEPENDENCIES_AVAILABLE:
            print("Warning: Dependencies not available, using mock implementations")
            self._initialized = True
            return

        try:
            # Initialize database manager
            if not DatabaseManager or not MongoRepositoryFactory:
                raise ImportError("Required dependencies not available")

            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            database_name = os.getenv("DATABASE_NAME", "forex_trading")

            self._database_manager = DatabaseManager()
            await self._database_manager.connect(mongodb_url, database_name)

            # Initialize repository factory
            self._repository_factory = MongoRepositoryFactory(self._database_manager)

            # Create repository instances
            self._signal_repository = (
                await self._repository_factory.create_signal_repository()
            )
            self._market_data_repository = (
                await self._repository_factory.create_market_data_repository()
            )
            self._strategy_repository = (
                await self._repository_factory.create_strategy_repository()
            )

            self._initialized = True
            print("Dependencies initialized successfully")

        except Exception as e:
            print(f"Failed to initialize dependencies: {e}")
            # Don't re-raise to allow app to start even without full DB connection

    async def cleanup(self):
        """Cleanup resources."""
        if self._database_manager and hasattr(self._database_manager, "disconnect"):
            await self._database_manager.disconnect()

    @property
    def database_manager(self) -> Optional[Any]:
        """Get database manager instance."""
        return self._database_manager

    @property
    def signal_repository(self) -> Optional[Any]:
        """Get signal repository instance."""
        return self._signal_repository

    @property
    def market_data_repository(self) -> Optional[Any]:
        """Get market data repository instance."""
        return self._market_data_repository

    @property
    def strategy_repository(self) -> Optional[Any]:
        """Get strategy repository instance."""
        return self._strategy_repository


# Global container instance
_container: Optional[Container] = None


@lru_cache()
def get_container() -> Container:
    """
    Get or create the global container instance.

    Returns:
        Container: Dependency injection container
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


# FastAPI dependency functions
async def get_signal_repository() -> Optional[Any]:
    """Dependency for signal repository."""
    container = get_container()
    if not container._initialized:
        await container.initialize()
    return container.signal_repository


async def get_market_data_repository() -> Optional[Any]:
    """Dependency for market data repository."""
    container = get_container()
    if not container._initialized:
        await container.initialize()
    return container.market_data_repository


async def get_strategy_repository() -> Optional[Any]:
    """Dependency for strategy repository."""
    container = get_container()
    if not container._initialized:
        await container.initialize()
    return container.strategy_repository


async def get_database_manager() -> Optional[Any]:
    """Dependency for database manager."""
    container = get_container()
    if not container._initialized:
        await container.initialize()
    return container.database_manager
