"""
Repository Configuration Management
Handles repository type selection and configuration.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


class RepositoryType(Enum):
    """Available repository implementation types."""

    MONGODB = "mongodb"
    MEMORY = "memory"
    POSTGRESQL = "postgresql"  # For future implementation
    SQLITE = "sqlite"  # For future implementation


@dataclass
class DatabaseConfiguration:
    """Database connection configuration."""

    host: str = "localhost"
    port: int = 27017
    database: str = "trading_db"
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None

    # Connection pool settings
    max_pool_size: int = 100
    min_pool_size: int = 10
    max_idle_time_ms: int = 30000

    # Retry settings
    retry_writes: bool = True
    retry_reads: bool = True

    # Timeout settings
    connect_timeout_ms: int = 10000
    server_selection_timeout_ms: int = 30000
    socket_timeout_ms: int = 5000

    def get_connection_string(self) -> str:
        """
        Get MongoDB connection string.

        Returns:
            MongoDB connection string
        """
        if self.connection_string:
            return self.connection_string

        auth_part = ""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"

        return f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}"


@dataclass
class RepositoryConfiguration:
    """Repository configuration settings."""

    # Repository type selection
    repository_type: RepositoryType = RepositoryType.MONGODB

    # Database configuration
    database: Optional[DatabaseConfiguration] = None

    # Collection/table naming
    collection_prefix: str = ""

    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    bulk_operation_size: int = 1000

    # Indexing settings
    auto_create_indexes: bool = True

    # Monitoring settings
    enable_query_logging: bool = False
    slow_query_threshold_ms: int = 1000

    # Data validation
    strict_validation: bool = True
    validate_on_write: bool = True

    def __post_init__(self):
        """Initialize default database configuration if not provided."""
        if self.database is None:
            self.database = DatabaseConfiguration()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RepositoryConfiguration":
        """
        Create configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Repository configuration instance
        """
        # Extract database config
        db_config = config_dict.get("database", {})
        database = DatabaseConfiguration(**db_config)

        # Extract repository type
        repo_type_str = config_dict.get("repository_type", "mongodb")
        repository_type = RepositoryType(repo_type_str)

        # Create configuration
        config = cls(
            repository_type=repository_type,
            database=database,
            collection_prefix=config_dict.get("collection_prefix", ""),
            enable_caching=config_dict.get("enable_caching", True),
            cache_ttl_seconds=config_dict.get("cache_ttl_seconds", 300),
            bulk_operation_size=config_dict.get("bulk_operation_size", 1000),
            auto_create_indexes=config_dict.get("auto_create_indexes", True),
            enable_query_logging=config_dict.get("enable_query_logging", False),
            slow_query_threshold_ms=config_dict.get("slow_query_threshold_ms", 1000),
            strict_validation=config_dict.get("strict_validation", True),
            validate_on_write=config_dict.get("validate_on_write", True),
        )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        result = {
            "repository_type": self.repository_type.value,
            "collection_prefix": self.collection_prefix,
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "bulk_operation_size": self.bulk_operation_size,
            "auto_create_indexes": self.auto_create_indexes,
            "enable_query_logging": self.enable_query_logging,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "strict_validation": self.strict_validation,
            "validate_on_write": self.validate_on_write,
        }

        if self.database:
            result["database"] = {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                "password": self.database.password,
                "connection_string": self.database.connection_string,
                "max_pool_size": self.database.max_pool_size,
                "min_pool_size": self.database.min_pool_size,
                "max_idle_time_ms": self.database.max_idle_time_ms,
                "retry_writes": self.database.retry_writes,
                "retry_reads": self.database.retry_reads,
                "connect_timeout_ms": self.database.connect_timeout_ms,
                "server_selection_timeout_ms": self.database.server_selection_timeout_ms,
                "socket_timeout_ms": self.database.socket_timeout_ms,
            }

        return result

    def get_collection_name(self, entity_name: str) -> str:
        """
        Get collection name for entity.

        Args:
            entity_name: Entity name

        Returns:
            Collection name with prefix
        """
        if self.collection_prefix:
            return f"{self.collection_prefix}_{entity_name.lower()}"
        return entity_name.lower()

    def validate(self) -> List[str]:
        """
        Validate configuration.

        Returns:
            List of validation errors
        """
        errors = []

        # Validate database configuration
        if self.database:
            if not self.database.host:
                errors.append("Database host is required")

            if self.database.port <= 0 or self.database.port > 65535:
                errors.append("Database port must be between 1 and 65535")

            if not self.database.database:
                errors.append("Database name is required")

        # Validate performance settings
        if self.cache_ttl_seconds < 0:
            errors.append("Cache TTL must be non-negative")

        if self.bulk_operation_size <= 0:
            errors.append("Bulk operation size must be positive")

        if self.slow_query_threshold_ms < 0:
            errors.append("Slow query threshold must be non-negative")

        return errors
