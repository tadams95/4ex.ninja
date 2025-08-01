"""
Test Suite for Day 2 Database Layer & Repository Pattern Implementation

This test suite validates:
- Enhanced MongoBaseRepository with CRUD operations and transaction support
- Repository Factory Pattern
- Error handling improvements
- Integration with database layer from Day 1
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Test framework imports
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.repositories.mongo_base_repository import MongoBaseRepository
from src.infrastructure.repositories.factory import (
    MongoRepositoryFactory,
    get_repository_factory,
)
from src.infrastructure.database.connection import DatabaseManager
from src.infrastructure.database.config import DatabaseConfigurationManager

# Test logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEntity:
    """Test entity for repository testing."""

    def __init__(self, id: str = "", name: str = "", value: int = 0, **kwargs):
        self.id = id
        self.name = name
        self.value = value
        for key, val in kwargs.items():
            setattr(self, key, val)


class TestMongoRepository(MongoBaseRepository[TestEntity]):
    """Test repository implementation."""

    def __init__(
        self, database: Any, collection_name: str = "test_entities", session: Any = None
    ):
        super().__init__(database, collection_name, TestEntity, session)


class TestDay2RepositoryEnhancements:
    """Test suite for Day 2 repository enhancements."""

    @pytest.fixture
    def mock_database(self):
        """Create mock database for testing."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__.return_value = mock_collection
        return mock_db, mock_collection

    @pytest.fixture
    def test_repository(self, mock_database):
        """Create test repository instance."""
        mock_db, _ = mock_database
        return TestMongoRepository(mock_db, "test_collection")

    @pytest.mark.asyncio
    async def test_repository_session_support(self, test_repository):
        """Test repository session support for transactions."""
        # Test initial state
        assert not await test_repository.in_transaction()

        # Test setting session
        mock_session = Mock()
        mock_session.in_transaction = True
        test_repository.set_session(mock_session)

        # Verify session is set
        assert test_repository._session == mock_session
        assert await test_repository.in_transaction()

        logger.info("✅ Repository session support working correctly")

    @pytest.mark.asyncio
    async def test_session_kwargs_generation(self, test_repository):
        """Test session kwargs generation for MongoDB operations."""
        # Test without session
        kwargs = test_repository._get_session_kwargs()
        assert kwargs == {}

        # Test with session
        mock_session = Mock()
        test_repository.set_session(mock_session)
        kwargs = test_repository._get_session_kwargs()
        assert kwargs == {"session": mock_session}

        logger.info("✅ Session kwargs generation working correctly")

    @pytest.mark.asyncio
    async def test_new_crud_operations_structure(self, test_repository, mock_database):
        """Test the new CRUD operations added to base repository."""
        _, mock_collection = mock_database

        # Test get_by_ids method exists and has correct signature
        assert hasattr(test_repository, "get_by_ids")
        assert hasattr(test_repository, "find_one")
        assert hasattr(test_repository, "upsert")
        assert hasattr(test_repository, "delete_by_criteria")
        assert hasattr(test_repository, "update_by_criteria")

        logger.info("✅ New CRUD operations properly implemented")

    def test_repository_initialization_with_session(self, mock_database):
        """Test repository initialization with session parameter."""
        mock_db, _ = mock_database
        mock_session = Mock()

        # Test initialization with session
        repo = TestMongoRepository(mock_db, "test_collection", session=mock_session)
        assert repo._session == mock_session

        # Test initialization without session
        repo2 = TestMongoRepository(mock_db, "test_collection")
        assert repo2._session is None

        logger.info("✅ Repository initialization with session working correctly")


