"""
Database Initialization and Migration Utilities

This module provides utilities for database initialization, schema setup,
and data migration operations for the trading system.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Represents a database migration."""

    version: str
    name: str
    description: str
    up_script: Callable
    down_script: Optional[Callable] = None
    dependencies: Optional[List[str]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class MigrationRecord:
    """Migration execution record."""

    version: str
    name: str
    status: MigrationStatus
    executed_at: datetime
    execution_time_ms: float
    error_message: Optional[str] = None


class DatabaseInitializer:
    """
    Handles database initialization and setup operations.

    Creates collections, indexes, and initial data required for the
    trading system to function properly.
    """

    def __init__(self, db_manager):
        """
        Initialize database setup manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    async def initialize_database(self) -> bool:
        """
        Initialize database with required collections and indexes.

        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Starting database initialization...")

            # Ensure database connection
            if not self.db_manager.is_connected:
                await self.db_manager.connect()

            database = self.db_manager.database

            # Create collections with validation
            await self._create_collections(database)

            # Create indexes for performance
            await self._create_indexes(database)

            # Insert initial data if needed
            await self._insert_initial_data(database)

            # Verify setup
            await self._verify_setup(database)

            logger.info("Database initialization completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False

    async def _create_collections(self, database) -> None:
        """Create required collections with validation rules."""

        collections_config = {
            "signals": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "pair",
                            "signal_type",
                            "entry_price",
                            "created_at",
                        ],
                        "properties": {
                            "pair": {"bsonType": "string"},
                            "signal_type": {"enum": ["BUY", "SELL"]},
                            "entry_price": {"bsonType": "number"},
                            "stop_loss": {"bsonType": "number"},
                            "take_profit": {"bsonType": "number"},
                            "created_at": {"bsonType": "date"},
                            "status": {
                                "enum": ["ACTIVE", "FILLED", "CANCELLED", "EXPIRED"]
                            },
                        },
                    }
                }
            },
            "market_data": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "pair",
                            "timeframe",
                            "timestamp",
                            "open",
                            "high",
                            "low",
                            "close",
                        ],
                        "properties": {
                            "pair": {"bsonType": "string"},
                            "timeframe": {"bsonType": "string"},
                            "timestamp": {"bsonType": "date"},
                            "open": {"bsonType": "number"},
                            "high": {"bsonType": "number"},
                            "low": {"bsonType": "number"},
                            "close": {"bsonType": "number"},
                            "volume": {"bsonType": "number"},
                        },
                    }
                },
                "timeseries": {
                    "timeField": "timestamp",
                    "metaField": "metadata",
                    "granularity": "minutes",
                },
            },
            "strategies": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "name",
                            "strategy_type",
                            "parameters",
                            "created_at",
                        ],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "strategy_type": {"bsonType": "string"},
                            "parameters": {"bsonType": "object"},
                            "is_active": {"bsonType": "bool"},
                            "created_at": {"bsonType": "date"},
                        },
                    }
                }
            },
            "migrations": {
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["version", "name", "status", "executed_at"],
                        "properties": {
                            "version": {"bsonType": "string"},
                            "name": {"bsonType": "string"},
                            "status": {
                                "enum": [
                                    "pending",
                                    "running",
                                    "completed",
                                    "failed",
                                    "rolled_back",
                                ]
                            },
                            "executed_at": {"bsonType": "date"},
                        },
                    }
                }
            },
        }

        existing_collections = await database.list_collection_names()

        for collection_name, config in collections_config.items():
            if collection_name not in existing_collections:
                try:
                    # Create time-series collection for market data
                    if collection_name == "market_data" and "timeseries" in config:
                        await database.create_collection(
                            collection_name,
                            validator=config.get("validator"),
                            timeseries=config["timeseries"],
                        )
                        logger.info(
                            f"Created time-series collection: {collection_name}"
                        )
                    else:
                        await database.create_collection(
                            collection_name, validator=config.get("validator")
                        )
                        logger.info(f"Created collection: {collection_name}")

                except Exception as e:
                    logger.error(
                        f"Failed to create collection {collection_name}: {str(e)}"
                    )
                    raise
            else:
                logger.info(f"Collection {collection_name} already exists")

    async def _create_indexes(self, database) -> None:
        """Create performance indexes on collections."""

        indexes_config = {
            "signals": [
                # Individual indexes
                ("pair", 1),
                ("created_at", -1),
                ("status", 1),
                ("signal_type", 1),
                ("strategy_id", 1),
                # Compound indexes for common queries
                [("pair", 1), ("created_at", -1)],
                [("status", 1), ("created_at", -1)],
                [("strategy_id", 1), ("created_at", -1)],
                [("pair", 1), ("status", 1)],
            ],
            "market_data": [
                # Time-series optimized indexes
                ("pair", 1),
                ("timeframe", 1),
                ("timestamp", -1),
                # Compound indexes for time-series queries
                [("pair", 1), ("timeframe", 1), ("timestamp", -1)],
                [("pair", 1), ("timestamp", -1)],
            ],
            "strategies": [
                ("name", 1),
                ("strategy_type", 1),
                ("is_active", 1),
                ("created_at", -1),
                # Compound indexes
                [("strategy_type", 1), ("is_active", 1)],
            ],
            "migrations": [
                ("version", 1),  # Unique index for version
                ("executed_at", -1),
                ("status", 1),
            ],
        }

        for collection_name, indexes in indexes_config.items():
            collection = database[collection_name]

            for index_spec in indexes:
                try:
                    if isinstance(index_spec, tuple):
                        # Simple index
                        index_name = f"{index_spec[0]}_{index_spec[1]}"
                        await collection.create_index(
                            [index_spec], name=index_name, background=True
                        )
                    elif isinstance(index_spec, list):
                        # Compound index
                        index_name = "_".join(
                            [f"{field}_{direction}" for field, direction in index_spec]
                        )
                        await collection.create_index(
                            index_spec, name=index_name, background=True
                        )

                    logger.debug(f"Created index on {collection_name}: {index_spec}")

                except Exception as e:
                    # Don't fail if index already exists
                    if "already exists" not in str(e).lower():
                        logger.error(
                            f"Failed to create index {index_spec} on {collection_name}: {str(e)}"
                        )
                        raise

        logger.info("Database indexes created successfully")

    async def _insert_initial_data(self, database) -> None:
        """Insert initial data required by the system."""

        # Insert default strategies if they don't exist
        strategies_collection = database["strategies"]

        default_strategies = [
            {
                "name": "MA_Crossover_Default",
                "strategy_type": "moving_average_crossover",
                "parameters": {
                    "fast_period": 10,
                    "slow_period": 20,
                    "atr_multiplier": 2.0,
                    "enabled_pairs": ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"],
                },
                "is_active": True,
                "created_at": datetime.utcnow(),
                "description": "Default moving average crossover strategy",
            }
        ]

        for strategy in default_strategies:
            existing = await strategies_collection.find_one({"name": strategy["name"]})
            if not existing:
                await strategies_collection.insert_one(strategy)
                logger.info(f"Inserted default strategy: {strategy['name']}")

        logger.info("Initial data insertion completed")

    async def _verify_setup(self, database) -> None:
        """Verify database setup is correct."""

        # Check that all required collections exist
        required_collections = ["signals", "market_data", "strategies", "migrations"]
        existing_collections = await database.list_collection_names()

        missing_collections = [
            col for col in required_collections if col not in existing_collections
        ]
        if missing_collections:
            raise Exception(f"Missing required collections: {missing_collections}")

        # Check that indexes are created
        for collection_name in required_collections:
            collection = database[collection_name]
            indexes = await collection.list_indexes().to_list(length=None)

            if len(indexes) < 2:  # At least _id and one custom index
                logger.warning(
                    f"Collection {collection_name} has fewer indexes than expected"
                )

        logger.info("Database setup verification completed")


