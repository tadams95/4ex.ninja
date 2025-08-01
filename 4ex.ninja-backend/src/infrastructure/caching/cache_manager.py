"""
Caching layer for frequently accessed data.

This module provides a comprehensive caching infrastructure with support for
multiple cache backends, TTL management, cache warming, and intelligent
invalidation strategies.
"""

import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from functools import wraps
import asyncio
from collections import OrderedDict
import pickle

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Represents a cached entry with metadata."""

    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        pass

    @abstractmethod
    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set a value in the cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all values from the cache."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheBackend):
    """
    In-memory cache implementation with LRU eviction and TTL support.

    This cache is suitable for single-process applications and provides
    fast access with automatic cleanup of expired entries.
    """

    def __init__(self, max_size: int = 10000, default_ttl_seconds: int = 3600):
        """
        Initialize the memory cache.

        Args:
            max_size: Maximum number of entries to store
            default_ttl_seconds: Default TTL for entries
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "expired_cleanups": 0,
        }

        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                current_time = datetime.utcnow()
                expired_keys = []

                for key, entry in self._cache.items():
                    if entry.expires_at and current_time > entry.expires_at:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self._cache[key]
                    self._stats["expired_cleanups"] += 1

                if expired_keys:
                    logger.debug(
                        f"Cleaned up {len(expired_keys)} expired cache entries"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(60)

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        try:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check if expired
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["expired_cleanups"] += 1
                return None

            # Update access info and move to end (LRU)
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry.value

        except Exception as e:
            logger.error(f"Error getting cache entry for key {key}: {e}")
            self._stats["misses"] += 1
            return None

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set a value in the cache."""
        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None

            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = 0

            # Create entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=size_bytes,
            )

            # Handle cache size limit
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Remove oldest entry (LRU)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1

            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._stats["sets"] += 1

            return True

        except Exception as e:
            logger.error(f"Error setting cache entry for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        try:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting cache entry for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        if key not in self._cache:
            return False

        entry = self._cache[key]
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            del self._cache[key]
            return False

        return True

    async def clear(self) -> bool:
        """Clear all values from the cache."""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests) if total_requests > 0 else 0

        # Calculate memory usage
        total_size = sum(entry.size_bytes for entry in self._cache.values())

        return {
            "backend": "memory",
            "entries": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate * 100, 2),
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "evictions": self._stats["evictions"],
            "expired_cleanups": self._stats["expired_cleanups"],
            "total_size_bytes": total_size,
            "avg_size_bytes": total_size // len(self._cache) if self._cache else 0,
        }


class CacheManager:
    """
    High-level cache manager with intelligent caching strategies.

    This manager provides automatic key generation, cache warming,
    tag-based invalidation, and performance monitoring.
    """

    def __init__(
        self,
        backend: CacheBackend,
        default_ttl_seconds: int = 3600,
        key_prefix: str = "4ex_ninja",
    ):
        """
        Initialize the cache manager.

        Args:
            backend: Cache backend implementation
            default_ttl_seconds: Default TTL for cached entries
            key_prefix: Prefix for all cache keys
        """
        self.backend = backend
        self.default_ttl_seconds = default_ttl_seconds
        self.key_prefix = key_prefix

        # Cache warming configuration
        self._warm_cache_functions: Dict[str, Callable] = {}

        # Performance tracking
        self._performance_stats = {
            "cache_saves": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time_saved_ms": 0,
        }

    def _generate_cache_key(
        self, namespace: str, identifier: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a consistent cache key.

        Args:
            namespace: Cache namespace (e.g., 'market_data', 'signals')
            identifier: Unique identifier within namespace
            params: Additional parameters to include in key

        Returns:
            Generated cache key
        """
        key_parts = [self.key_prefix, namespace, identifier]

        if params:
            # Sort parameters for consistent key generation
            param_str = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)

        return ":".join(key_parts)

    async def get(
        self, namespace: str, identifier: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            namespace: Cache namespace
            identifier: Unique identifier
            params: Additional parameters

        Returns:
            Cached value or None if not found
        """
        try:
            key = self._generate_cache_key(namespace, identifier, params)
            start_time = time.time()

            result = await self.backend.get(key)

            if result is not None:
                self._performance_stats["cache_hits"] += 1
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit for {key} in {duration_ms:.2f}ms")
            else:
                self._performance_stats["cache_misses"] += 1
                logger.debug(f"Cache miss for {key}")

            return result

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self._performance_stats["cache_misses"] += 1
            return None

    async def set(
        self,
        namespace: str,
        identifier: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            namespace: Cache namespace
            identifier: Unique identifier
            value: Value to cache
            ttl_seconds: TTL override
            params: Additional parameters
            tags: Tags for invalidation

        Returns:
            True if successful
        """
        try:
            key = self._generate_cache_key(namespace, identifier, params)
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

            success = await self.backend.set(key, value, ttl)

            if success:
                self._performance_stats["cache_saves"] += 1
                logger.debug(f"Cached {key} with TTL {ttl}s")

            return success

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(
        self, namespace: str, identifier: str, params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Delete a value from the cache."""
        try:
            key = self._generate_cache_key(namespace, identifier, params)
            return await self.backend.delete(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def invalidate_namespace(self, namespace: str) -> int:
        """
        Invalidate all entries in a namespace.

        Note: This is a simplified implementation for MemoryCache.
        For Redis or other backends, this would use pattern matching.
        """
        try:
            # For memory cache, we need to iterate through all keys
            if isinstance(self.backend, MemoryCache):
                keys_to_delete = []
                prefix = f"{self.key_prefix}:{namespace}:"

                for key in self.backend._cache.keys():
                    if key.startswith(prefix):
                        keys_to_delete.append(key)

                for key in keys_to_delete:
                    await self.backend.delete(key)

                logger.info(
                    f"Invalidated {len(keys_to_delete)} entries in namespace {namespace}"
                )
                return len(keys_to_delete)

            return 0

        except Exception as e:
            logger.error(f"Error invalidating namespace {namespace}: {e}")
            return 0

    def register_warm_cache_function(self, name: str, func: Callable):
        """Register a function for cache warming."""
        self._warm_cache_functions[name] = func

    async def warm_cache(self, function_names: Optional[List[str]] = None):
        """
        Warm the cache by pre-loading frequently accessed data.

        Args:
            function_names: Specific functions to run, or None for all
        """
        functions_to_run = function_names or list(self._warm_cache_functions.keys())

        for func_name in functions_to_run:
            if func_name in self._warm_cache_functions:
                try:
                    logger.info(f"Warming cache with function: {func_name}")
                    await self._warm_cache_functions[func_name]()
                except Exception as e:
                    logger.error(f"Error warming cache with {func_name}: {e}")

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        backend_stats = await self.backend.get_stats()

        total_requests = (
            self._performance_stats["cache_hits"]
            + self._performance_stats["cache_misses"]
        )
        hit_rate = (
            (self._performance_stats["cache_hits"] / total_requests)
            if total_requests > 0
            else 0
        )

        return {
            "manager_stats": {
                "cache_hits": self._performance_stats["cache_hits"],
                "cache_misses": self._performance_stats["cache_misses"],
                "cache_saves": self._performance_stats["cache_saves"],
                "hit_rate_percent": round(hit_rate * 100, 2),
                "total_time_saved_ms": self._performance_stats["total_time_saved_ms"],
            },
            "backend_stats": backend_stats,
        }


def cached(
    namespace: str,
    ttl_seconds: Optional[int] = None,
    cache_manager: Optional[CacheManager] = None,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator for automatic caching of function results.

    Args:
        namespace: Cache namespace
        ttl_seconds: TTL override
        cache_manager: Cache manager instance
        key_builder: Custom key building function

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Use global cache manager if none provided
            nonlocal cache_manager
            if cache_manager is None:
                cache_manager = global_cache_manager

            if cache_manager is None:
                # No cache available, execute function directly
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                identifier = key_builder(*args, **kwargs)
            else:
                # Default key building
                identifier = f"{func.__name__}"
                params = (
                    {"args": str(args), "kwargs": str(kwargs)}
                    if args or kwargs
                    else None
                )

            # Try to get from cache
            cached_result = await cache_manager.get(namespace, identifier, params)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000

            # Cache the result
            await cache_manager.set(namespace, identifier, result, ttl_seconds, params)

            # Track time saved for future cache hits
            cache_manager._performance_stats["total_time_saved_ms"] += int(
                execution_time_ms
            )

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll need to run in async context
            # This is a simplified implementation
            return func(*args, **kwargs)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Global cache manager instance
global_cache_manager: Optional[CacheManager] = None


def initialize_cache_manager(
    backend: Optional[CacheBackend] = None, default_ttl_seconds: int = 3600
) -> CacheManager:
    """Initialize the global cache manager."""
    global global_cache_manager

    if backend is None:
        backend = MemoryCache(max_size=10000, default_ttl_seconds=default_ttl_seconds)

    global_cache_manager = CacheManager(
        backend=backend, default_ttl_seconds=default_ttl_seconds
    )

    logger.info("Cache manager initialized")
    return global_cache_manager


def get_cache_manager() -> Optional[CacheManager]:
    """Get the global cache manager instance."""
    return global_cache_manager
