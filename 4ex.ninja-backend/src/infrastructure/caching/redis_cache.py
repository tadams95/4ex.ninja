"""
Redis cache backend implementation.

This module provides a Redis-based cache backend that implements the
CacheBackend interface for distributed caching across multiple instances.
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import pickle

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis as AsyncRedis

    REDIS_AVAILABLE = True
except ImportError:
    AsyncRedis = None
    aioredis = None
    REDIS_AVAILABLE = False

from .cache_manager import CacheBackend, CacheEntry

logger = logging.getLogger(__name__)


class RedisCache(CacheBackend):
    """
    Redis-based cache backend with async support.

    This backend provides distributed caching capabilities with
    automatic serialization/deserialization and connection pooling.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db: int = 0,
        max_connections: int = 20,
        decode_responses: bool = False,
        health_check_interval: int = 30,
    ):
        """
        Initialize Redis cache backend.

        Args:
            redis_url: Redis connection URL
            db: Redis database number
            max_connections: Maximum number of connections in pool
            decode_responses: Whether to decode responses as strings
            health_check_interval: Health check interval in seconds
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis dependencies not available. Install with: pip install redis aioredis"
            )

        self.redis_url = redis_url
        self.db = db
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self.health_check_interval = health_check_interval
        self._redis: Optional[Any] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "connection_errors": 0,
        }

    async def _get_redis(self) -> Any:
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    self.redis_url,
                    db=self.db,
                    max_connections=self.max_connections,
                    decode_responses=self.decode_responses,
                    health_check_interval=self.health_check_interval,
                )
                # Test connection
                await self._redis.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._stats["connection_errors"] += 1
                raise
        return self._redis

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        try:
            # Use pickle for Python objects, JSON for simple types
            if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                return json.dumps(value).encode("utf-8")
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            # Fallback to pickle
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from Redis storage."""
        try:
            # Try JSON first
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fallback to pickle
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Deserialization error: {e}")
                return None

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis cache."""
        try:
            redis = await self._get_redis()
            data = await redis.get(key)

            if data is None:
                self._stats["misses"] += 1
                return None

            value = self._deserialize(data)
            self._stats["hits"] += 1
            return value

        except Exception as e:
            logger.error(f"Error getting from Redis cache: {e}")
            self._stats["errors"] += 1
            return None

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set a value in Redis cache."""
        try:
            redis = await self._get_redis()
            data = self._serialize(value)

            if ttl_seconds:
                result = await redis.setex(key, ttl_seconds, data)
            else:
                result = await redis.set(key, data)

            self._stats["sets"] += 1
            return bool(result)

        except Exception as e:
            logger.error(f"Error setting Redis cache: {e}")
            self._stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from Redis cache."""
        try:
            redis = await self._get_redis()
            result = await redis.delete(key)
            self._stats["deletes"] += 1
            return bool(result)

        except Exception as e:
            logger.error(f"Error deleting from Redis cache: {e}")
            self._stats["errors"] += 1
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache."""
        try:
            redis = await self._get_redis()
            result = await redis.exists(key)
            return bool(result)

        except Exception as e:
            logger.error(f"Error checking Redis key existence: {e}")
            self._stats["errors"] += 1
            return False

    async def clear(self) -> bool:
        """Clear all values from Redis cache."""
        try:
            redis = await self._get_redis()
            await redis.flushdb()
            return True

        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            self._stats["errors"] += 1
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            redis = await self._get_redis()
            redis_info = await redis.info()

            return {
                **self._stats,
                "backend": "redis",
                "memory_usage": redis_info.get("used_memory", 0),
                "connected_clients": redis_info.get("connected_clients", 0),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0),
                "total_commands_processed": redis_info.get(
                    "total_commands_processed", 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {**self._stats, "backend": "redis", "connection_error": str(e)}

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "crossovers:*")

        Returns:
            Number of keys deleted
        """
        try:
            redis = await self._get_redis()
            keys = await redis.keys(pattern)

            if keys:
                deleted = await redis.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Error invalidating by pattern {pattern}: {e}")
            self._stats["errors"] += 1
            return 0

    async def get_keys_by_pattern(self, pattern: str) -> list:
        """
        Get all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "crossovers:*")

        Returns:
            List of matching keys
        """
        try:
            redis = await self._get_redis()
            keys = await redis.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]

        except Exception as e:
            logger.error(f"Error getting keys by pattern {pattern}: {e}")
            self._stats["errors"] += 1
            return []

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
