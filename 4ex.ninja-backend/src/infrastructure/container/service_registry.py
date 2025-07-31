"""
Service Registry for tracking and managing service registrations.
"""

from typing import Dict, List, Type, TypeVar, Optional, Set, Any, Callable
import logging
from .types import ServiceDescriptor, ServiceLifetime

T = TypeVar("T")
logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Registry for managing service descriptors and their metadata.
    """

    def __init__(self):
        """Initialize empty service registry."""
        self._services: Dict[Type, List[ServiceDescriptor]] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._registration_order: List[Type] = []

    def register(self, descriptor: ServiceDescriptor[T]) -> None:
        """
        Register a service descriptor.

        Args:
            descriptor: Service descriptor to register
        """
        service_type = descriptor.service_type

        if service_type not in self._services:
            self._services[service_type] = []
            self._registration_order.append(service_type)

        self._services[service_type].append(descriptor)

        logger.debug(
            f"Registered service: {service_type.__name__} -> {descriptor.implementation_type.__name__ if descriptor.implementation_type else 'factory/instance'}"
        )

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable] = None,
        instance: Optional[T] = None,
    ) -> None:
        """
        Register a singleton service.

        Args:
            service_type: Service interface type
            implementation_type: Implementation type
            factory: Factory function
            instance: Pre-created instance
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON,
        )
        self.register(descriptor)

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable] = None,
    ) -> None:
        """
        Register a transient service.

        Args:
            service_type: Service interface type
            implementation_type: Implementation type
            factory: Factory function
        """
        if implementation_type is None and factory is None:
            # Default to self-registration
            implementation_type = service_type

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
        )
        self.register(descriptor)

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable] = None,
    ) -> None:
        """
        Register a scoped service.

        Args:
            service_type: Service interface type
            implementation_type: Implementation type
            factory: Factory function
        """
        if implementation_type is None and factory is None:
            implementation_type = service_type

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED,
        )
        self.register(descriptor)

    def get_descriptors(self, service_type: Type[T]) -> List[ServiceDescriptor[T]]:
        """
        Get all descriptors for a service type.

        Args:
            service_type: Service type to lookup

        Returns:
            List of service descriptors
        """
        return self._services.get(service_type, [])

    def get_descriptor(self, service_type: Type[T]) -> Optional[ServiceDescriptor[T]]:
        """
        Get the last registered descriptor for a service type.

        Args:
            service_type: Service type to lookup

        Returns:
            Service descriptor if found, None otherwise
        """
        descriptors = self.get_descriptors(service_type)
        return descriptors[-1] if descriptors else None

    def has_service(self, service_type: Type[T]) -> bool:
        """
        Check if service type is registered.

        Args:
            service_type: Service type to check

        Returns:
            True if service is registered
        """
        return service_type in self._services

    def get_registered_types(self) -> List[Type]:
        """
        Get all registered service types in registration order.

        Returns:
            List of registered service types
        """
        return self._registration_order.copy()

    def store_singleton_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Store singleton instance for later retrieval.

        Args:
            service_type: Service type
            instance: Instance to store
        """
        self._singleton_instances[service_type] = instance

    def get_singleton_instance(self, service_type: Type[T]) -> Optional[T]:
        """
        Get stored singleton instance.

        Args:
            service_type: Service type

        Returns:
            Singleton instance if exists
        """
        return self._singleton_instances.get(service_type)

    def clear_singletons(self) -> None:
        """Clear all singleton instances."""
        self._singleton_instances.clear()

    def clear(self) -> None:
        """Clear all registrations."""
        self._services.clear()
        self._singleton_instances.clear()
        self._registration_order.clear()

    def get_dependency_graph(self) -> Dict[Type, Set[Type]]:
        """
        Build dependency graph for registered services.

        Returns:
            Dictionary mapping service types to their dependencies
        """
        graph: Dict[Type, Set[Type]] = {}

        for service_type in self._registration_order:
            graph[service_type] = set()
            descriptors = self.get_descriptors(service_type)

            for descriptor in descriptors:
                if descriptor.implementation_type:
                    # Extract constructor dependencies via inspection
                    try:
                        import inspect

                        sig = inspect.signature(descriptor.implementation_type.__init__)
                        for param_name, param in sig.parameters.items():
                            if param_name != "self" and param.annotation != param.empty:
                                if param.annotation in self._services:
                                    graph[service_type].add(param.annotation)
                    except Exception as e:
                        logger.debug(
                            f"Could not extract dependencies for {service_type.__name__}: {e}"
                        )

        return graph

    def validate_dependencies(self) -> List[str]:
        """
        Validate service dependencies and detect issues.

        Returns:
            List of validation error messages
        """
        errors = []
        graph = self.get_dependency_graph()

        # Check for circular dependencies
        def has_cycle(node: Type, visited: Set[Type], rec_stack: Set[Type]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for service_type in self._registration_order:
            if service_type not in visited:
                if has_cycle(service_type, visited, set()):
                    errors.append(
                        f"Circular dependency detected involving {service_type.__name__}"
                    )

        # Check for missing dependencies
        for service_type, dependencies in graph.items():
            for dep in dependencies:
                if not self.has_service(dep):
                    errors.append(
                        f"Service {service_type.__name__} depends on unregistered service {dep.__name__}"
                    )

        return errors