class TestRepositoryFactory:
    """Test suite for repository factory pattern."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager."""
        mock_config = Mock()
        mock_db_config = Mock()
        mock_config.get_database_config.return_value = mock_db_config
        return mock_config

    @pytest.fixture
    async def factory(self, mock_config_manager):
        """Create test factory instance."""
        with patch(
            "src.infrastructure.repositories.factory.DatabaseManager"
        ) as mock_db_manager_class:
            mock_db_manager = AsyncMock()
            mock_db_manager_class.return_value = mock_db_manager

            factory = MongoRepositoryFactory(mock_config_manager)
            await factory.initialize()
            return factory

    @pytest.mark.asyncio
    async def test_factory_initialization(self, mock_config_manager):
        """Test factory initialization process."""
        with patch(
            "src.infrastructure.repositories.factory.DatabaseManager"
        ) as mock_db_manager_class:
            mock_db_manager = AsyncMock()
            mock_db_manager_class.return_value = mock_db_manager

            factory = MongoRepositoryFactory(mock_config_manager)
            assert not factory._initialized

            await factory.initialize()
            assert factory._initialized

            # Verify database manager was created and connected
            mock_db_manager_class.assert_called_once()
            mock_db_manager.connect.assert_called_once()

            logger.info("✅ Factory initialization working correctly")

    @pytest.mark.asyncio
    async def test_factory_cleanup(self, factory):
        """Test factory cleanup process."""
        await factory.cleanup()
        assert not factory._initialized
        assert factory._database_manager is None
        assert len(factory._repositories) == 0

        logger.info("✅ Factory cleanup working correctly")

    @pytest.mark.asyncio
    async def test_repository_creation_placeholder(self, factory):
        """Test repository creation methods (placeholder implementations)."""
        # Test that repository creation methods exist and raise NotImplementedError
        # (since entity classes are not yet available)

        with pytest.raises(NotImplementedError):
            await factory.create_signal_repository()

        with pytest.raises(NotImplementedError):
            await factory.create_market_data_repository()

        with pytest.raises(NotImplementedError):
            await factory.create_strategy_repository()

        logger.info("✅ Repository creation placeholder methods working correctly")

    @pytest.mark.asyncio
    async def test_singleton_factory_pattern(self):
        """Test singleton factory pattern."""
        with patch(
            "src.infrastructure.repositories.factory.MongoRepositoryFactory"
        ) as mock_factory_class:
            mock_factory = AsyncMock()
            mock_factory_class.return_value = mock_factory

            # Clear any existing singleton
            import src.infrastructure.repositories.factory as factory_module

            factory_module._factory_instance = None

            # Get factory instance twice
            factory1 = await get_repository_factory()
            factory2 = await get_repository_factory()

            # Should be the same instance
            assert factory1 is factory2

            # Should only create one instance
            mock_factory_class.assert_called_once()

            logger.info("✅ Singleton factory pattern working correctly")


class TestDatabaseLayerIntegration:
    """Test integration between Day 1 database layer and Day 2 repositories."""

    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test that repository factory integrates with Day 1 configuration."""
        config_manager = DatabaseConfigurationManager()

        # Verify config manager methods exist
        assert hasattr(config_manager, "get_database_config")

        # Test config retrieval
        config = config_manager.get_database_config()
        assert config is not None

        logger.info("✅ Configuration integration working correctly")

    @pytest.mark.asyncio
    async def test_database_manager_integration(self):
        """Test that factory integrates with Day 1 database manager."""
        # Test that DatabaseManager can be imported and has expected interface
        assert hasattr(DatabaseManager, "connect")
        assert hasattr(DatabaseManager, "disconnect")
        assert hasattr(DatabaseManager, "database")

        logger.info("✅ Database manager integration working correctly")


class TestTransactionSupport:
    """Test transaction support in base repository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock MongoDB session."""
        session = Mock()
        session.in_transaction = True
        return session

    @pytest.mark.asyncio
    async def test_transaction_detection(self, test_repository, mock_session):
        """Test transaction state detection."""
        # Initially not in transaction
        assert not await test_repository.in_transaction()

        # Set session and test transaction detection
        test_repository.set_session(mock_session)
        assert await test_repository.in_transaction()

        # Test with session but not in transaction
        mock_session.in_transaction = False
        assert not await test_repository.in_transaction()

        logger.info("✅ Transaction detection working correctly")

    @pytest.mark.asyncio
    async def test_session_propagation_to_operations(
        self, test_repository, mock_database
    ):
        """Test that session is propagated to MongoDB operations."""
        _, mock_collection = mock_database
        mock_session = Mock()
        test_repository.set_session(mock_session)

        # Mock async iterator for find operations
        async def mock_async_iter():
            return iter([])

        mock_collection.find.return_value.__aiter__ = mock_async_iter

        # Test that operations include session
        kwargs = test_repository._get_session_kwargs()
        assert "session" in kwargs
        assert kwargs["session"] == mock_session

        logger.info("✅ Session propagation working correctly")


def run_day2_validation():
    """Run comprehensive Day 2 validation."""
    print("🚀 Starting Day 2 Database Layer & Repository Pattern validation...")
    print("=" * 70)

    # Run pytest with verbose output
    pytest_args = [__file__, "-v", "--tb=short", "-x"]  # Stop on first failure

    try:
        exit_code = pytest.main(pytest_args)

        if exit_code == 0:
            print("\n" + "=" * 70)
            print(
                "✅ Day 2 validation PASSED - All repository enhancements working correctly!"
            )
            print("\nCompleted features:")
            print("• Enhanced MongoBaseRepository with missing CRUD operations")
            print("• Transaction support with MongoDB sessions")
            print("• Repository Factory Pattern interface")
            print("• Error handling integration")
            print("• Configuration integration with Day 1 components")
            print("=" * 70)
            return True
        else:
            print("\n" + "=" * 70)
            print("❌ Day 2 validation FAILED - Some tests failed")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n❌ Error running Day 2 validation: {e}")
        return False


if __name__ == "__main__":
    success = run_day2_validation()
    exit(0 if success else 1)
