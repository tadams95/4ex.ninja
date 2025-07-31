"""
Configuration Loader
Handles loading configuration from various sources (files, environment, etc.).
"""

from typing import Dict, Any, Optional
import os
import json
import logging
from pathlib import Path

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

from .settings import Settings, AppConfig, DatabaseConfig, TradingConfig, OandaConfig
from .environment import EnvironmentManager, Environment

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Configuration loading error."""

    pass


class ConfigLoader:
    """
    Configuration loader supporting multiple sources and formats.
    """

    def __init__(self, environment_manager: Optional[EnvironmentManager] = None):
        """
        Initialize configuration loader.

        Args:
            environment_manager: Environment manager instance
        """
        self.environment_manager = environment_manager or EnvironmentManager()
        self._config_cache: Optional[Settings] = None

    def load_settings(self, config_path: Optional[str] = None) -> Settings:
        """
        Load settings from various sources with precedence order.

        Precedence (highest to lowest):
        1. Environment variables
        2. Configuration file
        3. Default values

        Args:
            config_path: Optional path to configuration file

        Returns:
            Loaded settings
        """
        if self._config_cache is not None:
            return self._config_cache

        try:
            # Start with default settings
            settings = Settings.create_default()

            # Load from configuration file if provided
            if config_path:
                file_config = self._load_from_file(config_path)
                settings = self._merge_settings(settings, file_config)
            else:
                # Try to find environment-specific config file
                env_config_path = self._find_environment_config()
                if env_config_path:
                    file_config = self._load_from_file(env_config_path)
                    settings = self._merge_settings(settings, file_config)

            # Override with environment variables (highest precedence)
            env_settings = Settings.from_environment()
            settings = self._merge_settings(settings, env_settings)

            # Validate the final configuration
            self._validate_settings(settings)

            self._config_cache = settings
            logger.info("Configuration loaded successfully")
            return settings

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")

    def reload_settings(self, config_path: Optional[str] = None) -> Settings:
        """
        Reload settings (clears cache).

        Args:
            config_path: Optional path to configuration file

        Returns:
            Reloaded settings
        """
        self._config_cache = None
        return self.load_settings(config_path)

    def _find_environment_config(self) -> Optional[str]:
        """
        Find environment-specific configuration file.

        Returns:
            Path to configuration file if found
        """
        current_env = self.environment_manager.get_current_environment()

        # Try different config file locations
        config_paths = [
            f"config.{current_env.value}.json",
            f"config/{current_env.value}.json",
            f"config/config.{current_env.value}.json",
            "config.json",
            "config/config.json",
        ]

        for config_path in config_paths:
            if os.path.exists(config_path):
                logger.info(f"Found configuration file: {config_path}")
                return config_path

        logger.debug("No configuration file found")
        return None

    def _load_from_file(self, config_path: str) -> Settings:
        """
        Load settings from configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Settings loaded from file
        """
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.endswith(".json"):
                    config_data = json.load(f)
                elif config_path.endswith((".yaml", ".yml")):
                    config_data = self._load_yaml(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {config_path}"
                    )

            return self._create_settings_from_dict(config_data)

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file: {e}")

    def _load_yaml(self, file_handle) -> Dict[str, Any]:
        """
        Load YAML configuration (optional dependency).

        Args:
            file_handle: File handle to read from

        Returns:
            Configuration dictionary
        """
        if not YAML_AVAILABLE:
            raise ConfigurationError(
                "PyYAML not installed - cannot load YAML configuration"
            )
        
        try:
            return yaml.safe_load(file_handle)  # type: ignore
        except Exception as e:
            raise ConfigurationError(f"Failed to parse YAML configuration: {e}")

    def _create_settings_from_dict(self, config_data: Dict[str, Any]) -> Settings:
        """
        Create settings object from configuration dictionary.

        Args:
            config_data: Configuration dictionary

        Returns:
            Settings object
        """
        try:
            # Extract configuration sections
            app_data = config_data.get("app", {})
            database_data = config_data.get("database", {})
            trading_data = config_data.get("trading", {})
            oanda_data = config_data.get("oanda", {})

            # Create configuration objects
            app_config = AppConfig(**app_data)
            database_config = DatabaseConfig(**database_data)
            trading_config = TradingConfig(**trading_data)
            oanda_config = OandaConfig(**oanda_data)

            return Settings(
                app=app_config,
                database=database_config,
                trading=trading_config,
                oanda=oanda_config,
            )

        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration structure: {e}")
        except ValueError as e:
            raise ConfigurationError(f"Invalid configuration values: {e}")

    def _merge_settings(self, base: Settings, override: Settings) -> Settings:
        """
        Merge two settings objects (override takes precedence).

        Args:
            base: Base settings
            override: Override settings

        Returns:
            Merged settings
        """
        # Convert to dictionaries for easier merging
        base_dict = base.to_dict()
        override_dict = override.to_dict()

        # Merge dictionaries
        merged_dict = self._deep_merge_dicts(base_dict, override_dict)

        # Create new settings object
        return self._create_settings_from_dict(merged_dict)

    def _deep_merge_dicts(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def _validate_settings(self, settings: Settings) -> None:
        """
        Validate settings for current environment.

        Args:
            settings: Settings to validate
        """
        errors = []

        # Environment-specific validation
        current_env = self.environment_manager.get_current_environment()

        if current_env == Environment.PRODUCTION:
            errors.extend(settings.validate_production_settings())

        # General validation
        if not settings.app.secret_key:
            errors.append("Secret key is required")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"- {error}" for error in errors
            )
            raise ConfigurationError(error_msg)

    def export_config_template(self, output_path: str, format: str = "json") -> None:
        """
        Export configuration template file.

        Args:
            output_path: Output file path
            format: Output format ('json' or 'yaml')
        """
        try:
            # Create default settings
            settings = Settings.create_default()
            config_dict = settings.to_dict()

            # Add comments/descriptions
            config_dict["_description"] = "4ex.ninja Trading Application Configuration"
            config_dict["_environment"] = (
                "Set APP_ENV environment variable to: development, testing, staging, or production"
            )

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                if format.lower() == "json":
                    json.dump(config_dict, f, indent=2, default=str)
                elif format.lower() in ("yaml", "yml"):
                    if not YAML_AVAILABLE:
                        raise ConfigurationError(
                            "PyYAML not installed - cannot export YAML"
                        )
                    yaml.safe_dump(  # type: ignore
                        config_dict, f, indent=2, default_flow_style=False
                    )
                else:
                    raise ConfigurationError(f"Unsupported export format: {format}")

            logger.info(f"Configuration template exported to: {output_path}")

        except Exception as e:
            raise ConfigurationError(f"Failed to export configuration template: {e}")

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for debugging.

        Returns:
            Configuration summary
        """
        settings = self.load_settings()

        return {
            "environment": self.environment_manager.get_current_environment().value,
            "app_name": settings.app.app_name,
            "app_version": settings.app.version,
            "debug_mode": settings.app.debug,
            "api_port": settings.app.api_port,
            "database_host": settings.database.host,
            "database_name": settings.database.name,
            "has_oanda_credentials": bool(
                settings.oanda.api_key and settings.oanda.account_id
            ),
            "enabled_trading_pairs": len(settings.trading.enabled_pairs),
            "log_level": settings.app.log_level,
        }
