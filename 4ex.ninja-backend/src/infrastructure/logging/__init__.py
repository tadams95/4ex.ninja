"""
Logging Infrastructure Module

Provides centralized logging configuration, formatters, and middleware
for comprehensive application monitoring and debugging.

Components:
- config: Centralized logging configuration management
- formatters: Custom log formatters for different environments
- middleware: Request/response logging and performance monitoring

Usage:
    from src.infrastructure.logging import get_logger, setup_logging
    
    # Setup logging for the application
    setup_logging()
    
    # Get a logger instance
    logger = get_logger("my.module")
    logger.info("Hello, world!")
"""

from .config import (
    get_logger,
    setup_logging,
    LoggingManager,
    LogLevel,
    Environment
)

from .formatters import (
    DevelopmentFormatter,
    ProductionFormatter,
    ErrorFormatter,
    PerformanceFormatter,
    AuditFormatter
)

from .middleware import (
    BaseLoggerMixin,
    get_correlation_id,
    get_user_id,
    set_correlation_id,
    set_user_id,
    generate_correlation_id,
    log_with_context,
    FASTAPI_AVAILABLE
)

# Only export FastAPI-specific components if available
if FASTAPI_AVAILABLE:
    from .middleware import (
        LoggingMiddleware,
        StructuredLoggingRoute,
        setup_middleware
    )
    
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
        
        # Middleware and utilities
        "BaseLoggerMixin",
        "LoggingMiddleware",
        "StructuredLoggingRoute",
        "setup_middleware",
        "get_correlation_id",
        "get_user_id",
        "set_correlation_id",
        "set_user_id",
        "generate_correlation_id",
        "log_with_context",
        "FASTAPI_AVAILABLE"
    ]
else:
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
        
        # Middleware and utilities (non-FastAPI)
        "BaseLoggerMixin",
        "get_correlation_id",
        "get_user_id",
        "set_correlation_id",
        "set_user_id", 
        "generate_correlation_id",
        "log_with_context",
        "FASTAPI_AVAILABLE"
    ]
