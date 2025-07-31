"""
Centralized logging configuration for 4ex.ninja backend.
Provides structured logging with environment-specific settings,
file rotation, and performance monitoring capabilities.
"""

import logging
import logging.handlers
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

from .formatters import DevelopmentFormatter, ProductionFormatter, ErrorFormatter


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class LoggingConfig:
    """Configuration for logging system."""

    # Environment settings
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO

    # File logging settings
    enable_file_logging: bool = True
    log_dir: str = "logs"
    log_file: str = "app.log"
    error_log_file: str = "error.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # Console logging settings
    enable_console_logging: bool = True
    console_log_level: Optional[LogLevel] = None

    # Structured logging settings
    enable_json_logging: bool = False
    include_extra_fields: bool = True

    # Performance settings
    enable_performance_logging: bool = True
    slow_query_threshold: float = 1.0  # seconds

    # Application-specific settings
    correlation_id_header: str = "X-Correlation-ID"
    user_id_header: str = "X-User-ID"


class LoggingManager:
    """Centralized logging manager for application-wide configuration."""

    _instance: Optional["LoggingManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "LoggingManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config: Optional[LoggingConfig] = None
            self.loggers: Dict[str, logging.Logger] = {}
            self._initialized = True

    def configure(self, config: Optional[LoggingConfig] = None) -> None:
        """Configure the logging system with the provided configuration."""
        if config is None:
            config = self._create_default_config()

        self.config = config
        self._setup_logging()

    def _create_default_config(self) -> LoggingConfig:
        """Create default configuration based on environment variables."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return LoggingConfig(
            environment=(
                Environment(env)
                if env in Environment.__members__.values()
                else Environment.DEVELOPMENT
            ),
            log_level=LogLevel.DEBUG if debug else LogLevel.INFO,
            enable_json_logging=env == "production",
            console_log_level=LogLevel.DEBUG if debug else None,
            log_dir=os.getenv("LOG_DIR", "logs"),
            enable_performance_logging=os.getenv(
                "ENABLE_PERFORMANCE_LOGGING", "true"
            ).lower()
            == "true",
        )

    def _setup_logging(self) -> None:
        """Setup logging handlers and formatters."""
        if not self.config:
            raise ValueError("Logging configuration not set")

        # Create log directory if it doesn't exist
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.log_level.value)

        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Setup console handler
        if self.config.enable_console_logging:
            self._setup_console_handler(root_logger)

        # Setup file handlers
        if self.config.enable_file_logging:
            self._setup_file_handlers(root_logger)

        # Setup error handler
        self._setup_error_handler(root_logger)

        # Configure third-party loggers
        self._configure_third_party_loggers()

    def _setup_console_handler(self, logger: logging.Logger) -> None:
        """Setup console logging handler."""
        if not self.config:
            return

        console_handler = logging.StreamHandler(sys.stdout)

        console_level = (
            self.config.console_log_level.value
            if self.config.console_log_level
            else self.config.log_level.value
        )
        console_handler.setLevel(console_level)

        # Use appropriate formatter based on environment
        if self.config.environment == Environment.PRODUCTION:
            formatter = ProductionFormatter()
        else:
            formatter = DevelopmentFormatter()

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    def _setup_file_handlers(self, logger: logging.Logger) -> None:
        """Setup file logging handlers with rotation."""
        if not self.config:
            return

        log_path = Path(self.config.log_dir) / self.config.log_file

        # Main log file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(self.config.log_level.value)

        # Use production formatter for file logging
        if self.config.enable_json_logging:
            formatter = ProductionFormatter()
        else:
            formatter = DevelopmentFormatter()

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def _setup_error_handler(self, logger: logging.Logger) -> None:
        """Setup dedicated error file handler."""
        if not self.config or not self.config.enable_file_logging:
            return

        error_log_path = Path(self.config.log_dir) / self.config.error_log_file

        error_handler = logging.handlers.RotatingFileHandler(
            filename=str(error_log_path),
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(ErrorFormatter())

        logger.addHandler(error_handler)

    def _configure_third_party_loggers(self) -> None:
        """Configure logging levels for third-party libraries."""
        third_party_configs = {
            "uvicorn": logging.WARNING,
            "fastapi": logging.WARNING,
            "pymongo": logging.WARNING,
            "httpx": logging.WARNING,
            "urllib3": logging.WARNING,
        }

        for logger_name, level in third_party_configs.items():
            logging.getLogger(logger_name).setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name."""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]

    def update_log_level(self, level: LogLevel) -> None:
        """Update the log level for all loggers."""
        if self.config:
            self.config.log_level = level
            logging.getLogger().setLevel(level.value)

    def get_config(self) -> Optional[LoggingConfig]:
        """Get the current logging configuration."""
        return self.config


# Global logging manager instance
logging_manager = LoggingManager()


def configure_logging(config: Optional[LoggingConfig] = None) -> None:
    """Configure the global logging system."""
    logging_manager.configure(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging_manager.get_logger(name)


def get_config() -> Optional[LoggingConfig]:
    """Get the current logging configuration."""
    return logging_manager.get_config()


# Convenience function for application setup
def setup_logging(
    environment: str = "development",
    debug: bool = False,
    log_dir: str = "logs",
    enable_json: bool = False,
) -> None:
    """Quick setup function for common configurations."""

    config = LoggingConfig(
        environment=(
            Environment(environment)
            if environment in Environment.__members__.values()
            else Environment.DEVELOPMENT
        ),
        log_level=LogLevel.DEBUG if debug else LogLevel.INFO,
        enable_json_logging=enable_json,
        log_dir=log_dir,
        console_log_level=LogLevel.DEBUG if debug else LogLevel.INFO,
    )

    configure_logging(config)
