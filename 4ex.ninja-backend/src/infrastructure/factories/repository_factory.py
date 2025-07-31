"""
Repository Factory for Dynamic Repository Creation
Provides factory pattern for creating repository instances based on configuration.
"""

from typing import Type, TypeVar, Dict, Any, Optional
import logging
from abc import ABC

# Import repository interfaces
from ...core.interfaces.signal_repository import ISignalRepository
from ...core.interfaces.market_data_repository import IMarketDataRepository
from ...core.interfaces.strategy_repository import IStrategyRepository

# Import repository implementations
from ..repositories.mongo_signal_repository import MongoSignalRepository
from ..repositories.mongo_market_data_repository import MongoMarketDataRepository
from ..repositories.mongo_strategy_repository import MongoStrategyRepository

# Import configuration
from .repository_configuration import RepositoryConfiguration, RepositoryType

T = TypeVar("T")
logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Factory for creating repository instances based on configuration.
    Supports multiple repository implementations and automatic dependency injection.
    """

    def __init__(self, configuration: RepositoryConfiguration):
        """
        Initialize repository factory.

        Args:
            configuration: Repository configuration
        """
        self.configuration = configuration
        self._repositories: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

        # Validate configuration
        errors = configuration.validate()
        if errors:
            raise ValueError(f"Invalid repository configuration: {', '.join(errors)}")

    def create_signal_repository(self) -> ISignalRepository:
        """
        Create signal repository instance.

        Returns:
            Signal repository implementation
        """
        return self._create_repository(ISignalRepository)

    def create_market_data_repository(self) -> IMarketDataRepository:
        """
        Create market data repository instance.

        Returns:
            Market data repository implementation
        """
        return self._create_repository(IMarketDataRepository)

    def create_strategy_repository(self) -> IStrategyRepository:
        """
        Create strategy repository instance.

        Returns:
            Strategy repository implementation
        """
        return self._create_repository(IStrategyRepository)

    def get_singleton_repository(self, repository_type: Type[T]) -> T:
        """
        Get singleton repository instance.

        Args:
            repository_type: Repository interface type

        Returns:
            Singleton repository instance
        """
        if repository_type in self._singletons:
            return self._singletons[repository_type]

        repository = self._create_repository(repository_type)
        self._singletons[repository_type] = repository
        return repository

    def _create_repository(self, repository_interface: Type[T]) -> T:
        """
        Create repository instance based on interface type and configuration.

        Args:
            repository_interface: Repository interface type

        Returns:
            Repository implementation instance
        """
        implementation_class = self._get_implementation_class(repository_interface)

        if implementation_class is None:
            raise ValueError(
                f"No implementation found for {repository_interface.__name__}"
            )

        # Create repository with configuration
        try:
            repository = implementation_class(
                database_config=self.configuration.database,
                collection_prefix=self.configuration.collection_prefix,
            )

            logger.info(
                f"Created {repository_interface.__name__} -> {implementation_class.__name__}"
            )
            return repository

        except Exception as e:
            logger.error(f"Failed to create {repository_interface.__name__}: {e}")
            raise RuntimeError(f"Repository creation failed: {e}")

    def _get_implementation_class(self, repository_interface: Type) -> Optional[Type]:
        """
        Get implementation class for repository interface.

        Args:
            repository_interface: Repository interface type

        Returns:
            Implementation class or None if not found
        """
        # MongoDB implementations
        if self.configuration.repository_type == RepositoryType.MONGODB:
            mongodb_mappings = {
                ISignalRepository: MongoSignalRepository,
                IMarketDataRepository: MongoMarketDataRepository,
                IStrategyRepository: MongoStrategyRepository,
            }
            return mongodb_mappings.get(repository_interface)

        # Memory implementations (for testing)
        elif self.configuration.repository_type == RepositoryType.MEMORY:
            # Memory implementations are not yet implemented
            # This will be implemented in future phases
            logger.warning("Memory repository implementations not yet available")
            return None

        # Future implementations
        elif self.configuration.repository_type == RepositoryType.POSTGRESQL:
            logger.warning("PostgreSQL repository implementations not yet available")
            return None

        elif self.configuration.repository_type == RepositoryType.SQLITE:
            logger.warning("SQLite repository implementations not yet available")
            return None

        return None

    def register_custom_implementation(
        self, repository_interface: Type[T], implementation_class: Type[T]
    ) -> None:
        """
        Register custom repository implementation.

        Args:
            repository_interface: Repository interface type
            implementation_class: Implementation class
        """
        if not issubclass(implementation_class, repository_interface):
            raise ValueError(
                f"{implementation_class.__name__} does not implement {repository_interface.__name__}"
            )

        self._repositories[repository_interface] = implementation_class
        logger.info(
            f"Registered custom implementation: {repository_interface.__name__} -> {implementation_class.__name__}"
        )

    def create_repositories(self) -> Dict[Type, Any]:
        """
        Create all repository instances.

        Returns:
            Dictionary mapping repository interfaces to implementations
        """
        repositories = {}

        try:
            repositories[ISignalRepository] = self.create_signal_repository()
            repositories[IMarketDataRepository] = self.create_market_data_repository()
            repositories[IStrategyRepository] = self.create_strategy_repository()

            logger.info(f"Created {len(repositories)} repository instances")
            return repositories

        except Exception as e:
            logger.error(f"Failed to create repositories: {e}")
            raise

    def test_connections(self) -> Dict[str, bool]:
        """
        Test repository connections.

        Returns:
            Dictionary mapping repository names to connection status
        """
        results = {}

        # Test each repository type
        repository_types = [
            ("SignalRepository", ISignalRepository),
            ("MarketDataRepository", IMarketDataRepository),
            ("StrategyRepository", IStrategyRepository),
        ]

        for name, repo_type in repository_types:
            try:
                repo = self._create_repository(repo_type)

                # Test connection if method exists
                if hasattr(repo, "test_connection"):
                    results[name] = repo.test_connection()
                else:
                    # Try a simple operation
                    if hasattr(repo, "count"):
                        # Async method handling
                        import asyncio

                        if asyncio.iscoroutinefunction(repo.count):
                            # Cannot test async in sync context
                            results[name] = True
                        else:
                            repo.count()
                            results[name] = True
                    else:
                        results[name] = True

            except Exception as e:
                logger.error(f"Connection test failed for {name}: {e}")
                results[name] = False

        return results

    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get repository factory information.

        Returns:
            Dictionary with factory information
        """
        return {
            "repository_type": self.configuration.repository_type.value,
            "database_host": (
                self.configuration.database.host
                if self.configuration.database
                else None
            ),
            "database_name": (
                self.configuration.database.database
                if self.configuration.database
                else None
            ),
            "collection_prefix": self.configuration.collection_prefix,
            "available_repositories": [
                "ISignalRepository",
                "IMarketDataRepository",
                "IStrategyRepository",
            ],
            "custom_implementations": len(self._repositories),
            "singleton_instances": len(self._singletons),
        }

    def clear_singletons(self) -> None:
        """Clear all singleton repository instances."""
        self._singletons.clear()
        logger.info("Cleared singleton repository instances")


