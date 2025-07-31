"""
Service Lifetime Enumeration and Core DI Types
"""

from enum import Enum
from typing import TypeVar, Generic, Callable, Any, Dict, Type, Optional, Protocol
from abc import ABC, abstractmethod

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Service lifetime management options."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor(Generic[T]):
    """Describes how a service should be created and managed."""

    def __init__(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        """
        Initialize service descriptor.

        Args:
            service_type: The service interface or abstract type
            implementation_type: Concrete implementation type
            factory: Factory function to create instances
            instance: Pre-created instance (for singletons)
            lifetime: Service lifetime management
        """
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime

        # Validation
        creation_methods = sum(
            [implementation_type is not None, factory is not None, instance is not None]
        )

        if creation_methods != 1:
            raise ValueError(
                "Exactly one of implementation_type, factory, or instance must be provided"
            )


class IServiceProvider(Protocol):
    """Interface for service provider/resolver."""

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance by type."""
        ...

    def get_required_service(self, service_type: Type[T]) -> T:
        """Get required service instance by type (raises if not found)."""
        ...

    def get_services(self, service_type: Type[T]) -> list[T]:
        """Get all service instances of the given type."""
        ...


class ServiceResolutionError(Exception):
    """Raised when service resolution fails."""

    pass


class CircularDependencyError(ServiceResolutionError):
    """Raised when circular dependency is detected."""

    pass
