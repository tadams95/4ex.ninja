"""
Core Interfaces Package - Repository and dependency injection interfaces

This package contains all the core interfaces that define the contracts
for data access and dependency injection in the clean architecture.
"""

from .repository import IBaseRepository, RepositoryError
from .signal_repository import ISignalRepository
from .market_data_repository import IMarketDataRepository
from .strategy_repository import IStrategyRepository
from .unit_of_work import (
    IUnitOfWork,
    IUnitOfWorkFactory,
    UnitOfWorkError,
    UnitOfWorkContext,
)
from .container import (
    IContainer,
    IServiceScope,
    IContainerBuilder,
    ServiceLifetime,
    ContainerError,
    CircularDependencyError,
)

__all__ = [
    # Base repository
    "IBaseRepository",
    "RepositoryError",
    # Entity repositories
    "ISignalRepository",
    "IMarketDataRepository",
    "IStrategyRepository",
    # Unit of work
    "IUnitOfWork",
    "IUnitOfWorkFactory",
    "UnitOfWorkError",
    "UnitOfWorkContext",
    # Dependency injection
    "IContainer",
    "IServiceScope",
    "IContainerBuilder",
    "ServiceLifetime",
    "ContainerError",
    "CircularDependencyError",
]
