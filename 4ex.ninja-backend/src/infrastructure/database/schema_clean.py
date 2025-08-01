"""Database schema initialization and management.

This module provides comprehensive database schema initialization with
optimized indexes for MongoDB collections used in the trading system.
"""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING

# Runtime flags for available libraries
MOTOR_AVAILABLE = False
PYMONGO_AVAILABLE = False

# Import Motor/PyMongo with fallbacks
if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from pymongo import IndexModel, ASCENDING, DESCENDING
    from pymongo.errors import DuplicateKeyError
else:
    try:
        from motor.motor_asyncio import AsyncIOMotorDatabase

        MOTOR_AVAILABLE = True
    except ImportError:
        AsyncIOMotorDatabase = None

    try:
        from pymongo import IndexModel, ASCENDING, DESCENDING
        from pymongo.errors import DuplicateKeyError

        PYMONGO_AVAILABLE = True
    except ImportError:
        IndexModel = None
        ASCENDING = 1
        DESCENDING = -1
        DuplicateKeyError = Exception

logger = logging.getLogger(__name__)


class SchemaInitializer:
    """
    Database schema initialization and management.

    Handles database schema initialization with proper indexing strategies.
    """

    def __init__(self, database):
        """Initialize with database instance."""
        self.database = database

        # Schema definitions for all collections
        self.signal_schema = {
            "bsonType": "object",
            "required": [
                "signal_id",
                "strategy_id",
                "pair",
                "signal_type",
                "timestamp",
                "metadata",
            ],
            "properties": {
                "signal_id": {"bsonType": "string"},
                "strategy_id": {"bsonType": "string"},
                "pair": {"bsonType": "string"},
                "signal_type": {"enum": ["entry", "exit", "stop_loss", "take_profit"]},
                "entry_price": {"bsonType": "number"},
                "exit_price": {"bsonType": ["number", "null"]},
                "stop_loss": {"bsonType": ["number", "null"]},
                "take_profit": {"bsonType": ["number", "null"]},
                "position_size": {"bsonType": "number", "minimum": 0},
                "timestamp": {"bsonType": "date"},
                "executed_at": {"bsonType": ["date", "null"]},
                "status": {"enum": ["pending", "executed", "cancelled", "filled"]},
                "metadata": {"bsonType": "object"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }

        self.market_data_schema = {
            "bsonType": "object",
            "required": [
                "pair",
                "timeframe",
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
            "properties": {
                "pair": {"bsonType": "string"},
                "timeframe": {
                    "enum": ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"]
                },
                "timestamp": {"bsonType": "date"},
                "open": {"bsonType": "number"},
                "high": {"bsonType": "number"},
                "low": {"bsonType": "number"},
                "close": {"bsonType": "number"},
                "volume": {"bsonType": "number", "minimum": 0},
                "spread": {"bsonType": ["number", "null"]},
                "tick_volume": {"bsonType": ["number", "null"]},
                "metadata": {"bsonType": "object"},
                "created_at": {"bsonType": "date"},
            },
        }

        self.strategy_schema = {
            "bsonType": "object",
            "required": ["strategy_id", "name", "type", "status", "created_at"],
            "properties": {
                "strategy_id": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "type": {
                    "enum": [
                        "trend_following",
                        "mean_reversion",
                        "arbitrage",
                        "scalping",
                        "swing",
                    ]
                },
                "description": {"bsonType": ["string", "null"]},
                "parameters": {"bsonType": "object"},
                "risk_parameters": {"bsonType": "object"},
                "status": {"enum": ["active", "inactive", "testing", "disabled"]},
                "performance_metrics": {"bsonType": "object"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
                "last_executed_at": {"bsonType": ["date", "null"]},
            },
        }

        self.user_schema = {
            "bsonType": "object",
            "required": ["user_id", "email", "created_at"],
            "properties": {
                "user_id": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "username": {"bsonType": ["string", "null"]},
                "password_hash": {"bsonType": ["string", "null"]},
                "profile": {"bsonType": "object"},
                "preferences": {"bsonType": "object"},
                "subscription": {"bsonType": "object"},
                "api_keys": {"bsonType": "object"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
                "last_login_at": {"bsonType": ["date", "null"]},
                "is_active": {"bsonType": "bool"},
            },
        }

        self.migration_schema = {
            "bsonType": "object",
            "required": ["migration_id", "version", "applied_at"],
            "properties": {
                "migration_id": {"bsonType": "string"},
                "version": {"bsonType": "string"},
                "description": {"bsonType": ["string", "null"]},
                "applied_at": {"bsonType": "date"},
                "duration_ms": {"bsonType": ["number", "null"]},
                "checksum": {"bsonType": ["string", "null"]},
            },
        }

    def _get_collection_indexes(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get index specifications for a collection."""
        if not PYMONGO_AVAILABLE:
            logger.warning("PyMongo not available, returning empty index specs")
            return []

        indexes = {
            "signals": [
                {
                    "name": "idx_signal_id",
                    "keys": {"signal_id": ASCENDING},
                    "options": {"unique": True},
                },
                {
                    "name": "idx_strategy_pair_timestamp",
                    "keys": {
                        "strategy_id": ASCENDING,
                        "pair": ASCENDING,
                        "timestamp": DESCENDING,
                    },
                    "options": {},
                },
                {
                    "name": "idx_pair_timestamp",
                    "keys": {"pair": ASCENDING, "timestamp": DESCENDING},
                    "options": {},
                },
                {
                    "name": "idx_status_timestamp",
                    "keys": {"status": ASCENDING, "timestamp": DESCENDING},
                    "options": {},
                },
                {
                    "name": "idx_timestamp",
                    "keys": {"timestamp": DESCENDING},
                    "options": {},
                },
            ],
            "market_data": [
                {
                    "name": "idx_pair_timeframe_timestamp",
                    "keys": {
                        "pair": ASCENDING,
                        "timeframe": ASCENDING,
                        "timestamp": DESCENDING,
                    },
                    "options": {"unique": True},
                },
                {
                    "name": "idx_timestamp",
                    "keys": {"timestamp": DESCENDING},
                    "options": {},
                },
                {
                    "name": "idx_pair_timestamp",
                    "keys": {"pair": ASCENDING, "timestamp": DESCENDING},
                    "options": {},
                },
            ],
            "strategies": [
                {
                    "name": "idx_strategy_id",
                    "keys": {"strategy_id": ASCENDING},
                    "options": {"unique": True},
                },
                {
                    "name": "idx_status_type",
                    "keys": {"status": ASCENDING, "type": ASCENDING},
                    "options": {},
                },
                {
                    "name": "idx_created_at",
                    "keys": {"created_at": DESCENDING},
                    "options": {},
                },
            ],
            "users": [
                {
                    "name": "idx_user_id",
                    "keys": {"user_id": ASCENDING},
                    "options": {"unique": True},
                },
                {
                    "name": "idx_email",
                    "keys": {"email": ASCENDING},
                    "options": {"unique": True},
                },
                {
                    "name": "idx_username",
                    "keys": {"username": ASCENDING},
                    "options": {"unique": True, "sparse": True},
                },
            ],
            "migrations": [
                {
                    "name": "idx_migration_id",
                    "keys": {"migration_id": ASCENDING},
                    "options": {"unique": True},
                },
                {
                    "name": "idx_version",
                    "keys": {"version": ASCENDING},
                    "options": {"unique": True},
                },
                {
                    "name": "idx_applied_at",
                    "keys": {"applied_at": DESCENDING},
                    "options": {},
                },
            ],
        }

        return indexes.get(collection_name, [])

    async def _create_indexes(
        self, collection_name: str, index_specs: List[Dict[str, Any]]
    ) -> List[str]:
        """Create indexes for a collection."""
        created_indexes = []

        if not MOTOR_AVAILABLE or not PYMONGO_AVAILABLE or IndexModel is None:
            logger.warning("Motor/PyMongo not available, skipping index creation")
            return created_indexes

        collection = self.database[collection_name]

        for index_spec in index_specs:
            try:
                index_name = index_spec.get("name")
                keys = index_spec["keys"]
                options = index_spec.get("options", {})

                # Convert key specification to index model
                if isinstance(keys, dict):
                    index_keys = [
                        (field, direction) for field, direction in keys.items()
                    ]
                else:
                    index_keys = keys

                index_model = IndexModel(index_keys, name=index_name, **options)

                # Create the index
                result = await collection.create_indexes([index_model])
                created_indexes.extend(result)
                logger.info(
                    f"Created index {index_name or 'unnamed'} on collection {collection_name}"
                )

            except DuplicateKeyError:
                logger.info(
                    f"Index {index_name or 'unnamed'} already exists on collection {collection_name}"
                )
            except Exception as e:
                logger.error(f"Failed to create index on {collection_name}: {e}")
                raise

        return created_indexes

    async def _create_collection_with_schema(
        self, collection_name: str, schema: Dict[str, Any]
    ) -> bool:
        """Create collection with JSON schema validation."""
        if not MOTOR_AVAILABLE:
            logger.warning("Motor not available, skipping collection creation")
            return False

        try:
            # Check if collection exists
            collections = await self.database.list_collection_names()

            if collection_name not in collections:
                # Create collection with validation
                validator = {"$jsonSchema": schema}
                await self.database.create_collection(
                    collection_name,
                    validator=validator,
                    validationLevel="strict",
                    validationAction="error",
                )
                logger.info(
                    f"Created collection {collection_name} with schema validation"
                )
            else:
                # Update validation rules for existing collection
                await self.database.command(
                    {
                        "collMod": collection_name,
                        "validator": {"$jsonSchema": schema},
                        "validationLevel": "strict",
                        "validationAction": "error",
                    }
                )
                logger.info(
                    f"Updated schema validation for collection {collection_name}"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to create/update collection {collection_name}: {e}")
            raise

    async def initialize_collection(self, collection_name: str) -> Dict[str, Any]:
        """Initialize a single collection with schema and indexes."""
        result = {
            "collection": collection_name,
            "schema_created": False,
            "indexes_created": [],
            "time_series_configured": False,
        }

        # Get schema for collection
        schema_map = {
            "signals": self.signal_schema,
            "market_data": self.market_data_schema,
            "strategies": self.strategy_schema,
            "users": self.user_schema,
            "migrations": self.migration_schema,
        }

        schema = schema_map.get(collection_name)
        if not schema:
            logger.warning(f"No schema defined for collection {collection_name}")
            return result

        try:
            # Create collection with schema
            result["schema_created"] = await self._create_collection_with_schema(
                collection_name, schema
            )

            # Create indexes
            index_specs = self._get_collection_indexes(collection_name)
            if index_specs:
                result["indexes_created"] = await self._create_indexes(
                    collection_name, index_specs
                )

            logger.info(f"Successfully initialized collection {collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize collection {collection_name}: {e}")
            raise

        return result

    async def initialize_all_collections(self) -> Dict[str, Any]:
        """Initialize all database collections with schemas and indexes."""
        collections = ["signals", "market_data", "strategies", "users", "migrations"]
        results = {
            "initialized_collections": [],
            "failed_collections": [],
            "total_indexes_created": 0,
        }

        for collection_name in collections:
            try:
                collection_result = await self.initialize_collection(collection_name)
                results["initialized_collections"].append(collection_result)
                results["total_indexes_created"] += len(
                    collection_result["indexes_created"]
                )

            except Exception as e:
                logger.error(f"Failed to initialize collection {collection_name}: {e}")
                results["failed_collections"].append(
                    {"collection": collection_name, "error": str(e)}
                )

        logger.info(
            f"Database schema initialization completed. "
            f"Collections: {len(results['initialized_collections'])}, "
            f"Indexes: {results['total_indexes_created']}"
        )

        return results

    async def validate_schema_integrity(self) -> Dict[str, Any]:
        """Validate database schema integrity and index presence."""
        if not MOTOR_AVAILABLE:
            logger.warning("Motor not available, skipping schema validation")
            return {"status": "skipped", "reason": "Motor not available"}

        validation_result = {
            "collections_validated": [],
            "missing_indexes": [],
            "validation_errors": [],
        }

        collections = ["signals", "market_data", "strategies", "users", "migrations"]

        for collection_name in collections:
            try:
                collection = self.database[collection_name]

                # Check if collection exists
                collections_list = await self.database.list_collection_names()
                if collection_name not in collections_list:
                    validation_result["validation_errors"].append(
                        {
                            "collection": collection_name,
                            "error": "Collection does not exist",
                        }
                    )
                    continue

                # Check indexes
                existing_indexes = await collection.list_indexes().to_list(length=None)
                existing_index_names = {idx["name"] for idx in existing_indexes}

                expected_indexes = self._get_collection_indexes(collection_name)
                expected_index_names = {idx["name"] for idx in expected_indexes}

                missing_indexes = expected_index_names - existing_index_names
                if missing_indexes:
                    validation_result["missing_indexes"].append(
                        {
                            "collection": collection_name,
                            "missing": list(missing_indexes),
                        }
                    )

                validation_result["collections_validated"].append(
                    {
                        "collection": collection_name,
                        "status": "valid",
                        "indexes_present": len(existing_index_names),
                        "indexes_expected": len(expected_index_names),
                    }
                )

            except Exception as e:
                validation_result["validation_errors"].append(
                    {"collection": collection_name, "error": str(e)}
                )

        return validation_result


# Convenience functions for easy import and use
async def initialize_database_schema(database) -> Dict[str, Any]:
    """
    Initialize complete database schema with all collections and indexes.

    Args:
        database: AsyncIOMotorDatabase instance

    Returns:
        Dict containing initialization results
    """
    initializer = SchemaInitializer(database)
    return await initializer.initialize_all_collections()


async def validate_database_schema(database) -> Dict[str, Any]:
    """
    Validate database schema integrity.

    Args:
        database: AsyncIOMotorDatabase instance

    Returns:
        Dict containing validation results
    """
    initializer = SchemaInitializer(database)
    return await initializer.validate_schema_integrity()