class RepositoryFactoryBuilder:
    """
    Builder pattern for creating repository factory with fluent interface.
    """

    def __init__(self):
        """Initialize builder."""
        self._configuration = RepositoryConfiguration()

    def with_mongodb(
        self, host: str = "localhost", port: int = 27017, database: str = "trading_db"
    ) -> "RepositoryFactoryBuilder":
        """
        Configure for MongoDB.

        Args:
            host: MongoDB host
            port: MongoDB port
            database: Database name

        Returns:
            Builder instance
        """
        from .repository_configuration import DatabaseConfiguration

        self._configuration.repository_type = RepositoryType.MONGODB
        if self._configuration.database is None:
            self._configuration.database = DatabaseConfiguration()

        self._configuration.database.host = host
        self._configuration.database.port = port
        self._configuration.database.database = database
        return self

    def with_memory(self) -> "RepositoryFactoryBuilder":
        """
        Configure for in-memory repositories.

        Returns:
            Builder instance
        """
        self._configuration.repository_type = RepositoryType.MEMORY
        return self

    def with_collection_prefix(self, prefix: str) -> "RepositoryFactoryBuilder":
        """
        Set collection prefix.

        Args:
            prefix: Collection prefix

        Returns:
            Builder instance
        """
        self._configuration.collection_prefix = prefix
        return self

    def with_caching(
        self, enabled: bool = True, ttl_seconds: int = 300
    ) -> "RepositoryFactoryBuilder":
        """
        Configure caching.

        Args:
            enabled: Enable caching
            ttl_seconds: Cache TTL in seconds

        Returns:
            Builder instance
        """
        self._configuration.enable_caching = enabled
        self._configuration.cache_ttl_seconds = ttl_seconds
        return self

    def build(self) -> RepositoryFactory:
        """
        Build repository factory.

        Returns:
            Repository factory instance
        """
        return RepositoryFactory(self._configuration)
