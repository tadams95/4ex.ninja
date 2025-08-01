"""
Database Layer Usage Example

This example demonstrates how to use the Database Layer components
in a real application scenario.
"""

import asyncio
import logging
from datetime import datetime

from src.infrastructure.database import (
    db_manager,
    config_manager,
    DatabaseMonitoringService,
    initialize_database_system,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_database_usage():
    """
    Example showing complete database layer usage.
    """

    logger.info("=== Database Layer Usage Example ===")

    # 1. Configuration Management
    logger.info("1. Configuration Management")
    logger.info(f"Current environment: {config_manager.current_env.value}")

    config_summary = config_manager.get_configuration_summary()
    logger.info(f"Database configuration: {config_summary}")

    # 2. Database Connection (would work with real MongoDB)
    logger.info("\n2. Database Connection")
    try:
        # Note: This will fail without MongoDB running, but shows the interface
        await db_manager.connect()
        logger.info("✓ Database connected successfully")

        # 3. Health Monitoring
        logger.info("\n3. Health Monitoring")
        monitoring_service = DatabaseMonitoringService(db_manager)
        await monitoring_service.start_monitoring()

        # Let monitoring run for a few cycles
        await asyncio.sleep(5)

        health_status = monitoring_service.get_health_status()
        logger.info(f"Health status: {health_status}")

        await monitoring_service.stop_monitoring()

        # 4. Database Operations Example
        logger.info("\n4. Database Operations")
        database = db_manager.database

        # Example: Insert a signal
        signals_collection = database["signals"]

        signal_data = {
            "pair": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.1200,
            "stop_loss": 1.1150,
            "take_profit": 1.1300,
            "created_at": datetime.utcnow(),
            "status": "ACTIVE",
        }

        result = await signals_collection.insert_one(signal_data)
        logger.info(f"✓ Signal inserted with ID: {result.inserted_id}")

        # Example: Query signals
        recent_signals = (
            await signals_collection.find({"pair": "EUR_USD"})
            .limit(5)
            .to_list(length=None)
        )

        logger.info(f"✓ Found {len(recent_signals)} EUR_USD signals")

        # 5. Graceful shutdown
        logger.info("\n5. Graceful Shutdown")
        await db_manager.disconnect()
        logger.info("✓ Database disconnected")

    except Exception as e:
        logger.error(f"Database operation failed (expected without MongoDB): {str(e)}")

        # Show that the configuration and health monitoring still work
        logger.info("Configuration and health monitoring work independently:")
        logger.info(f"Connection info: {db_manager.get_connection_info()}")


async def example_initialization():
    """
    Example showing database initialization process.
    """

    logger.info("\n=== Database Initialization Example ===")

    try:
        # This would normally set up the entire database schema
        success = await initialize_database_system(db_manager)

        if success:
            logger.info("✓ Database system initialization completed")
        else:
            logger.warning(
                "⚠ Database initialization failed (expected without MongoDB)"
            )

    except Exception as e:
        logger.info(
            f"Database initialization failed (expected without MongoDB): {str(e)}"
        )


if __name__ == "__main__":

    async def main():
        await example_database_usage()
        await example_initialization()

        logger.info("\n=== Example Complete ===")
        logger.info(
            "This example shows how the Database Layer would work with a real MongoDB connection."
        )
        logger.info("Key benefits:")
        logger.info("- Environment-based configuration")
        logger.info("- Connection pooling and health monitoring")
        logger.info("- Automatic retries and error handling")
        logger.info("- Database initialization and migrations")
        logger.info("- Comprehensive logging and monitoring")

    asyncio.run(main())
