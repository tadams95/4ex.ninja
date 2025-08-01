"""
MongoDB Connection Manager - Centralized database connection handling

This module provides a robust DatabaseManager class for managing MongoDB connections
with proper connection pooling, health checks, and retry logic following clean
architecture principles.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, TYPE_CHECKING
from contextlib import asynccontextmanager

# Type checking imports - only imported during static analysis
if TYPE_CHECKING:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
    except ImportError:
        AsyncIOMotorClient = Any
        AsyncIOMotorDatabase = Any

# Runtime imports with fallback
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
    from pymongo.errors import (  # type: ignore
        ServerSelectionTimeoutError,
        ConnectionFailure,
        PyMongoError,
        NetworkTimeout,
    )
    from pymongo import ASCENDING, DESCENDING  # type: ignore

    MOTOR_AVAILABLE = True
except ImportError:
    # Fallback for when motor/pymongo is not installed
    MOTOR_AVAILABLE = False
    ServerSelectionTimeoutError = Exception
    ConnectionFailure = Exception
    PyMongoError = Exception
    NetworkTimeout = Exception
    ASCENDING = 1
    DESCENDING = -1

from ..config.settings import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class DatabaseManager:
    """
    Centralized MongoDB connection manager with health monitoring and reconnection.

    This class handles all database connection lifecycle operations including:
    - Connection establishment with retry logic
    - Connection pooling and configuration
    - Health checks and monitoring
    - Graceful connection closing
    - Environment-based configuration
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize the DatabaseManager.

        Args:
            config: Database configuration. If None, loads from environment
        """
        self._config = config or self._load_config_from_env()
        self._client: Optional[Any] = None  # AsyncIOMotorClient when available
        self._database: Optional[Any] = None  # AsyncIOMotorDatabase when available

        # Connection state tracking
        self._is_connected: bool = False
        self._connection_attempts: int = 0
        self._last_health_check: float = 0
        self._health_check_interval: float = 30.0  # seconds

        # Connection retry settings
        self._max_retry_attempts: int = 3
        self._retry_delay: float = 1.0  # seconds
        self._max_retry_delay: float = 30.0  # seconds

    def _load_config_from_env(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        import os

        # Check for MongoDB connection string first
        connection_string = os.getenv("MONGO_CONNECTION_STRING")
        if connection_string:
            # Parse connection string for database name
            db_name = "trading_db"
            if "/" in connection_string:
                parts = connection_string.split("/")
                if len(parts) > 3:
                    db_name = parts[-1].split("?")[0]

            config = DatabaseConfig(name=db_name)
            # Store connection string separately
            setattr(config, "_connection_string", connection_string)
            return config

        # Fallback to individual environment variables
        return DatabaseConfig(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", "27017")),
            name=os.getenv("DATABASE_NAME", "trading_db"),
            username=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
        )

    def _get_connection_string(self) -> str:
        """Get the MongoDB connection string."""
        if hasattr(self._config, "_connection_string"):
            return getattr(self._config, "_connection_string")
        return self._config.get_connection_string()

    async def connect(self) -> None:
        """
        Establish connection to MongoDB with retry logic.

        Raises:
            DatabaseConnectionError: If connection fails after all retries
        """
        if self._is_connected and self._client and self._database:
            logger.info("Database already connected")
            return

        connection_string = self._get_connection_string()
        logger.info(f"Connecting to MongoDB database: {self._config.name}")

        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                if not MOTOR_AVAILABLE:
                    raise DatabaseConnectionError(
                        "Motor library not available. Install with: pip install motor"
                    )

                # Import here to avoid issues when motor is not available
                try:
                    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
                except ImportError:
                    raise DatabaseConnectionError(
                        "Motor library not available. Install with: pip install motor"
                    )

                # Create client with connection pooling configuration
                self._client = AsyncIOMotorClient(
                    connection_string,
                    maxPoolSize=self._config.max_pool_size,
                    minPoolSize=self._config.min_pool_size,
                    maxIdleTimeMS=self._config.max_idle_time_ms,
                    connectTimeoutMS=self._config.connect_timeout_ms,
                    serverSelectionTimeoutMS=self._config.server_selection_timeout_ms,
                    socketTimeoutMS=self._config.socket_timeout_ms,
                    retryWrites=self._config.retry_writes,
                    retryReads=self._config.retry_reads,
                )

                # Get database reference
                if self._client is not None:
                    self._database = self._client[self._config.name]

                    # Test connection with ping
                    await self._client.admin.command("ping")

                self._is_connected = True
                self._connection_attempts = 0
                logger.info(
                    f"Successfully connected to MongoDB database: {self._config.name}"
                )
                return

            except (
                ServerSelectionTimeoutError,
                ConnectionFailure,
                NetworkTimeout,
            ) as e:
                self._connection_attempts = attempt
                error_msg = f"Connection attempt {attempt}/{self._max_retry_attempts} failed: {str(e)}"

                if attempt < self._max_retry_attempts:
                    delay = min(
                        self._retry_delay * (2 ** (attempt - 1)), self._max_retry_delay
                    )
                    logger.warning(f"{error_msg}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{error_msg}. All retry attempts exhausted.")
                    raise DatabaseConnectionError(
                        f"Failed to connect to MongoDB after {self._max_retry_attempts} attempts",
                        original_error=e,
                    )

    async def disconnect(self) -> None:
        """
        Close database connection gracefully.
        """
        if self._client:
            try:
                self._client.close()
                logger.info("Database connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing database connection: {str(e)}")
            finally:
                self._client = None
                self._database = None
                self._is_connected = False

    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            bool: True if database is healthy, False otherwise
        """
        current_time = time.time()

        # Skip frequent health checks
        if current_time - self._last_health_check < self._health_check_interval:
            return self._is_connected

        self._last_health_check = current_time

        if not self._client or not self._database:
            return False

        try:
            # Simple ping to check connectivity
            await self._client.admin.command("ping", maxTimeMS=5000)
            self._is_connected = True
            return True

        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            self._is_connected = False
            return False

    @property
    def database(self) -> Any:
        """
        Get the database instance.

        Returns:
            AsyncIOMotorDatabase: The database instance

        Raises:
            DatabaseConnectionError: If database is not connected
        """
        if not self._is_connected or not self._database:
            raise DatabaseConnectionError(
                "Database not connected. Call connect() first."
            )
        return self._database

    @property
    def client(self) -> Any:
        """
        Get the MongoDB client instance.

        Returns:
            AsyncIOMotorClient: The MongoDB client

        Raises:
            DatabaseConnectionError: If client is not connected
        """
        if not self._is_connected or not self._client:
            raise DatabaseConnectionError(
                "Database client not connected. Call connect() first."
            )
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if database is currently connected."""
        return self._is_connected

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            async with db_manager.transaction() as session:
                # Perform database operations
                await collection.insert_one(doc, session=session)
        """
        if not self._client:
            raise DatabaseConnectionError("Database not connected")

        async with await self._client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                except Exception:
                    await session.abort_transaction()
                    raise

    async def get_collection_names(self) -> list[str]:
        """
        Get list of all collection names in the database.

        Returns:
            List of collection names
        """
        if not self._database:
            raise DatabaseConnectionError("Database not connected")

        return await self._database.list_collection_names()

    async def ensure_indexes(self, collection_indexes: Dict[str, list]) -> None:
        """
        Ensure specified indexes exist on collections.

        Args:
            collection_indexes: Dict mapping collection names to lists of index specifications
                Example: {"signals": [("pair", 1), ("created_at", -1)]}
        """
        if not self._database:
            raise DatabaseConnectionError("Database not connected")

        for collection_name, indexes in collection_indexes.items():
            collection = self._database[collection_name]

            for index_spec in indexes:
                try:
                    if isinstance(index_spec, tuple):
                        # Simple index: ("field_name", direction)
                        await collection.create_index([index_spec])
                    elif isinstance(index_spec, list):
                        # Compound index: [("field1", 1), ("field2", -1)]
                        await collection.create_index(index_spec)
                    else:
                        logger.warning(
                            f"Invalid index specification for {collection_name}: {index_spec}"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to create index {index_spec} on {collection_name}: {str(e)}"
                    )

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information for monitoring.

        Returns:
            Dictionary with connection details
        """
        return {
            "is_connected": self._is_connected,
            "database_name": self._config.name,
            "connection_attempts": self._connection_attempts,
            "last_health_check": self._last_health_check,
            "max_pool_size": self._config.max_pool_size,
            "min_pool_size": self._config.min_pool_size,
        }


# Global database manager instance
db_manager = DatabaseManager()
