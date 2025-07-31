"""
Dependency Injection Container Interface - Service registration and resolution

This module defines the dependency injection container interface for managing
service registration, resolution, and lifecycle within the application.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Type, Any, Optional, Callable, Dict, Union
from enum import Enum

# Generic type for services
T = TypeVar("T")


class ServiceLifetime(Enum):
    """
    Enumeration for service lifetime management.

    - SINGLETON: Single instance for the entire application lifetime
    - SCOPED: Single instance per scope (e.g., per request)
    - TRANSIENT: New instance every time the service is requested
    """

    SINGLETON = "SINGLETON"
    SCOPED = "SCOPED"
    TRANSIENT = "TRANSIENT"


class IContainer(ABC):
    """
    Dependency injection container interface.

    This interface provides the contract for service registration and resolution,
    enabling loose coupling and testability throughout the application.
    """

    @abstractmethod
    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None,
    ) -> "IContainer":
        """
        Register a service with singleton lifetime.

        Args:
            service_type: The service interface or class type
            implementation: The concrete implementation (if different from service_type)
            factory: Factory function to create the service
            instance: Pre-created instance to use

        Returns:
            Self for method chaining

        Raises:
            ContainerError: If registration fails or conflicts
        """
        pass

    @abstractmethod
    def register_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
    ) -> "IContainer":
        """
        Register a service with scoped lifetime.

        Args:
            service_type: The service interface or class type
            implementation: The concrete implementation (if different from service_type)
            factory: Factory function to create the service

        Returns:
            Self for method chaining

        Raises:
            ContainerError: If registration fails or conflicts
        """
        pass

    @abstractmethod
    def register_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
    ) -> "IContainer":
        """
        Register a service with transient lifetime.

        Args:
            service_type: The service interface or class type
            implementation: The concrete implementation (if different from service_type)
            factory: Factory function to create the service

        Returns:
            Self for method chaining

        Raises:
            ContainerError: If registration fails or conflicts
        """
        pass

    @abstractmethod
    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> "IContainer":
        """
        Register a service with specified lifetime.

        Args:
            service_type: The service interface or class type
            implementation: The concrete implementation (if different from service_type)
            factory: Factory function to create the service
            instance: Pre-created instance (only for singleton)
            lifetime: Service lifetime management

        Returns:
            Self for method chaining

        Raises:
            ContainerError: If registration fails or conflicts
        """
        pass

    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance

        Raises:
            ContainerError: If service cannot be resolved
        """
        pass

    @abstractmethod
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service instance without raising an exception.

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance if available, None otherwise
        """
        pass

    @abstractmethod
    def is_registered(self, service_type: Type[T]) -> bool:
        """
        Check if a service type is registered.

        Args:
            service_type: The service type to check

        Returns:
            True if service is registered, False otherwise
        """
        pass

    @abstractmethod
    def unregister(self, service_type: Type[T]) -> bool:
        """
        Unregister a service type.

        Args:
            service_type: The service type to unregister

        Returns:
            True if service was unregistered, False if not found
        """
        pass

    @abstractmethod
    def create_scope(self) -> "IServiceScope":
        """
        Create a new service scope.

        Returns:
            New service scope for scoped service management
        """
        pass

    @abstractmethod
    def get_registered_services(self) -> Dict[Type, Dict[str, Any]]:
        """
        Get information about all registered services.

        Returns:
            Dictionary mapping service types to registration information
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all service registrations.

        This removes all registered services and clears singleton instances.
        """
        pass


class IServiceScope(ABC):
    """
    Service scope interface for managing scoped services.

    A scope provides a way to manage the lifetime of scoped services,
    typically used for request-scoped dependencies.
    """

    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service within this scope.

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance

        Raises:
            ContainerError: If service cannot be resolved
        """
        pass

    @abstractmethod
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service within this scope.

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance if available, None otherwise
        """
        pass

    @abstractmethod
    def dispose(self) -> None:
        """
        Dispose the scope and all scoped services.

        This should be called when the scope is no longer needed
        (e.g., at the end of a request).
        """
        pass

    @abstractmethod
    def __enter__(self) -> "IServiceScope":
        """
        Context manager entry.

        Returns:
            Self for use in with statement
        """
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit - automatically dispose the scope.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        pass


class IContainerBuilder(ABC):
    """
    Container builder interface for configuring services before building the container.

    This provides a fluent interface for service registration and configuration.
    """

    @abstractmethod
    def add_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None,
    ) -> "IContainerBuilder":
        """
        Add a singleton service registration.

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def add_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
    ) -> "IContainerBuilder":
        """
        Add a scoped service registration.

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def add_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
    ) -> "IContainerBuilder":
        """
        Add a transient service registration.

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def configure_module(
        self, module_configurator: Callable[["IContainerBuilder"], None]
    ) -> "IContainerBuilder":
        """
        Configure services using a module configurator function.

        Args:
            module_configurator: Function that configures services

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def build(self) -> IContainer:
        """
        Build the container with all registered services.

        Returns:
            Configured container instance

        Raises:
            ContainerError: If container build fails
        """
        pass


class ContainerError(Exception):
    """
    Custom exception for dependency injection container operations.

    This exception should be raised when container operations fail,
    providing clear information about service registration and resolution issues.
    """

    def __init__(
        self,
        message: str,
        service_type: Optional[Type] = None,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.service_type = service_type
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        service_info = (
            f" for service {self.service_type.__name__}" if self.service_type else ""
        )
        error_info = (
            f". Original error: {str(self.original_error)}"
            if self.original_error
            else ""
        )
        return f"{self.message}{service_info}{error_info}"


class CircularDependencyError(ContainerError):
    """
    Exception raised when a circular dependency is detected.
    """

    def __init__(self, dependency_chain: list):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join([dep.__name__ for dep in dependency_chain])
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message)
