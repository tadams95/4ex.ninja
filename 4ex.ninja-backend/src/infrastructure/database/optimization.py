"""
Database connection pool optimization utilities.

This module provides optimizations for MongoDB connection pooling
to improve API response times.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Runtime imports with fallback for MongoDB
try:
    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
    from pymongo.errors import ServerSelectionTimeoutError  # type: ignore

    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = None
    ServerSelectionTimeoutError = Exception


class OptimizedConnectionPool:
    """
    Optimized connection pool manager for MongoDB.

    Provides optimizations for:
    - Connection pool sizing based on load
    - Connection health monitoring
    - Automatic connection management
    - Query performance tracking
    """

    def __init__(
        self,
        connection_string: str,
        min_pool_size: int = 10,
        max_pool_size: int = 100,
        max_idle_time_ms: int = 30000,
        server_selection_timeout_ms: int = 5000,  # Reduced for faster failover
        socket_timeout_ms: int = 3000,  # Reduced for faster response
        connect_timeout_ms: int = 5000,  # Reduced for faster startup
        enable_monitoring: bool = True,
    ):
        """Initialize optimized connection pool."""
        self.connection_string = connection_string
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.max_idle_time_ms = max_idle_time_ms
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self.socket_timeout_ms = socket_timeout_ms
        self.connect_timeout_ms = connect_timeout_ms
        self.enable_monitoring = enable_monitoring

        self._client = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "avg_response_time_ms": 0.0,
        }

    async def get_client(self):
        """Get optimized MongoDB client with connection pooling."""
        if not MOTOR_AVAILABLE:
            logger.warning("MongoDB driver not available")
            return None

        if self._client is None and MOTOR_AVAILABLE and AsyncIOMotorClient:
            try:
                # Create client with optimized settings
                self._client = AsyncIOMotorClient(
                    self.connection_string,
                    minPoolSize=self.min_pool_size,
                    maxPoolSize=self.max_pool_size,
                    maxIdleTimeMS=self.max_idle_time_ms,
                    serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                    socketTimeoutMS=self.socket_timeout_ms,
                    connectTimeoutMS=self.connect_timeout_ms,
                    # Performance optimizations
                    retryWrites=True,
                    retryReads=True,
                    w="majority",  # Write concern for consistency
                    readPreference="secondaryPreferred",  # Read from secondary when possible
                    compressors=["zstd", "zlib"],  # Enable compression
                    maxStalenessSeconds=120,  # Allow slightly stale reads for performance
                )

                # Test connection
                await self._client.admin.command("ping")
                logger.info("Optimized MongoDB connection pool initialized")

            except Exception as e:
                logger.error(f"Failed to initialize optimized connection pool: {e}")
                self._client = None

        return self._client

    @asynccontextmanager
    async def get_database(self, db_name: str):
        """Get database with connection monitoring."""
        client = await self.get_client()
        if not client:
            yield None
            return

        import time

        start_time = time.time()

        try:
            database = client[db_name]
            self._connection_stats["active_connections"] += 1
            yield database

            # Record successful connection
            response_time = (time.time() - start_time) * 1000
            self._update_response_time(response_time)

        except Exception as e:
            self._connection_stats["failed_connections"] += 1
            logger.error(f"Database operation failed: {e}")
            yield None
        finally:
            self._connection_stats["active_connections"] -= 1

    def _update_response_time(self, response_time_ms: float):
        """Update average response time statistics."""
        current_avg = self._connection_stats["avg_response_time_ms"]
        total_connections = self._connection_stats["total_connections"]

        # Calculate running average
        new_avg = (current_avg * total_connections + response_time_ms) / (
            total_connections + 1
        )
        self._connection_stats["avg_response_time_ms"] = new_avg
        self._connection_stats["total_connections"] += 1

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        stats = self._connection_stats.copy()

        if self._client:
            try:
                # Get server info for additional metrics
                client = await self.get_client()
                if client:
                    server_info = await client.admin.command("serverStatus")
                    stats["server_uptime"] = server_info.get("uptime", 0)
                    stats["server_connections"] = server_info.get("connections", {})

            except Exception as e:
                logger.debug(f"Could not get server stats: {e}")

        return stats

    async def health_check(self) -> bool:
        """Perform health check on connection pool."""
        try:
            client = await self.get_client()
            if not client:
                return False

            # Perform a quick ping
            await asyncio.wait_for(
                client.admin.command("ping"),
                timeout=1.0,  # 1 second timeout for health check
            )
            return True

        except Exception as e:
            logger.warning(f"Connection pool health check failed: {e}")
            return False

    async def close(self):
        """Close connection pool."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Connection pool closed")


# Global connection pool instance
_connection_pool: Optional[OptimizedConnectionPool] = None


async def get_optimized_connection_pool(
    connection_string: Optional[str] = None, **kwargs
) -> Optional[OptimizedConnectionPool]:
    """Get or create optimized connection pool instance."""
    global _connection_pool

    if _connection_pool is None and connection_string:
        _connection_pool = OptimizedConnectionPool(connection_string, **kwargs)

    return _connection_pool


async def optimize_query_performance(collection, query: Dict[str, Any], **kwargs):
    """
    Optimize query performance with automatic query analysis.

    Args:
        collection: MongoDB collection
        query: Query parameters
        **kwargs: Additional query options

    Returns:
        Query results with performance optimizations
    """
    if not collection:
        return []

    # Add query optimizations
    optimized_kwargs = {
        "batch_size": 100,  # Optimize batch size for network efficiency
        **kwargs,
    }

    # Add index hints for common query patterns
    if "pair" in query:
        optimized_kwargs["hint"] = [("pair", 1), ("created_at", -1)]
    elif "created_at" in query:
        optimized_kwargs["hint"] = [("created_at", -1)]

    try:
        # Execute query with timeout
        cursor = collection.find(query, **optimized_kwargs)

        # Use to_list with reasonable limit to prevent memory issues
        limit = optimized_kwargs.get("limit", 1000)
        results = await cursor.to_list(length=min(limit, 1000))

        return results

    except Exception as e:
        logger.error(f"Query optimization failed: {e}")
        # Fallback to simple query
        return await collection.find(query).to_list(length=100)
