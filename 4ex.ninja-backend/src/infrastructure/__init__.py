"""
Infrastructure Module

Provides infrastructure components including logging, database access,
external services, and configuration management.

Key components:
- logging: Centralized logging configuration and middleware
- database: Database connection and repository implementations
- external_services: API clients and external service integrations
- config: Configuration management and environment settings

Usage:
    from src.infrastructure import get_logger, setup_logging

    # Setup logging for the application
    setup_logging()

    # Get a logger instance
    logger = get_logger("my.module")
    logger.info("Hello, world!")
"""

# Import logging infrastructure
from .logging import (
    get_logger,
    setup_logging,
    LoggingManager,
    LogLevel,
    Environment,
    DevelopmentFormatter,
    ProductionFormatter,
    ErrorFormatter,
    PerformanceFormatter,
    AuditFormatter,
    BaseLoggerMixin,
    get_correlation_id,
    get_user_id,
    set_correlation_id,
    set_user_id,
    generate_correlation_id,
    log_with_context,
    FASTAPI_AVAILABLE,
)

# Import FastAPI-specific components if available
try:
    from .logging import LoggingMiddleware, StructuredLoggingRoute, setup_middleware

    _fastapi_available = True
except ImportError:
    _fastapi_available = False

__all__ = [
    # Core logging
    "get_logger",
    "setup_logging",
    "LoggingManager",
    "LogLevel",
    "Environment",
    # Formatters
    "DevelopmentFormatter",
    "ProductionFormatter",
    "ErrorFormatter",
    "PerformanceFormatter",
    "AuditFormatter",
    # Base utilities
    "BaseLoggerMixin",
    "get_correlation_id",
    "get_user_id",
    "set_correlation_id",
    "set_user_id",
    "generate_correlation_id",
    "log_with_context",
    "FASTAPI_AVAILABLE",
]

# Add FastAPI components to exports if available
if _fastapi_available:
    __all__.extend(
        [
            "LoggingMiddleware",
            "StructuredLoggingRoute",
            "setup_middleware",
        ]
    )
