"""
Environment Management
Handles environment detection and environment-specific configuration.
"""

from enum import Enum
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentManager:
    """
    Manages environment detection and environment-specific settings.
    """

    def __init__(self):
        """Initialize environment manager."""
        self._current_environment: Optional[Environment] = None
        self._environment_variables: Dict[str, str] = dict(os.environ)

    def get_current_environment(self) -> Environment:
        """
        Get current application environment.

        Returns:
            Current environment
        """
        if self._current_environment is not None:
            return self._current_environment

        # Check environment variable
        env_name = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()

        try:
            self._current_environment = Environment(env_name)
        except ValueError:
            logger.warning(
                f"Unknown environment '{env_name}', defaulting to development"
            )
            self._current_environment = Environment.DEVELOPMENT

        return self._current_environment

    def set_environment(self, environment: Environment) -> None:
        """
        Set current environment (mainly for testing).

        Args:
            environment: Environment to set
        """
        self._current_environment = environment
        logger.info(f"Environment set to: {environment.value}")

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.get_current_environment() == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.get_current_environment() == Environment.TESTING

    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.get_current_environment() == Environment.STAGING

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.get_current_environment() == Environment.PRODUCTION

    def get_environment_variable(
        self, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get environment variable with optional default.

        Args:
            key: Environment variable key
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return self._environment_variables.get(key, default)

    def require_environment_variable(self, key: str) -> str:
        """
        Get required environment variable (raises if not found).

        Args:
            key: Environment variable key

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable not found
        """
        value = self.get_environment_variable(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' not found")
        return value

    def get_environment_variables(self, prefix: str = "") -> Dict[str, str]:
        """
        Get all environment variables with optional prefix filter.

        Args:
            prefix: Optional prefix to filter by

        Returns:
            Dictionary of environment variables
        """
        if not prefix:
            return self._environment_variables.copy()

        return {
            key: value
            for key, value in self._environment_variables.items()
            if key.startswith(prefix)
        }

    def get_config_filename(self, base_name: str = "config") -> str:
        """
        Get environment-specific config filename.

        Args:
            base_name: Base configuration filename

        Returns:
            Environment-specific config filename
        """
        env = self.get_current_environment()
        return f"{base_name}.{env.value}.yaml"

    def get_log_level(self) -> str:
        """
        Get appropriate log level for current environment.

        Returns:
            Log level string
        """
        env = self.get_current_environment()

        # Default log levels by environment
        default_levels = {
            Environment.DEVELOPMENT: "DEBUG",
            Environment.TESTING: "WARNING",
            Environment.STAGING: "INFO",
            Environment.PRODUCTION: "WARNING",
        }

        # Check for explicit log level override
        log_level = self.get_environment_variable("LOG_LEVEL")
        if log_level:
            return log_level.upper()

        return default_levels[env]

    def get_database_url(self) -> Optional[str]:
        """
        Get database URL from environment.

        Returns:
            Database URL if configured
        """
        # Try common database URL environment variables
        url_vars = ["DATABASE_URL", "DB_URL", "MONGODB_URL", "MONGO_URL"]

        for var in url_vars:
            url = self.get_environment_variable(var)
            if url:
                return url

        return None

    def get_debug_mode(self) -> bool:
        """
        Get debug mode setting for current environment.

        Returns:
            True if debug mode should be enabled
        """
        # Check explicit debug setting
        debug_env = self.get_environment_variable("DEBUG")
        if debug_env:
            return debug_env.lower() in ("true", "1", "yes", "on")

        # Default based on environment
        return self.is_development()

    def validate_environment(self) -> Dict[str, bool]:
        """
        Validate environment setup and required variables.

        Returns:
            Dictionary with validation results
        """
        results = {}

        # Check current environment is valid
        try:
            env = self.get_current_environment()
            results["valid_environment"] = True
            logger.info(f"Running in {env.value} environment")
        except Exception as e:
            results["valid_environment"] = False
            logger.error(f"Invalid environment configuration: {e}")

        # Check for required production variables
        if self.is_production():
            required_vars = [
                "DATABASE_URL",
                "SECRET_KEY",
                "OANDA_API_KEY",
                "OANDA_ACCOUNT_ID",
            ]

            for var in required_vars:
                has_var = self.get_environment_variable(var) is not None
                results[f"has_{var.lower()}"] = has_var
                if not has_var:
                    logger.warning(f"Missing required production variable: {var}")

        return results

    def export_environment_info(self) -> Dict[str, Any]:
        """
        Export environment information for debugging.

        Returns:
            Dictionary with environment information
        """
        env = self.get_current_environment()

        return {
            "environment": env.value,
            "is_development": self.is_development(),
            "is_testing": self.is_testing(),
            "is_staging": self.is_staging(),
            "is_production": self.is_production(),
            "debug_mode": self.get_debug_mode(),
            "log_level": self.get_log_level(),
            "config_filename": self.get_config_filename(),
            "has_database_url": self.get_database_url() is not None,
            "environment_variable_count": len(self._environment_variables),
        }
