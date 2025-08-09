"""
Response optimization middleware for improved API performance.

This middleware provides additional response optimizations including:
- Response compression optimization
- Connection keep-alive optimization
- Response size monitoring
- Request timing optimization
"""

import logging
import time
from typing import Callable, Any, Optional, Union, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for optimizing API response performance.

    Provides optimizations for:
    - Response headers for better caching
    - Connection optimization
    - Response time tracking
    - Memory usage optimization
    """

    def __init__(
        self,
        app: Any,
        enable_keepalive: bool = True,
        max_response_size_mb: int = 10,
        enable_timing_headers: bool = True,
    ):
        """
        Initialize response optimization middleware.

        Args:
            app: FastAPI application
            enable_keepalive: Enable HTTP keep-alive optimization
            max_response_size_mb: Maximum response size in MB before compression
            enable_timing_headers: Add timing headers to responses
        """
        super().__init__(app)
        self.enable_keepalive = enable_keepalive
        self.max_response_size_mb = max_response_size_mb
        self.enable_timing_headers = enable_timing_headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and optimize response."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add timing headers if enabled
        if self.enable_timing_headers:
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Timestamp"] = str(int(time.time()))

        # Optimize connection headers
        if self.enable_keepalive:
            response.headers["Connection"] = "keep-alive"
            response.headers["Keep-Alive"] = "timeout=5, max=1000"

        # Add cache optimization headers for static content
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
        elif request.url.path.startswith("/health"):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        elif request.url.path.startswith("/api"):
            # API responses - short cache for performance
            response.headers["Cache-Control"] = "private, max-age=60"  # 1 minute

        # Add security headers that don't impact performance
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        # Log slow responses
        if process_time > 1.0:  # Log responses taking more than 1 second
            logger.warning(
                f"Slow response: {request.method} {request.url.path} took {process_time:.4f}s"
            )

        return response


def add_performance_headers(
    response: Response, metadata: Optional[dict] = None
) -> Response:
    """
    Add performance-related headers to response.

    Args:
        response: FastAPI response object
        metadata: Additional metadata to include in headers

    Returns:
        Response with performance headers added
    """
    # Add metadata as headers
    if metadata:
        if "cache_hit" in metadata:
            response.headers["X-Cache"] = "HIT" if metadata["cache_hit"] else "MISS"

        if "source" in metadata:
            response.headers["X-Data-Source"] = str(metadata["source"])

        if "total_count" in metadata:
            response.headers["X-Total-Count"] = str(metadata["total_count"])

    # Add performance hints
    response.headers["X-DNS-Prefetch-Control"] = "on"

    return response


class ResponseSizeOptimizer:
    """
    Utility class for optimizing response size and memory usage.
    """

    @staticmethod
    def should_compress(content_length: int, content_type: str) -> bool:
        """
        Determine if response should be compressed based on size and type.

        Args:
            content_length: Size of response content in bytes
            content_type: MIME type of response

        Returns:
            True if response should be compressed
        """
        # Don't compress already compressed content
        if content_type in [
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/gzip",
            "application/zip",
        ]:
            return False

        # Compress text-based content over 1KB
        if content_type.startswith(("text/", "application/json", "application/xml")):
            return content_length > 1024

        return False

    @staticmethod
    def optimize_json_response(data: Union[dict, list]) -> Union[dict, list]:
        """
        Optimize JSON response structure for better performance.

        Args:
            data: Response data dictionary

        Returns:
            Optimized response data
        """

        # Remove null/empty values to reduce response size
        def remove_empty(obj):
            if isinstance(obj, dict):
                return {
                    k: remove_empty(v)
                    for k, v in obj.items()
                    if v is not None and v != ""
                }
            elif isinstance(obj, list):
                return [remove_empty(item) for item in obj if item is not None]
            return obj

        return remove_empty(data)


def create_streaming_response(data_generator, content_type: str = "application/json"):
    """
    Create a streaming response for large datasets.

    Args:
        data_generator: Async generator yielding data chunks
        content_type: MIME type of the response

    Returns:
        StreamingResponse for large datasets
    """
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        data_generator,
        media_type=content_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    )
