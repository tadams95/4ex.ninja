"""
Dependency Injection Container Implementation
Main DI container for service resolution and lifecycle management.
"""

from typing import Type, TypeVar, Optional, List, Dict, Any, Set, Callable
import inspect
import logging
from threading import Lock
from .types import (
    ServiceDescriptor,
    ServiceLifetime,
    IServiceProvider,
    ServiceResolutionError,
    CircularDependencyError,
)
from .service_registry import ServiceRegistry

T = TypeVar("T")
logger = logging.getLogger(__name__)


class DIContainer(IServiceProvider):
    """
    Dependency Injection Container with automatic constructor injection.
    """

    def __init__(self, parent: Optional["DIContainer"] = None):
        """
        Initialize DI container.

        Args:
            parent: Parent container for hierarchical resolution
        """
        self._registry = ServiceRegistry()
        self._parent = parent
        self._scoped_instances: Dict[Type, Any] = {}
        self._resolution_stack: Set[Type] = set()
        self._lock = Lock()

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable] = None,
        instance: Optional[T] = None,
    ) -> "DIContainer":
        """
        Register singleton service.

        Args:
            service_type: Service interface type
            implementation_type: Implementation type
            factory: Factory function
            instance: Pre-created instance

        Returns:
            Self for method chaining
        """
        self._registry.register_singleton(
            service_type, implementation_type, factory, instance
        )
        return self

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable] = None,
    ) -> "DIContainer":
        """
        Register transient service.

        Args:
            service_type: Service interface type
            implementation_type: Implementation type
            factory: Factory function

        Returns:
            Self for method chaining
        """
        self._registry.register_transient(service_type, implementation_type, factory)
        return self

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable] = None,
    ) -> "DIContainer":
        """
        Register scoped service.

        Args:
            service_type: Service interface type
            implementation_type: Implementation type
            factory: Factory function

        Returns:
            Self for method chaining
        """
        self._registry.register_scoped(service_type, implementation_type, factory)
        return self

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Get service instance by type.

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance or None if not found
        """
        try:
            return self.get_required_service(service_type)
        except ServiceResolutionError:
            return None

    def get_required_service(self, service_type: Type[T]) -> T:
        """
        Get required service instance by type.

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance

        Raises:
            ServiceResolutionError: If service cannot be resolved
        """
        with self._lock:
            # Check for circular dependency
            if service_type in self._resolution_stack:
                cycle_path = " -> ".join([t.__name__ for t in self._resolution_stack])
                raise CircularDependencyError(
                    f"Circular dependency detected: {cycle_path} -> {service_type.__name__}"
                )

            try:
                self._resolution_stack.add(service_type)
                return self._resolve_service(service_type)
            finally:
                self._resolution_stack.discard(service_type)

    def get_services(self, service_type: Type[T]) -> List[T]:
        """
        Get all service instances of the given type.

        Args:
            service_type: Service type to resolve

        Returns:
            List of service instances
        """
        descriptors = self._registry.get_descriptors(service_type)
        services = []

        for descriptor in descriptors:
            service = self._create_service_instance(descriptor)
            if service is not None:
                services.append(service)

        return services

    def create_scope(self) -> "DIContainer":
        """
        Create a new scoped container.

        Returns:
            New scoped container with this container as parent
        """
        return DIContainer(parent=self)

    def dispose_scope(self) -> None:
        """Dispose scoped instances and clear scope cache."""
        self._scoped_instances.clear()

    def validate(self) -> List[str]:
        """
        Validate container configuration.

        Returns:
            List of validation error messages
        """
        return self._registry.validate_dependencies()

    def _resolve_service(self, service_type: Type[T]) -> T:
        """
        Internal service resolution logic.

        Args:
            service_type: Service type to resolve

        Returns:
            Service instance

        Raises:
            ServiceResolutionError: If service cannot be resolved
        """
        # Try to resolve from current container
        descriptor = self._registry.get_descriptor(service_type)

        if descriptor is not None:
            instance = self._create_service_instance(descriptor)
            if instance is not None:
                return instance

        # Try parent container
        if self._parent is not None:
            return self._parent.get_required_service(service_type)

        # Service not found
        raise ServiceResolutionError(
            f"Service of type {service_type.__name__} is not registered"
        )

    def _create_service_instance(self, descriptor: ServiceDescriptor[T]) -> Optional[T]:
        """
        Create service instance from descriptor.

        Args:
            descriptor: Service descriptor

        Returns:
            Service instance
        """
        try:
            # Handle singleton lifecycle
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                return self._create_singleton_instance(descriptor)

            # Handle scoped lifecycle
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                return self._create_scoped_instance(descriptor)

            # Handle transient lifecycle
            else:
                return self._create_transient_instance(descriptor)

        except Exception as e:
            logger.error(
                f"Failed to create instance of {descriptor.service_type.__name__}: {e}"
            )
            raise ServiceResolutionError(f"Failed to create instance: {e}")

    def _create_singleton_instance(self, descriptor: ServiceDescriptor[T]) -> T:
        """Create or return singleton instance."""
        # Check if instance already exists
        if descriptor.instance is not None:
            return descriptor.instance

        # Check registry cache
        cached = self._registry.get_singleton_instance(descriptor.service_type)
        if cached is not None:
            return cached

        # Create new instance
        instance = self._create_new_instance(descriptor)

        # Cache the instance
        self._registry.store_singleton_instance(descriptor.service_type, instance)

        return instance

    def _create_scoped_instance(self, descriptor: ServiceDescriptor[T]) -> T:
        """Create or return scoped instance."""
        service_type = descriptor.service_type

        # Check scope cache
        if service_type in self._scoped_instances:
            return self._scoped_instances[service_type]

        # Create new instance
        instance = self._create_new_instance(descriptor)

        # Cache in scope
        self._scoped_instances[service_type] = instance

        return instance

    def _create_transient_instance(self, descriptor: ServiceDescriptor[T]) -> T:
        """Create new transient instance."""
        return self._create_new_instance(descriptor)

    def _create_new_instance(self, descriptor: ServiceDescriptor[T]) -> T:
        """
        Create new service instance using descriptor configuration.

        Args:
            descriptor: Service descriptor

        Returns:
            New service instance
        """
        # Use pre-created instance
        if descriptor.instance is not None:
            return descriptor.instance

        # Use factory function
        if descriptor.factory is not None:
            return self._invoke_factory(descriptor.factory)

        # Use implementation type with constructor injection
        if descriptor.implementation_type is not None:
            return self._create_with_constructor_injection(
                descriptor.implementation_type
            )

        raise ServiceResolutionError(
            f"No creation method available for {descriptor.service_type.__name__}"
        )

    def _invoke_factory(self, factory: Callable) -> Any:
        """
        Invoke factory function with dependency injection.

        Args:
            factory: Factory function

        Returns:
            Factory result
        """
        try:
            # Get factory signature
            sig = inspect.signature(factory)
            kwargs = {}

            # Resolve dependencies
            for param_name, param in sig.parameters.items():
                if param.annotation != param.empty:
                    dependency = self.get_required_service(param.annotation)
                    kwargs[param_name] = dependency

            return factory(**kwargs)

        except Exception as e:
            raise ServiceResolutionError(f"Factory invocation failed: {e}")

    def _create_with_constructor_injection(self, implementation_type: Type[T]) -> T:
        """
        Create instance with constructor dependency injection.

        Args:
            implementation_type: Implementation type to instantiate

        Returns:
            New instance with injected dependencies
        """
        try:
            # Get constructor signature
            sig = inspect.signature(implementation_type.__init__)
            kwargs = {}

            # Resolve constructor dependencies
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                if param.annotation != param.empty:
                    # Try to resolve dependency
                    dependency = self.get_service(param.annotation)
                    if dependency is not None:
                        kwargs[param_name] = dependency
                    elif param.default == param.empty:
                        # Required parameter without default
                        raise ServiceResolutionError(
                            f"Cannot resolve required dependency {param.annotation.__name__} "
                            f"for {implementation_type.__name__}.{param_name}"
                        )

            return implementation_type(**kwargs)

        except Exception as e:
            raise ServiceResolutionError(
                f"Constructor injection failed for {implementation_type.__name__}: {e}"
            )

    def get_registration_info(self) -> Dict[str, Any]:
        """
        Get container registration information for debugging.

        Returns:
            Dictionary with registration details
        """
        registered_types = self._registry.get_registered_types()

        info = {
            "registered_services": len(registered_types),
            "services": [],
            "dependency_graph": {},
        }

        for service_type in registered_types:
            descriptor = self._registry.get_descriptor(service_type)
            if descriptor:
                service_info = {
                    "service_type": service_type.__name__,
                    "implementation_type": (
                        descriptor.implementation_type.__name__
                        if descriptor.implementation_type
                        else None
                    ),
                    "lifetime": descriptor.lifetime.value,
                    "has_factory": descriptor.factory is not None,
                    "has_instance": descriptor.instance is not None,
                }
                info["services"].append(service_info)

        # Add dependency graph
        graph = self._registry.get_dependency_graph()
        for service_type, deps in graph.items():
            info["dependency_graph"][service_type.__name__] = [
                dep.__name__ for dep in deps
            ]

        return info
