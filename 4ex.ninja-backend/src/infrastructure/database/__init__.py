"""
Database Infrastructure Package

This package provides comprehensive database management functionality including:
- Connection management with pooling and health monitoring
- Environment-based configuration
- Database initialization and migration utilities
- Health monitoring and metrics collection
"""

from .connection import DatabaseManager, DatabaseConnectionError, db_manager
from .config import (
    DatabaseConfigurationManager,
    EnvironmentConfig,
    Environment,
    config_manager,
)
from .health import (
    DatabaseHealthMonitor,
    DatabaseMonitoringService,
    HealthStatus,
    HealthMetrics,
)
from .migrations import (
    DatabaseInitializer,
    DatabaseMigrationManager,
    initialize_database_system,
)

__all__ = [
    # Connection management
    "DatabaseManager",
    "DatabaseConnectionError",
    "db_manager",
    # Configuration management
    "DatabaseConfigurationManager",
    "EnvironmentConfig",
    "Environment",
    "config_manager",
    # Health monitoring
    "DatabaseHealthMonitor",
    "DatabaseMonitoringService",
    "HealthStatus",
    "HealthMetrics",
    # Initialization and migrations
    "DatabaseInitializer",
    "DatabaseMigrationManager",
    "initialize_database_system",
]
