"""
Simple validation test for the Database Layer implementation.

This script validates that the DatabaseManager can be instantiated and
basic operations work without requiring an actual MongoDB connection.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.infrastructure.database import (
    DatabaseManager,
    DatabaseConfigurationManager,
    DatabaseHealthMonitor,
    initialize_database_system,
)
from src.infrastructure.config.settings import DatabaseConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_manager():
    """Test DatabaseManager basic functionality."""

    logger.info("Testing DatabaseManager...")

    # Test configuration loading
    config = DatabaseConfig(host="localhost", port=27017, name="test_db")

    # Test DatabaseManager instantiation
    db_manager = DatabaseManager(config)

    # Test configuration properties
    assert db_manager._config.host == "localhost"
    assert db_manager._config.port == 27017
    assert db_manager._config.name == "test_db"

    # Test connection string generation
    connection_string = db_manager._get_connection_string()
    assert "mongodb://localhost:27017/test_db" in connection_string

    # Test connection info
    info = db_manager.get_connection_info()
    assert info["database_name"] == "test_db"
    assert info["is_connected"] == False

    logger.info("✓ DatabaseManager tests passed")


def test_configuration_manager():
    """Test DatabaseConfigurationManager."""

    logger.info("Testing DatabaseConfigurationManager...")

    # Test configuration manager
    config_manager = DatabaseConfigurationManager()

    # Test environment detection
    assert config_manager.current_env is not None

    # Test getting current config
    current_config = config_manager.get_current_config()
    assert current_config.database_config is not None
    assert current_config.environment is not None

    # Test configuration validation
    is_valid = config_manager.validate_configuration()
    assert isinstance(is_valid, bool)

    # Test configuration summary
    summary = config_manager.get_configuration_summary()
    assert "environment" in summary
    assert "database_name" in summary

    logger.info("✓ DatabaseConfigurationManager tests passed")


def test_health_monitor():
    """Test DatabaseHealthMonitor basic functionality."""

    logger.info("Testing DatabaseHealthMonitor...")

    # Create a mock database manager
    config = DatabaseConfig(name="test_db")
    db_manager = DatabaseManager(config)

    # Test health monitor instantiation
    health_monitor = DatabaseHealthMonitor(db_manager)

    # Test metrics storage
    assert health_monitor.metrics_history == []
    assert health_monitor.max_history_size == 100

    # Test getting recent metrics (should be empty)
    recent = health_monitor.get_recent_metrics()
    assert recent == []

    # Test average response time (should be 0 with no data)
    avg_time = health_monitor.get_average_response_time()
    assert avg_time == 0.0

    logger.info("✓ DatabaseHealthMonitor tests passed")


async def run_all_tests():
    """Run all validation tests."""

    logger.info("Starting Database Layer validation tests...")

    try:
        # Test basic functionality without database connection
        await test_database_manager()
        test_configuration_manager()
        test_health_monitor()

        logger.info("🎉 All Database Layer tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Tests failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
