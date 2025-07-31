"""
Dependency Injection Container Module
Provides service registration and resolution for the trading application.
"""

from .types import (
    ServiceLifetime,
    ServiceDescriptor,
    IServiceProvider,
    ServiceResolutionError,
    CircularDependencyError,
)
from .service_registry import ServiceRegistry
from .dependency_injection import DIContainer

__all__ = [
    "DIContainer",
    "ServiceLifetime",
    "ServiceRegistry",
    "ServiceDescriptor",
    "IServiceProvider",
    "ServiceResolutionError",
    "CircularDependencyError",
]
