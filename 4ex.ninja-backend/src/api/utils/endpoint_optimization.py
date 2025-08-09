"""
API endpoint performance optimization utilities.

This module provides utilities for optimizing specific API endpoint performance
including request batching, response streaming, and query optimization.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class RequestBatcher:
    """
    Utility for batching multiple API requests to improve performance.
    """

    def __init__(self, batch_size: int = 10, batch_timeout_seconds: float = 0.1):
        """
        Initialize request batcher.

        Args:
            batch_size: Maximum number of requests per batch
            batch_timeout_seconds: Maximum time to wait for batch to fill
        """
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self._pending_requests = []
        self._batch_lock = asyncio.Lock()

    async def add_request(self, request_func, *args, **kwargs):
        """Add a request to the batch queue."""
        async with self._batch_lock:
            self._pending_requests.append((request_func, args, kwargs))

            # Execute batch if it's full
            if len(self._pending_requests) >= self.batch_size:
                return await self._execute_batch()

            # Wait for timeout and execute partial batch
            await asyncio.sleep(self.batch_timeout_seconds)
            if self._pending_requests:
                return await self._execute_batch()

    async def _execute_batch(self) -> List[Any]:
        """Execute all pending requests in batch."""
        if not self._pending_requests:
            return []

        try:
            # Execute all requests concurrently
            tasks = [
                request_func(*args, **kwargs)
                for request_func, args, kwargs in self._pending_requests
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._pending_requests.clear()

            return results

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            self._pending_requests.clear()
            return []


class ResponseStreamer:
    """
    Utility for streaming large responses to improve perceived performance.
    """

    @staticmethod
    async def stream_json_array(
        data_generator: AsyncGenerator[Dict[str, Any], None], chunk_size: int = 50
    ) -> AsyncGenerator[str, None]:
        """
        Stream JSON array data in chunks.

        Args:
            data_generator: Async generator yielding data items
            chunk_size: Number of items per chunk

        Yields:
            JSON string chunks
        """
        yield "["

        first_item = True
        chunk = []

        async for item in data_generator:
            if not first_item:
                yield ","
            first_item = False

            chunk.append(item)

            if len(chunk) >= chunk_size:
                # Yield chunk as JSON
                chunk_json = json.dumps(chunk)[1:-1]  # Remove array brackets
                yield chunk_json
                chunk = []

        # Yield remaining items
        if chunk:
            if not first_item:
                yield ","
            chunk_json = json.dumps(chunk)[1:-1]
            yield chunk_json

        yield "]"

    @staticmethod
    async def stream_paginated_data(
        fetch_page_func, page_size: int = 100, max_pages: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream paginated data efficiently.

        Args:
            fetch_page_func: Function to fetch a page of data
            page_size: Number of items per page
            max_pages: Maximum number of pages to fetch

        Yields:
            Individual data items
        """
        page = 0

        while max_pages is None or page < max_pages:
            try:
                # Fetch page data
                page_data = await fetch_page_func(
                    offset=page * page_size, limit=page_size
                )

                if not page_data:
                    break

                # Yield individual items
                for item in page_data:
                    yield item

                # Stop if we got less than expected (last page)
                if len(page_data) < page_size:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break


