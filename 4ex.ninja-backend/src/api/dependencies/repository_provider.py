"""
Repository provider dependency for FastAPI.

This module provides dependency injection functions for repository access
in FastAPI routes using the repository service provider pattern.
"""

from typing import Optional
from fastapi import Depends

from ...infrastructure.configuration.repository_config import (
    RepositoryServiceProvider,
    RepositoryConfiguration,
)


# Global service provider instance
_service_provider: Optional[RepositoryServiceProvider] = None


async def initialize_service_provider() -> None:
    """Initialize the global service provider instance."""
    global _service_provider
    if _service_provider is None:
        # Create configured DI container
        container = await RepositoryConfiguration.create_configured_container()
        _service_provider = RepositoryServiceProvider(container)


async def get_repository_provider() -> RepositoryServiceProvider:
    """
    FastAPI dependency to get the repository service provider.

    Returns:
        RepositoryServiceProvider instance for dependency injection
    """
    global _service_provider
    if _service_provider is None:
        await initialize_service_provider()
    return _service_provider  # type: ignore
