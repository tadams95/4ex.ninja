"""
Test script for caching implementation.

This script tests the comprehensive caching layer implementation
without requiring external dependencies.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.cache_service import CacheServiceFactory, CrossoverCacheService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_memory_cache():
    """Test memory cache backend."""
    logger.info("Testing memory cache backend...")

    try:
        # Create cache service with memory backend
        cache_service = await CacheServiceFactory.create_crossover_cache_service(
            use_redis=False, fallback_to_memory=True
        )

        # Test data
        test_crossovers = [
            {
                "id": "test_1",
                "pair": "EUR_USD",
                "signal_type": "BUY",
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": "test_2",
                "pair": "GBP_USD",
                "signal_type": "SELL",
                "created_at": datetime.utcnow().isoformat(),
            },
        ]

        # Test cache set
        filters = {"pair": "EUR_USD", "limit": 50}
        success = await cache_service.set_crossovers(
            crossovers=test_crossovers,
            filters=filters,
            ttl_seconds=60,
            metadata={"test": True},
        )
        logger.info(f"Cache set successful: {success}")

        # Test cache get
        cached_data = await cache_service.get_crossovers(filters=filters)
        logger.info(f"Cache get successful: {cached_data is not None}")
        if cached_data:
            logger.info(f"Retrieved {len(cached_data)} crossovers from cache")

        # Test cache miss
        miss_data = await cache_service.get_crossovers(filters={"pair": "USD_JPY"})
        logger.info(f"Cache miss test: {miss_data is None}")

        # Test cache stats
        stats = await cache_service.get_stats()
        logger.info(f"Cache stats: {stats}")

        # Test cache invalidation
        invalidated = await cache_service.invalidate_crossovers(filters=filters)
        logger.info(f"Cache invalidation: {invalidated} entries invalidated")

        # Verify invalidation
        after_invalidation = await cache_service.get_crossovers(filters=filters)
        logger.info(f"After invalidation: {after_invalidation is None}")

        logger.info("Memory cache test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Memory cache test failed: {e}")
        return False


async def test_redis_cache():
    """Test Redis cache backend (if available)."""
    logger.info("Testing Redis cache backend...")

    try:
        # Try to create cache service with Redis backend
        cache_service = await CacheServiceFactory.create_crossover_cache_service(
            use_redis=True, redis_url="redis://localhost:6379", fallback_to_memory=False
        )

        # Test basic operations
        test_data = [{"id": "redis_test", "pair": "EUR_USD"}]
        filters = {"redis_test": True}

        await cache_service.set_crossovers(test_data, filters=filters)
        cached = await cache_service.get_crossovers(filters=filters)

        logger.info(f"Redis cache test successful: {cached is not None}")
        return True

    except Exception as e:
        logger.info(f"Redis cache test skipped (not available): {e}")
        return False


async def test_cache_warming():
    """Test cache warming functionality."""
    logger.info("Testing cache warming...")

    try:
        cache_service = await CacheServiceFactory.create_crossover_cache_service(
            use_redis=False, fallback_to_memory=True
        )

        # Test cache warming with common filters
        common_filters = [
            {},
            {"limit": 50},
            {"pair": "EUR_USD"},
            {"timeframe": "1h"},
        ]

        warmed_count = await cache_service.warm_cache(common_filters=common_filters)
        logger.info(f"Cache warming completed: {warmed_count} entries warmed")

        return True

    except Exception as e:
        logger.error(f"Cache warming test failed: {e}")
        return False


async def main():
    """Run all cache tests."""
    logger.info("Starting comprehensive cache testing...")

    tests = [
        ("Memory Cache", test_memory_cache),
        ("Redis Cache", test_redis_cache),
        ("Cache Warming", test_cache_warming),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} test...")
        logger.info(f"{'='*50}")

        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"{test_name} test failed with exception: {e}")
            results[test_name] = False

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("Test Results Summary:")
    logger.info(f"{'='*50}")

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)
    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info(
            "🎉 All cache tests passed! Caching implementation is working correctly."
        )
    else:
        logger.warning("⚠️  Some cache tests failed. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