class QueryOptimizer:
    """
    Utility for optimizing database queries to improve response times.
    """

    @staticmethod
    def optimize_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize query filters for better performance.

        Args:
            filters: Original query filters

        Returns:
            Optimized query filters
        """
        optimized = {}

        # Convert string dates to datetime objects for better indexing
        for key, value in filters.items():
            if key.endswith(("_at", "_date", "_time")) and isinstance(value, str):
                try:
                    optimized[key] = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    )
                except ValueError:
                    optimized[key] = value
            else:
                optimized[key] = value

        # Add date range optimization for recent data queries
        if "created_at" not in optimized and "since" not in optimized:
            # Default to last 30 days for better index usage
            optimized["created_at"] = {"$gte": datetime.utcnow() - timedelta(days=30)}

        return optimized

    @staticmethod
    def create_projection(
        fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, int]]:
        """
        Create MongoDB projection from field list.

        Args:
            fields: List of fields to include

        Returns:
            MongoDB projection dict or None
        """
        if not fields:
            return None

        # Always include _id unless explicitly excluded
        projection = {"_id": 1}

        for field in fields:
            if field == "id":
                projection["_id"] = 1
            elif field.startswith("-"):
                # Exclude field
                projection[field[1:]] = 0
            else:
                # Include field
                projection[field] = 1

        return projection

    @staticmethod
    def optimize_sorting(sort_params: Dict[str, Any]) -> List[tuple]:
        """
        Optimize sorting parameters for better index usage.

        Args:
            sort_params: Sorting parameters

        Returns:
            Optimized sort list for MongoDB
        """
        # Default sort by created_at descending for better index usage
        default_sort = [("created_at", -1)]

        if not sort_params:
            return default_sort

        sort_list = []
        for field, direction in sort_params.items():
            if direction in ("desc", "descending", -1):
                sort_list.append((field, -1))
            else:
                sort_list.append((field, 1))

        # Add created_at as secondary sort if not present
        if not any(field == "created_at" for field, _ in sort_list):
            sort_list.append(("created_at", -1))

        return sort_list


class CacheOptimizer:
    """
    Utility for optimizing caching strategies based on request patterns.
    """

    @staticmethod
    def calculate_optimal_ttl(
        request_frequency: float, data_update_frequency: float, base_ttl: int = 300
    ) -> int:
        """
        Calculate optimal TTL based on request and update patterns.

        Args:
            request_frequency: Requests per second
            data_update_frequency: Data updates per second
            base_ttl: Base TTL in seconds

        Returns:
            Optimized TTL in seconds
        """
        # Higher request frequency = longer TTL (more caching benefit)
        # Higher update frequency = shorter TTL (fresher data)

        if data_update_frequency == 0:
            # Static data - use longer TTL
            return min(base_ttl * 10, 3600)  # Max 1 hour

        update_interval = 1 / data_update_frequency
        request_interval = 1 / max(request_frequency, 0.01)  # Avoid division by zero

        # TTL should be a fraction of update interval but consider request frequency
        optimal_ttl = min(
            update_interval * 0.5,  # 50% of update interval
            base_ttl * max(1, request_frequency / 10),  # Scale with request frequency
        )

        return max(int(optimal_ttl), 30)  # Minimum 30 seconds

    @staticmethod
    def should_use_aggressive_caching(endpoint_path: str) -> bool:
        """
        Determine if endpoint should use aggressive caching.

        Args:
            endpoint_path: API endpoint path

        Returns:
            True if aggressive caching should be used
        """
        # Use aggressive caching for relatively static endpoints
        static_endpoints = [
            "/api/v1/market-data/",
            "/api/v1/performance/",
            "/health/",
        ]

        # Use moderate caching for dynamic endpoints
        dynamic_endpoints = [
            "/api/v1/signals/",
        ]

        return any(endpoint_path.startswith(pattern) for pattern in static_endpoints)


# Global instances for reuse
_request_batcher = RequestBatcher()
_query_optimizer = QueryOptimizer()
_cache_optimizer = CacheOptimizer()


async def optimize_endpoint_performance(
    endpoint_func,
    request_params: Dict[str, Any],
    enable_batching: bool = True,
    enable_streaming: bool = False,
    optimize_query: bool = True,
) -> Any:
    """
    Apply performance optimizations to an endpoint function.

    Args:
        endpoint_func: The endpoint function to optimize
        request_params: Request parameters
        enable_batching: Whether to enable request batching
        enable_streaming: Whether to enable response streaming
        optimize_query: Whether to optimize query parameters

    Returns:
        Optimized response
    """
    try:
        # Optimize query parameters
        if optimize_query and "filters" in request_params:
            request_params["filters"] = _query_optimizer.optimize_filters(
                request_params["filters"]
            )

        # Use batching for multiple similar requests
        if enable_batching:
            return await _request_batcher.add_request(endpoint_func, **request_params)

        # Direct execution for single requests
        return await endpoint_func(**request_params)

    except Exception as e:
        logger.error(f"Endpoint optimization failed: {e}")
        # Fallback to direct execution
        return await endpoint_func(**request_params)