class DatabaseMigrationManager:
    """
    Manages database migrations and schema versioning.

    Handles applying migrations, tracking migration history,
    and rollback capabilities.
    """

    def __init__(self, db_manager):
        """
        Initialize migration manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.migrations: List[Migration] = []
        self._load_migrations()

    def _load_migrations(self) -> None:
        """Load available migrations."""

        # Example migrations - in practice, these would be loaded from files
        self.migrations = [
            Migration(
                version="001",
                name="initial_setup",
                description="Initial database setup with collections and indexes",
                up_script=self._migration_001_up,
                down_script=self._migration_001_down,
            ),
            Migration(
                version="002",
                name="add_user_tables",
                description="Add user management tables",
                up_script=self._migration_002_up,
                down_script=self._migration_002_down,
                dependencies=["001"],
            ),
        ]

    async def run_migrations(self) -> bool:
        """
        Run pending migrations.

        Returns:
            bool: True if all migrations completed successfully
        """
        try:
            if not self.db_manager.is_connected:
                await self.db_manager.connect()

            database = self.db_manager.database

            # Get migration history
            completed_migrations = await self._get_completed_migrations(database)

            # Find pending migrations
            pending_migrations = [
                m for m in self.migrations if m.version not in completed_migrations
            ]

            if not pending_migrations:
                logger.info("No pending migrations found")
                return True

            # Sort migrations by version
            pending_migrations.sort(key=lambda x: x.version)

            # Run each pending migration
            for migration in pending_migrations:
                success = await self._run_migration(database, migration)
                if not success:
                    logger.error(f"Migration {migration.version} failed")
                    return False

            logger.info(f"Successfully completed {len(pending_migrations)} migrations")
            return True

        except Exception as e:
            logger.error(f"Migration execution failed: {str(e)}")
            return False

    async def _get_completed_migrations(self, database) -> List[str]:
        """Get list of completed migration versions."""

        migrations_collection = database["migrations"]
        completed = await migrations_collection.find(
            {"status": MigrationStatus.COMPLETED.value}
        ).to_list(length=None)

        return [migration["version"] for migration in completed]

    async def _run_migration(self, database, migration: Migration) -> bool:
        """Run a single migration."""

        migrations_collection = database["migrations"]
        start_time = datetime.utcnow()

        # Record migration start
        migration_record = {
            "version": migration.version,
            "name": migration.name,
            "status": MigrationStatus.RUNNING.value,
            "executed_at": start_time,
            "execution_time_ms": 0,
        }

        await migrations_collection.insert_one(migration_record)

        try:
            logger.info(f"Running migration {migration.version}: {migration.name}")

            # Execute migration
            await migration.up_script(database)

            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000

            # Update migration record
            await migrations_collection.update_one(
                {"version": migration.version},
                {
                    "$set": {
                        "status": MigrationStatus.COMPLETED.value,
                        "execution_time_ms": execution_time,
                    }
                },
            )

            logger.info(
                f"Migration {migration.version} completed in {execution_time:.2f}ms"
            )
            return True

        except Exception as e:
            # Update migration record with error
            await migrations_collection.update_one(
                {"version": migration.version},
                {
                    "$set": {
                        "status": MigrationStatus.FAILED.value,
                        "error_message": str(e),
                    }
                },
            )

            logger.error(f"Migration {migration.version} failed: {str(e)}")
            return False

    async def _migration_001_up(self, database) -> None:
        """Migration 001: Initial database setup."""
        initializer = DatabaseInitializer(self.db_manager)
        await initializer._create_collections(database)
        await initializer._create_indexes(database)

    async def _migration_001_down(self, database) -> None:
        """Rollback migration 001."""
        # Drop all collections (be careful in production!)
        collections = ["signals", "market_data", "strategies"]
        for collection_name in collections:
            await database.drop_collection(collection_name)

    async def _migration_002_up(self, database) -> None:
        """Migration 002: Add user management tables."""

        # Create users collection
        await database.create_collection(
            "users",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["email", "created_at"],
                    "properties": {
                        "email": {"bsonType": "string"},
                        "name": {"bsonType": "string"},
                        "is_premium": {"bsonType": "bool"},
                        "created_at": {"bsonType": "date"},
                    },
                }
            },
        )

        # Create indexes for users
        users_collection = database["users"]
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("created_at")

    async def _migration_002_down(self, database) -> None:
        """Rollback migration 002."""
        await database.drop_collection("users")


async def initialize_database_system(db_manager) -> bool:
    """
    Complete database system initialization.

    Args:
        db_manager: DatabaseManager instance

    Returns:
        bool: True if initialization successful
    """
    try:
        logger.info("Starting complete database system initialization...")

        # Initialize database
        initializer = DatabaseInitializer(db_manager)
        init_success = await initializer.initialize_database()

        if not init_success:
            logger.error("Database initialization failed")
            return False

        # Run migrations
        migration_manager = DatabaseMigrationManager(db_manager)
        migration_success = await migration_manager.run_migrations()

        if not migration_success:
            logger.error("Database migrations failed")
            return False

        logger.info("Database system initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database system initialization failed: {str(e)}")
        return False
