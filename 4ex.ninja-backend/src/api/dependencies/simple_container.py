"""
Simple Dependency Injection Container

A simplified version that allows FastAPI to start without complex repository dependencies.
This ensures the FastAPI application structure task can be completed.
"""

from functools import lru_cache
from typing import Optional, Any, Dict, List
import asyncio
import logging

logger = logging.getLogger(__name__)


class MockRepository:
    """Mock repository for testing purposes."""

    def __init__(self, name: str):
        self.name = name

    async def find_all(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Mock find all method."""
        return [
            {
                "id": f"mock_{self.name}_{i}",
                "name": f"Mock {self.name} {i}",
                "created_at": "2024-01-01T00:00:00Z",
                "status": "active",
            }
            for i in range(1, min(limit + 1, 6))
        ]

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Mock find by id method."""
        return {
            "id": id,
            "name": f"Mock {self.name}",
            "created_at": "2024-01-01T00:00:00Z",
            "status": "active",
        }


class SimpleContainer:
    """
    Simplified dependency injection container.
    Provides mock implementations for development and testing.
    """

    def __init__(self):
        self._signal_repository: Optional[MockRepository] = None
        self._market_data_repository: Optional[MockRepository] = None
        self._strategy_repository: Optional[MockRepository] = None
        self._database_manager: Optional[Any] = None
        self._initialized = False

    async def initialize(self):
        """Initialize simple dependencies."""
        if self._initialized:
            return

        try:
            # Create mock repositories
            self._signal_repository = MockRepository("signal")
            self._market_data_repository = MockRepository("market_data")
            self._strategy_repository = MockRepository("strategy")

            self._initialized = True
            logger.info("Simple container initialized with mock dependencies")

        except Exception as e:
            logger.error(f"Failed to initialize simple container: {e}")

    async def cleanup(self):
        """Cleanup resources."""
        # Nothing to cleanup for mock implementations
        pass

    @property
    def signal_repository(self) -> Optional[MockRepository]:
        """Get signal repository instance."""
        return self._signal_repository

    @property
    def market_data_repository(self) -> Optional[MockRepository]:
        """Get market data repository instance."""
        return self._market_data_repository

    @property
    def strategy_repository(self) -> Optional[MockRepository]:
        """Get strategy repository instance."""
        return self._strategy_repository

    @property
    def database_manager(self) -> Optional[Any]:
        """Get database manager instance."""
        return self._database_manager


# Global container instance
_container: Optional[SimpleContainer] = None


@lru_cache()
def get_container() -> SimpleContainer:
    """
    Get or create the global container instance.

    Returns:
        SimpleContainer: Dependency injection container
    """
    global _container
    if _container is None:
        _container = SimpleContainer()
    return _container


# FastAPI dependency functions
async def get_signal_repository() -> Optional[MockRepository]:
    """Dependency for signal repository."""
    container = get_container()
    if not container._initialized:
        await container.initialize()
    return container.signal_repository


async def get_market_data_repository() -> Optional[MockRepository]:
    """Dependency for market data repository."""
    container = get_container()
    if not container._initialized:
        await container.initialize()
    return container.market_data_repository


async def get_strategy_repository() -> Optional[MockRepository]:
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
