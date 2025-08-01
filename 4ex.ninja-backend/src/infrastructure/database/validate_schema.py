"""Database schema validation and testing utilities."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from src.infrastructure.database.connection import DatabaseManager
from src.infrastructure.database.schema import SchemaInitializer

logger = logging.getLogger(__name__)


async def validate_database_schema_setup() -> Dict[str, Any]:
    """
    Validate the database schema setup and initialization.

    Returns:
        Dict containing validation results and any issues found
    """
    validation_results = {
        "database_connection": False,
        "schema_initialization": False,
        "collections_created": [],
        "indexes_validated": [],
        "errors": [],
        "warnings": [],
    }

    db_manager = None

    try:
        # Test database connection
        db_manager = DatabaseManager()
        await db_manager.connect()
        validation_results["database_connection"] = True
        logger.info("Database connection successful")

        # Get database instance
        database = db_manager.database

        # Initialize schema
        initializer = SchemaInitializer(database)

        # Run schema initialization
        init_results = await initializer.initialize_all_collections()
        validation_results["schema_initialization"] = True
        validation_results["collections_created"] = init_results[
            "initialized_collections"
        ]

        if init_results["failed_collections"]:
            validation_results["errors"].extend(init_results["failed_collections"])

        # Validate schema integrity
        integrity_results = await initializer.validate_schema_integrity()
        validation_results["indexes_validated"] = integrity_results[
            "collections_validated"
        ]

        if integrity_results["missing_indexes"]:
            validation_results["warnings"].extend(integrity_results["missing_indexes"])

        if integrity_results["validation_errors"]:
            validation_results["errors"].extend(integrity_results["validation_errors"])

        logger.info("Schema validation completed successfully")

    except Exception as e:
        error_msg = f"Schema validation failed: {str(e)}"
        logger.error(error_msg)
        validation_results["errors"].append({"general": error_msg})

    finally:
        if db_manager:
            await db_manager.disconnect()

    return validation_results


async def test_collection_operations() -> Dict[str, Any]:
    """
    Test basic CRUD operations on schema-validated collections.

    Returns:
        Dict containing test results
    """
    test_results = {"crud_tests": [], "validation_tests": [], "errors": []}

    db_manager = None

    try:
        # Connect to database
        db_manager = DatabaseManager()
        await db_manager.connect()
        database = db_manager.database

        # Test data for each collection
        test_data = {
            "signals": {
                "signal_id": "test_signal_001",
                "strategy_id": "test_strategy_001",
                "pair": "EUR/USD",
                "signal_type": "entry",
                "entry_price": 1.0850,
                "position_size": 0.1,
                "timestamp": datetime.utcnow(),
                "status": "pending",
                "metadata": {"test": True},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            "market_data": {
                "pair": "EUR/USD",
                "timeframe": "H1",
                "timestamp": datetime.utcnow(),
                "open": 1.0850,
                "high": 1.0865,
                "low": 1.0840,
                "close": 1.0860,
                "volume": 1000,
                "metadata": {},
                "created_at": datetime.utcnow(),
            },
            "strategies": {
                "strategy_id": "test_strategy_001",
                "name": "Test Strategy",
                "type": "trend_following",
                "parameters": {"test": True},
                "risk_parameters": {"max_risk": 0.02},
                "status": "testing",
                "performance_metrics": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        }

        # Test each collection
        for collection_name, data in test_data.items():
            try:
                collection = database[collection_name]

                # Test insert
                insert_result = await collection.insert_one(data)
                test_results["crud_tests"].append(
                    {
                        "collection": collection_name,
                        "operation": "insert",
                        "success": bool(insert_result.inserted_id),
                        "document_id": str(insert_result.inserted_id),
                    }
                )

                # Test find
                find_result = await collection.find_one(
                    {"_id": insert_result.inserted_id}
                )
                test_results["crud_tests"].append(
                    {
                        "collection": collection_name,
                        "operation": "find",
                        "success": find_result is not None,
                    }
                )

                # Test validation by trying invalid data
                invalid_data = {"invalid": "data"}
                try:
                    await collection.insert_one(invalid_data)
                    test_results["validation_tests"].append(
                        {
                            "collection": collection_name,
                            "validation_working": False,
                            "note": "Invalid data was accepted",
                        }
                    )
                except Exception:
                    test_results["validation_tests"].append(
                        {
                            "collection": collection_name,
                            "validation_working": True,
                            "note": "Invalid data correctly rejected",
                        }
                    )

                # Clean up test data
                await collection.delete_one({"_id": insert_result.inserted_id})

            except Exception as e:
                test_results["errors"].append(
                    {"collection": collection_name, "error": str(e)}
                )

    except Exception as e:
        test_results["errors"].append({"general": str(e)})

    finally:
        if db_manager:
            await db_manager.disconnect()

    return test_results


async def run_comprehensive_validation() -> Dict[str, Any]:
    """
    Run comprehensive database schema validation and testing.

    Returns:
        Dict containing all validation and test results
    """
    logger.info("Starting comprehensive database schema validation")

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "schema_validation": {},
        "operation_tests": {},
        "overall_status": "unknown",
        "summary": {},
    }

    try:
        # Run schema validation
        results["schema_validation"] = await validate_database_schema_setup()

        # Run operation tests
        results["operation_tests"] = await test_collection_operations()

        # Determine overall status
        schema_ok = (
            results["schema_validation"]["database_connection"]
            and results["schema_validation"]["schema_initialization"]
            and len(results["schema_validation"]["errors"]) == 0
        )

        operations_ok = len(results["operation_tests"]["errors"]) == 0

        if schema_ok and operations_ok:
            results["overall_status"] = "success"
        elif schema_ok:
            results["overall_status"] = "partial"
        else:
            results["overall_status"] = "failed"

        # Create summary
        results["summary"] = {
            "collections_initialized": len(
                results["schema_validation"]["collections_created"]
            ),
            "indexes_validated": len(results["schema_validation"]["indexes_validated"]),
            "crud_tests_passed": len(
                [t for t in results["operation_tests"]["crud_tests"] if t["success"]]
            ),
            "validation_tests_passed": len(
                [
                    t
                    for t in results["operation_tests"]["validation_tests"]
                    if t["validation_working"]
                ]
            ),
            "total_errors": len(results["schema_validation"]["errors"])
            + len(results["operation_tests"]["errors"]),
            "total_warnings": len(results["schema_validation"]["warnings"]),
        }

        logger.info(
            f"Comprehensive validation completed with status: {results['overall_status']}"
        )

    except Exception as e:
        logger.error(f"Comprehensive validation failed: {e}")
        results["overall_status"] = "error"
        results["error"] = str(e)

    return results


if __name__ == "__main__":
    # Run validation when script is executed directly
    async def main():
        results = await run_comprehensive_validation()

        print("=== Database Schema Validation Results ===")
        print(f"Overall Status: {results['overall_status']}")
        print(f"Timestamp: {results['timestamp']}")

        if results.get("summary"):
            print("\nSummary:")
            for key, value in results["summary"].items():
                print(f"  {key}: {value}")

        if results.get("schema_validation", {}).get("errors"):
            print("\nSchema Errors:")
            for error in results["schema_validation"]["errors"]:
                print(f"  - {error}")

        if results.get("operation_tests", {}).get("errors"):
            print("\nOperation Test Errors:")
            for error in results["operation_tests"]["errors"]:
                print(f"  - {error}")

        print("\n=== Validation Complete ===")

    asyncio.run(main())
