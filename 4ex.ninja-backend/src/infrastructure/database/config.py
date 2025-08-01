"""
Environment-based Database Configuration

This module provides environment-specific database configuration management
with support for development, testing, and production environments.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from ..config.settings import DatabaseConfig

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration settings."""

    # Database settings
    database_config: DatabaseConfig

    # Environment metadata
    environment: Environment
    debug_mode: bool = False
    log_level: str = "INFO"

    # Performance settings
    connection_pool_multiplier: float = 1.0
    query_timeout_multiplier: float = 1.0

    # Security settings
    ssl_required: bool = False
    connection_encryption: bool = False

    # Monitoring settings
    health_check_interval: float = 30.0
    metrics_enabled: bool = True


class DatabaseConfigurationManager:
    """
    Manages database configuration across different environments.

    Automatically detects environment and applies appropriate settings
    for development, testing, staging, and production.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self.current_env = self._detect_environment()
        self._env_configs: Dict[Environment, EnvironmentConfig] = {}
        self._load_environment_configs()

    def _detect_environment(self) -> Environment:
        """
        Detect current environment from environment variables.

        Returns:
            Environment: Detected environment type
        """
        env_name = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()

        env_mapping = {
            "dev": Environment.DEVELOPMENT,
            "development": Environment.DEVELOPMENT,
            "test": Environment.TESTING,
            "testing": Environment.TESTING,
            "stage": Environment.STAGING,
            "staging": Environment.STAGING,
            "prod": Environment.PRODUCTION,
            "production": Environment.PRODUCTION,
        }

        detected_env = env_mapping.get(env_name, Environment.DEVELOPMENT)
        logger.info(f"Detected environment: {detected_env.value}")
        return detected_env

    def _load_environment_configs(self) -> None:
        """Load configuration for all environments."""

        # Development Configuration
        dev_config = self._create_development_config()
        self._env_configs[Environment.DEVELOPMENT] = dev_config

        # Testing Configuration
        test_config = self._create_testing_config()
        self._env_configs[Environment.TESTING] = test_config

        # Staging Configuration
        staging_config = self._create_staging_config()
        self._env_configs[Environment.STAGING] = staging_config

        # Production Configuration
        prod_config = self._create_production_config()
        self._env_configs[Environment.PRODUCTION] = prod_config

    def _create_development_config(self) -> EnvironmentConfig:
        """Create development environment configuration."""

        # Use local MongoDB by default for development
        db_config = DatabaseConfig(
            host=os.getenv("DEV_DATABASE_HOST", "localhost"),
            port=int(os.getenv("DEV_DATABASE_PORT", "27017")),
            name=os.getenv("DEV_DATABASE_NAME", "trading_db_dev"),
            username=os.getenv("DEV_DATABASE_USERNAME"),
            password=os.getenv("DEV_DATABASE_PASSWORD"),
            # Development-optimized settings
            max_pool_size=20,  # Lower pool size for development
            min_pool_size=2,
            connect_timeout_ms=5000,
            server_selection_timeout_ms=10000,
        )

        # Override with connection string if provided
        dev_connection_string = os.getenv("DEV_MONGO_CONNECTION_STRING") or os.getenv(
            "MONGO_CONNECTION_STRING"
        )
        if dev_connection_string:
            setattr(db_config, "_connection_string", dev_connection_string)

        return EnvironmentConfig(
            database_config=db_config,
            environment=Environment.DEVELOPMENT,
            debug_mode=True,
            log_level="DEBUG",
            connection_pool_multiplier=0.5,
            query_timeout_multiplier=2.0,
            health_check_interval=60.0,  # Less frequent health checks in dev
            metrics_enabled=True,
        )

    def _create_testing_config(self) -> EnvironmentConfig:
        """Create testing environment configuration."""

        db_config = DatabaseConfig(
            host=os.getenv("TEST_DATABASE_HOST", "localhost"),
            port=int(os.getenv("TEST_DATABASE_PORT", "27017")),
            name=os.getenv("TEST_DATABASE_NAME", "trading_db_test"),
            username=os.getenv("TEST_DATABASE_USERNAME"),
            password=os.getenv("TEST_DATABASE_PASSWORD"),
            # Testing-optimized settings
            max_pool_size=10,  # Minimal pool for testing
            min_pool_size=1,
            connect_timeout_ms=3000,
            server_selection_timeout_ms=5000,
        )

        # Override with test connection string if provided
        test_connection_string = os.getenv("TEST_MONGO_CONNECTION_STRING")
        if test_connection_string:
            setattr(db_config, "_connection_string", test_connection_string)

        return EnvironmentConfig(
            database_config=db_config,
            environment=Environment.TESTING,
            debug_mode=True,
            log_level="WARNING",
            connection_pool_multiplier=0.2,
            query_timeout_multiplier=0.5,  # Faster timeouts for tests
            health_check_interval=120.0,
            metrics_enabled=False,  # Disable metrics in tests
        )

    def _create_staging_config(self) -> EnvironmentConfig:
        """Create staging environment configuration."""

        db_config = DatabaseConfig(
            host=os.getenv("STAGING_DATABASE_HOST", "localhost"),
            port=int(os.getenv("STAGING_DATABASE_PORT", "27017")),
            name=os.getenv("STAGING_DATABASE_NAME", "trading_db_staging"),
            username=os.getenv("STAGING_DATABASE_USERNAME"),
            password=os.getenv("STAGING_DATABASE_PASSWORD"),
            # Staging settings - similar to production but with lower limits
            max_pool_size=50,
            min_pool_size=5,
            connect_timeout_ms=8000,
            server_selection_timeout_ms=15000,
            retry_writes=True,
            retry_reads=True,
        )

        # Override with staging connection string if provided
        staging_connection_string = os.getenv("STAGING_MONGO_CONNECTION_STRING")
        if staging_connection_string:
            setattr(db_config, "_connection_string", staging_connection_string)

        return EnvironmentConfig(
            database_config=db_config,
            environment=Environment.STAGING,
            debug_mode=False,
            log_level="INFO",
            connection_pool_multiplier=0.8,
            query_timeout_multiplier=1.0,
            ssl_required=True,
            connection_encryption=True,
            health_check_interval=30.0,
            metrics_enabled=True,
        )

    def _create_production_config(self) -> EnvironmentConfig:
        """Create production environment configuration."""

        db_config = DatabaseConfig(
            host=os.getenv("PROD_DATABASE_HOST", "localhost"),
            port=int(os.getenv("PROD_DATABASE_PORT", "27017")),
            name=os.getenv("PROD_DATABASE_NAME", "trading_db"),
            username=os.getenv("PROD_DATABASE_USERNAME"),
            password=os.getenv("PROD_DATABASE_PASSWORD"),
            # Production-optimized settings
            max_pool_size=100,
            min_pool_size=10,
            max_idle_time_ms=30000,
            connect_timeout_ms=10000,
            server_selection_timeout_ms=30000,
            socket_timeout_ms=5000,
            retry_writes=True,
            retry_reads=True,
            tls_enabled=True,
        )

        # Production connection string (required for production)
        prod_connection_string = os.getenv("PROD_MONGO_CONNECTION_STRING") or os.getenv(
            "MONGO_CONNECTION_STRING"
        )
        if prod_connection_string:
            setattr(db_config, "_connection_string", prod_connection_string)
        elif self.current_env == Environment.PRODUCTION:
            logger.warning(
                "No production MongoDB connection string found. Set PROD_MONGO_CONNECTION_STRING."
            )

        return EnvironmentConfig(
            database_config=db_config,
            environment=Environment.PRODUCTION,
            debug_mode=False,
            log_level="INFO",
            connection_pool_multiplier=1.0,
            query_timeout_multiplier=1.0,
            ssl_required=True,
            connection_encryption=True,
            health_check_interval=15.0,  # More frequent health checks in production
            metrics_enabled=True,
        )

    def get_current_config(self) -> EnvironmentConfig:
        """
        Get configuration for current environment.

        Returns:
            EnvironmentConfig: Current environment configuration
        """
        return self._env_configs[self.current_env]

    def get_config_for_environment(self, environment: Environment) -> EnvironmentConfig:
        """
        Get configuration for specific environment.

        Args:
            environment: Target environment

        Returns:
            EnvironmentConfig: Environment configuration
        """
        return self._env_configs[environment]

    def get_database_config(self) -> DatabaseConfig:
        """
        Get database configuration for current environment.

        Returns:
            DatabaseConfig: Database configuration
        """
        return self.get_current_config().database_config

    def validate_configuration(self) -> bool:
        """
        Validate current configuration.

        Returns:
            bool: True if configuration is valid
        """
        try:
            config = self.get_current_config()
            db_config = config.database_config

            # Validate required settings for production
            if config.environment == Environment.PRODUCTION:
                if (
                    not hasattr(db_config, "_connection_string")
                    and not db_config.username
                ):
                    logger.error(
                        "Production environment requires connection string or credentials"
                    )
                    return False

                if not config.ssl_required:
                    logger.warning("SSL should be required in production")

            # Validate database name
            if not db_config.name:
                logger.error("Database name is required")
                return False

            # Validate pool settings
            if db_config.max_pool_size < db_config.min_pool_size:
                logger.error("Max pool size must be >= min pool size")
                return False

            logger.info(
                f"Configuration validation passed for {config.environment.value}"
            )
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False

    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get summary of current configuration for logging/debugging.

        Returns:
            Dict with configuration summary (no sensitive data)
        """
        config = self.get_current_config()
        db_config = config.database_config

        return {
            "environment": config.environment.value,
            "database_name": db_config.name,
            "database_host": db_config.host,
            "database_port": db_config.port,
            "max_pool_size": db_config.max_pool_size,
            "min_pool_size": db_config.min_pool_size,
            "debug_mode": config.debug_mode,
            "log_level": config.log_level,
            "ssl_required": config.ssl_required,
            "metrics_enabled": config.metrics_enabled,
            "has_connection_string": hasattr(db_config, "_connection_string"),
        }


# Global configuration manager instance
config_manager = DatabaseConfigurationManager()
