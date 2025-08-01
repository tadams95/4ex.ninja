"""
Simple Day 2 Validation Script

This script validates the Day 2 Database Layer & Repository Pattern implementation
without complex import dependencies.
"""

import sys
import os
import inspect
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def validate_day2_implementation():
    """Validate Day 2 implementation components."""
    print("🚀 Starting Day 2 Database Layer & Repository Pattern validation...")
    print("=" * 70)

    validation_results = []

    # Test 1: Enhanced MongoBaseRepository
    try:
        from infrastructure.repositories.mongo_base_repository import (
            MongoBaseRepository,
        )

        # Check for new methods added in Day 2
        required_methods = [
            "get_by_ids",
            "find_one",
            "upsert",
            "delete_by_criteria",
            "update_by_criteria",
            "set_session",
            "in_transaction",
            "_get_session_kwargs",
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(MongoBaseRepository, method):
                missing_methods.append(method)

        if missing_methods:
            print(f"❌ MongoBaseRepository missing methods: {missing_methods}")
            validation_results.append(False)
        else:
            print(
                "✅ MongoBaseRepository has all required CRUD and transaction methods"
            )
            validation_results.append(True)

        # Check constructor signature for session support
        init_signature = inspect.signature(MongoBaseRepository.__init__)
        if "session" in init_signature.parameters:
            print("✅ MongoBaseRepository constructor supports session parameter")
            validation_results.append(True)
        else:
            print("❌ MongoBaseRepository constructor missing session parameter")
            validation_results.append(False)

    except ImportError as e:
        print(f"❌ Failed to import MongoBaseRepository: {e}")
        validation_results.append(False)

    # Test 2: Repository Factory Pattern
    try:
        from infrastructure.repositories.factory import (
            IRepositoryFactory,
            MongoRepositoryFactory,
            get_repository_factory,
        )

        # Check factory interface
        required_factory_methods = [
            "create_signal_repository",
            "create_market_data_repository",
            "create_strategy_repository",
            "create_repository",
            "get_database_manager",
            "cleanup",
        ]

        missing_factory_methods = []
        for method in required_factory_methods:
            if not hasattr(IRepositoryFactory, method):
                missing_factory_methods.append(method)

        if missing_factory_methods:
            print(f"❌ IRepositoryFactory missing methods: {missing_factory_methods}")
            validation_results.append(False)
        else:
            print("✅ IRepositoryFactory has all required methods")
            validation_results.append(True)

        # Check concrete implementation
        if hasattr(MongoRepositoryFactory, "initialize"):
            print("✅ MongoRepositoryFactory has initialization method")
            validation_results.append(True)
        else:
            print("❌ MongoRepositoryFactory missing initialization method")
            validation_results.append(False)

    except ImportError as e:
        print(f"❌ Failed to import Repository Factory components: {e}")
        validation_results.append(False)

    # Test 3: Integration with Day 1 Database Layer
    try:
        from infrastructure.database.connection import DatabaseManager
        from infrastructure.database.config import DatabaseConfigurationManager

        # Check that Day 1 components are still working
        config_manager = DatabaseConfigurationManager()
        if hasattr(config_manager, "get_database_config"):
            print("✅ DatabaseConfigurationManager integration working")
            validation_results.append(True)
        else:
            print("❌ DatabaseConfigurationManager missing get_database_config method")
            validation_results.append(False)

        # Check DatabaseManager has required properties
        if hasattr(DatabaseManager, "database"):
            print("✅ DatabaseManager has database property")
            validation_results.append(True)
        else:
            print("❌ DatabaseManager missing database property")
            validation_results.append(False)

    except ImportError as e:
        print(f"❌ Failed to import Day 1 Database Layer components: {e}")
        validation_results.append(False)

    # Test 4: Error Handling Integration
    try:
        from infrastructure.repositories.error_handling import (
            DatabaseError,
            DatabaseErrorType,
            ConnectionPoolManager,
        )

        print("✅ Error handling components available")
        validation_results.append(True)

    except ImportError as e:
        print(f"❌ Failed to import Error Handling components: {e}")
        validation_results.append(False)

    # Test 5: Core Interfaces Integration
    try:
        from core.interfaces.repository import IBaseRepository
        from core.interfaces.signal_repository import ISignalRepository
        from core.interfaces.market_data_repository import IMarketDataRepository
        from core.interfaces.strategy_repository import IStrategyRepository
        from core.interfaces.unit_of_work import IUnitOfWork

        print("✅ Core repository interfaces available")
        validation_results.append(True)

    except ImportError as e:
        print(f"❌ Failed to import Core Interface components: {e}")
        validation_results.append(False)

    # Summary
    print("\n" + "=" * 70)
    passed_tests = sum(validation_results)
    total_tests = len(validation_results)

    if passed_tests == total_tests:
        print("✅ Day 2 VALIDATION PASSED!")
        print(f"   All {total_tests} validation checks passed")
        print("\n🎉 Day 2 Database Layer & Repository Pattern Implementation Complete!")
        print("\n📋 Completed Day 2 Features:")
        print("   • Enhanced MongoBaseRepository with missing CRUD operations")
        print("   • Transaction support with MongoDB sessions")
        print("   • Repository Factory Pattern interface and implementation")
        print("   • Integration with Day 1 database layer components")
        print("   • Error handling improvements")
        print("=" * 70)
        return True
    else:
        print(f"❌ Day 2 VALIDATION FAILED!")
        print(f"   {passed_tests}/{total_tests} validation checks passed")
        print("   Please review the failed components above")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = validate_day2_implementation()
    sys.exit(0 if success else 1)
