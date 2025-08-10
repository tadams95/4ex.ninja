"""
Cache service for crossover data and API responses.

This module provides high-level caching services for frequently accessed
data with intelligent invalidation and warming strategies.
"""

from infrastructure.logging import get_logger
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from infrastructure.caching.cache_manager import CacheManager
from infrastructure.caching.redis_cache import RedisCache, REDIS_AVAILABLE
from infrastructure.caching.cache_manager import MemoryCache

logger = get_logger(__name__)


@dataclass
class CrossoverCacheKey:
    """Standardized cache key structure for crossover data."""

    namespace: str = "crossovers"
    filters: Optional[Dict[str, Any]] = None

    def to_string(self) -> str:
        """Convert to cache key string."""
        if self.filters:
            # Sort filters for consistent keys
            filter_str = "_".join(f"{k}:{v}" for k, v in sorted(self.filters.items()))
            return f"{self.namespace}:{filter_str}"
        return self.namespace


class CrossoverCacheService:
    """
    High-level cache service for crossover data.

    Provides caching for frequently accessed crossover data with
    automatic invalidation and intelligent cache warming.
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        default_ttl: int = 300,  # 5 minutes
        warm_cache_on_startup: bool = True,
    ):
        """
        Initialize crossover cache service.

        Args:
            cache_manager: Cache manager instance
            default_ttl: Default TTL for cached data in seconds
            warm_cache_on_startup: Whether to warm cache on startup
        """
        self.cache_manager = cache_manager
        self.default_ttl = default_ttl
        self.warm_cache_on_startup = warm_cache_on_startup
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "invalidations": 0,
        }

    async def get_crossovers(
        self,
        filters: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get crossovers from cache or return None if not cached.

        Args:
            filters: Crossover filters
            force_refresh: Skip cache and force refresh

        Returns:
            Cached crossovers or None if not in cache
        """
        if force_refresh:
            return None

        try:
            cache_key = CrossoverCacheKey(filters=filters)
            cached_data = await self.cache_manager.get(
                namespace=cache_key.namespace,
                identifier=cache_key.to_string(),
            )

            if cached_data:
                self._stats["cache_hits"] += 1
                logger.debug(f"Cache hit for crossovers: {cache_key.to_string()}")
                return cached_data.get("crossovers", [])
            else:
                self._stats["cache_misses"] += 1
                logger.debug(f"Cache miss for crossovers: {cache_key.to_string()}")
                return None

        except Exception as e:
            logger.error(f"Error getting crossovers from cache: {e}")
            self._stats["cache_misses"] += 1
            return None

    async def set_crossovers(
        self,
        crossovers: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Cache crossovers with metadata.

        Args:
            crossovers: List of crossover data
            filters: Filters used to generate this data
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata (total count, pagination, etc.)

        Returns:
            True if cached successfully
        """
        try:
            cache_key = CrossoverCacheKey(filters=filters)
            cache_data = {
                "crossovers": crossovers,
                "cached_at": datetime.utcnow().isoformat(),
                "filters": filters,
                "count": len(crossovers),
                **(metadata or {}),
            }

            success = await self.cache_manager.set(
                namespace=cache_key.namespace,
                identifier=cache_key.to_string(),
                value=cache_data,
                ttl_seconds=ttl_seconds or self.default_ttl,
                tags=["crossovers", "api_data"],
            )

            if success:
                self._stats["cache_sets"] += 1
                logger.debug(
                    f"Cached {len(crossovers)} crossovers: {cache_key.to_string()}"
                )

            return success

        except Exception as e:
            logger.error(f"Error caching crossovers: {e}")
            return False

    async def invalidate_crossovers(
        self,
        filters: Optional[Dict[str, Any]] = None,
        invalidate_all: bool = False,
    ) -> int:
        """
        Invalidate cached crossover data.

        Args:
            filters: Specific filters to invalidate (None for all)
            invalidate_all: Whether to invalidate all crossover data

        Returns:
            Number of cache entries invalidated
        """
        try:
            invalidated = 0

            if invalidate_all:
                # Invalidate all crossover data
                invalidated = await self.cache_manager.invalidate_namespace(
                    "crossovers"
                )
                logger.info(f"Invalidated all crossover cache entries: {invalidated}")
            elif filters:
                # Invalidate specific filter combination
                cache_key = CrossoverCacheKey(filters=filters)
                success = await self.cache_manager.delete(
                    namespace=cache_key.namespace,
                    identifier=cache_key.to_string(),
                )
                invalidated = 1 if success else 0
                logger.debug(
                    f"Invalidated specific crossover cache: {cache_key.to_string()}"
                )
            else:
                # Invalidate namespace
                invalidated = await self.cache_manager.invalidate_namespace(
                    "crossovers"
                )
                logger.info(f"Invalidated crossovers namespace: {invalidated}")

            self._stats["invalidations"] += invalidated
            return invalidated

        except Exception as e:
            logger.error(f"Error invalidating crossover cache: {e}")
            return 0

    async def warm_cache(
        self,
        common_filters: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Warm cache with commonly requested data.

        Args:
            common_filters: List of common filter combinations to pre-cache

        Returns:
            Number of cache entries warmed
        """
        if not common_filters:
            # Default common filter combinations
            common_filters = [
                {},  # All crossovers
                {"limit": 50, "offset": 0},  # First page
                {"pairs": ["EUR_USD", "GBP_USD", "USD_JPY"]},  # Major pairs
                {"timeframe": "1h"},  # 1-hour timeframe
                {
                    "since": (datetime.utcnow() - timedelta(hours=24)).isoformat()
                },  # Last 24h
            ]

        warmed = 0
        logger.info(
            f"Starting cache warming for {len(common_filters)} filter combinations"
        )

        for filters in common_filters:
            try:
                # Check if already cached
                cached = await self.get_crossovers(filters=filters)
                if cached is None:
                    # Note: In a real implementation, you'd fetch from the repository here
                    # For now, we'll just log the intention
                    logger.debug(f"Would warm cache for filters: {filters}")
                    # warmed += 1
                else:
                    logger.debug(f"Cache already warm for filters: {filters}")

            except Exception as e:
                logger.error(f"Error warming cache for filters {filters}: {e}")

        logger.info(f"Cache warming completed. Warmed {warmed} entries")
        return warmed

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache service statistics."""
        try:
            cache_stats = await self.cache_manager.backend.get_stats()
        except Exception:
            cache_stats = {}

        return {
            **self._stats,
            "cache_hit_rate": (
                self._stats["cache_hits"]
                / max(self._stats["cache_hits"] + self._stats["cache_misses"], 1)
            )
            * 100,
            "cache_manager_stats": cache_stats,
        }


class CacheServiceFactory:
    """Factory for creating cache services with appropriate backends."""

    @staticmethod
    async def create_cache_manager(
        use_redis: bool = True,
        redis_url: str = "redis://localhost:6379",
        fallback_to_memory: bool = True,
    ) -> CacheManager:
        """
        Create cache manager with Redis or memory backend.

        Args:
            use_redis: Whether to use Redis backend
            redis_url: Redis connection URL
            fallback_to_memory: Whether to fallback to memory cache if Redis fails

        Returns:
            Configured cache manager
        """
        backend = None

        if use_redis and REDIS_AVAILABLE:
            try:
                redis_backend = RedisCache(redis_url=redis_url)
                # Test connection
                await redis_backend._get_redis()
                backend = redis_backend
                logger.info("Using Redis cache backend")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis backend: {e}")
                if not fallback_to_memory:
                    raise

        if backend is None:
            # Fallback to memory cache
            backend = MemoryCache(max_size=10000, default_ttl_seconds=300)
            logger.info("Using memory cache backend")

        return CacheManager(
            backend=backend,
            default_ttl_seconds=300,
            key_prefix="4ex_ninja",
        )

    @staticmethod
    async def create_crossover_cache_service(
        cache_manager: Optional[CacheManager] = None,
        **kwargs,
    ) -> CrossoverCacheService:
        """
        Create crossover cache service with default configuration.

        Args:
            cache_manager: Cache manager instance (will create if None)
            **kwargs: Additional arguments for cache manager creation

        Returns:
            Configured crossover cache service
        """
        if cache_manager is None:
            cache_manager = await CacheServiceFactory.create_cache_manager(**kwargs)

        return CrossoverCacheService(
            cache_manager=cache_manager,
            default_ttl=300,  # 5 minutes
            warm_cache_on_startup=True,
        )
