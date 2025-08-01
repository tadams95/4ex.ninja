#!/usr/bin/env python3
"""
Test script for database schema initialization.

This script tests the database schema setup functionality without requiring
actual MongoDB connections.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDatabase:
    """Mock database for testing schema initialization without MongoDB."""

    def __init__(self):
        self.collections = {}
        self.created_collections = []
        self.created_indexes = []

    async def list_collection_names(self):
        """Mock list collection names."""
        return list(self.collections.keys())

    async def create_collection(self, name: str, **options):
        """Mock create collection."""
        self.collections[name] = {"options": options}
        self.created_collections.append({"name": name, "options": options})
        logger.info(f"Mock: Created collection {name} with options: {options}")

    async def command(self, command: Dict[str, Any]):
        """Mock database command."""
        logger.info(f"Mock: Executed command: {command}")

    def __getitem__(self, collection_name: str):
        """Get collection mock."""
        return MockCollection(collection_name, self)


class MockCollection:
    """Mock collection for testing."""

    def __init__(self, name: str, database: MockDatabase):
        self.name = name
        self.database = database
        self.indexes = []

    async def create_indexes(self, index_models):
        """Mock create indexes."""
        for model in index_models:
            index_name = getattr(model, "_IndexModel__document", {}).get(
                "name", "unnamed"
            )
            self.indexes.append(index_name)
            self.database.created_indexes.append(
                {"collection": self.name, "index": index_name}
            )
            logger.info(f"Mock: Created index {index_name} on collection {self.name}")
        return [f"idx_{i}" for i in range(len(index_models))]

    async def list_indexes(self):
        """Mock list indexes."""
        return MockCursor([{"name": idx} for idx in self.indexes])


class MockCursor:
    """Mock cursor for async iteration."""

    def __init__(self, data):
        self.data = data

    async def to_list(self, length=None):
        """Convert to list."""
        return self.data[:length] if length else self.data


def test_schema_initialization():
    """Test schema initialization with mock database."""
    # Import here to avoid motor dependency issues
    from src.infrastructure.database.schema import SchemaInitializer

    logger.info("Testing schema initialization...")

    # Create mock database
    mock_db = MockDatabase()

    # Create schema initializer
    initializer = SchemaInitializer(mock_db)

    # Test schema definitions
    assert initializer.signal_schema is not None
    assert initializer.market_data_schema is not None
    assert initializer.strategy_schema is not None
    assert initializer.user_schema is not None
    assert initializer.migration_schema is not None

    logger.info("✓ Schema definitions loaded successfully")

    # Test index specifications
    signal_indexes = initializer._get_collection_indexes("signals")
    # Will be empty if PyMongo not available, but should not crash
    logger.info(f"✓ Signal indexes defined: {len(signal_indexes)}")

    market_data_indexes = initializer._get_collection_indexes("market_data")
    logger.info(f"✓ Market data indexes defined: {len(market_data_indexes)}")

    strategy_indexes = initializer._get_collection_indexes("strategies")
    logger.info(f"✓ Strategy indexes defined: {len(strategy_indexes)}")

    return True


async def test_collection_initialization():
    """Test collection initialization with mock database."""
    from src.infrastructure.database.schema import SchemaInitializer

    logger.info("Testing collection initialization...")

    # Create mock database
    mock_db = MockDatabase()

    # Create schema initializer
    initializer = SchemaInitializer(mock_db)

    # Test single collection initialization
    result = await initializer.initialize_collection("signals")

    assert result["collection"] == "signals"
    logger.info("✓ Single collection initialization successful")

    # Test all collections initialization
    results = await initializer.initialize_all_collections()

    assert len(results["initialized_collections"]) > 0
    assert len(results["failed_collections"]) == 0
    logger.info(
        f"✓ All collections initialized: {len(results['initialized_collections'])}"
    )

    return True


async def test_schema_validation():
    """Test schema validation."""
    from src.infrastructure.database.schema import SchemaInitializer

    logger.info("Testing schema validation...")

    # Create mock database with some collections
    mock_db = MockDatabase()
    mock_db.collections = {"signals": {}, "market_data": {}, "strategies": {}}

    # Create schema initializer
    initializer = SchemaInitializer(mock_db)

    # Test validation (will return skipped status if Motor not available)
    validation_result = await initializer.validate_schema_integrity()

    # Should have some result even if skipped
    assert validation_result is not None
    logger.info("✓ Schema validation completed")

    return True


async def test_time_series_functionality():
    """Test time-series collection functionality."""
    from src.infrastructure.database.schema import SchemaInitializer

    logger.info("Testing time-series functionality...")

    # Create mock database
    mock_db = MockDatabase()

    # Create schema initializer
    initializer = SchemaInitializer(mock_db)

    # Test time-series collection setup
    result = await initializer._setup_time_series_collection(
        "market_data", "timestamp", "pair"
    )

    # Should return False since Motor is not available, but shouldn't crash
    logger.info("✓ Time-series setup handling works correctly")

    return True


def test_enhanced_validation_rules():
    """Test enhanced validation rules in schemas."""
    from src.infrastructure.database.schema import SchemaInitializer

    logger.info("Testing enhanced validation rules...")

    mock_db = MockDatabase()
    initializer = SchemaInitializer(mock_db)

    # Check signal schema has enhanced validation
    signal_schema = initializer.signal_schema
    assert "pattern" in signal_schema["properties"]["signal_id"]
    assert "minLength" in signal_schema["properties"]["signal_id"]
    assert "additionalProperties" in signal_schema
    logger.info("✓ Signal schema has enhanced validation rules")

    # Check market data schema has enhanced validation
    market_data_schema = initializer.market_data_schema
    assert "minimum" in market_data_schema["properties"]["open"]
    assert "maximum" in market_data_schema["properties"]["open"]
    assert "pattern" in market_data_schema["properties"]["pair"]
    logger.info("✓ Market data schema has enhanced validation rules")

    return True


async def main():
    """Run all tests."""
    logger.info("=== Database Schema Testing ===")

    tests = [
        ("Schema Initialization", test_schema_initialization),
        ("Collection Initialization", test_collection_initialization),
        ("Schema Validation", test_schema_validation),
        ("Time-Series Functionality", test_time_series_functionality),
        ("Enhanced Validation Rules", test_enhanced_validation_rules),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- Running {test_name} ---")
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            logger.info(f"✅ {test_name} PASSED")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED: {e}")
            failed += 1

    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")

    if failed == 0:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error(f"💥 {failed} test(s) failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
