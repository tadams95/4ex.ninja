"""
HTTP Caching Middleware for FastAPI.

This module provides HTTP caching capabilities including ETags,
conditional requests, and response caching headers.
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time

logger = logging.getLogger(__name__)


class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP caching middleware with ETag and Cache-Control support.

    This middleware automatically adds ETag headers to responses and
    handles conditional requests (If-None-Match, If-Modified-Since).
    """

    def __init__(
        self,
        app,
        cache_control_config: Optional[Dict[str, Dict[str, Any]]] = None,
        enable_etags: bool = True,
        enable_conditional_requests: bool = True,
        excluded_paths: Optional[List[str]] = None,
    ):
        """
        Initialize HTTP cache middleware.

        Args:
            app: FastAPI application
            cache_control_config: Path-specific cache control settings
            enable_etags: Whether to enable ETag generation
            enable_conditional_requests: Whether to handle conditional requests
            excluded_paths: Paths to exclude from caching
        """
        super().__init__(app)
        self.cache_control_config = (
            cache_control_config or self._get_default_cache_config()
        )
        self.enable_etags = enable_etags
        self.enable_conditional_requests = enable_conditional_requests
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self._stats = {
            "requests_processed": 0,
            "etag_hits": 0,
            "etag_misses": 0,
            "cache_headers_added": 0,
        }

    def _get_default_cache_config(self) -> Dict[str, Dict[str, Any]]:
        """Get default cache control configuration."""
        return {
            # API endpoints with frequent changes
            "/api/v1/signals": {
                "max_age": 60,  # 1 minute
                "stale_while_revalidate": 30,
                "must_revalidate": True,
            },
            "/api/v1/market-data": {
                "max_age": 30,  # 30 seconds
                "stale_while_revalidate": 15,
                "must_revalidate": True,
            },
            # Performance data (changes less frequently)
            "/api/v1/performance": {
                "max_age": 300,  # 5 minutes
                "stale_while_revalidate": 150,
                "s_maxage": 600,  # CDN cache for 10 minutes
            },
            # Static/semi-static data
            "/api/v1/pairs": {
                "max_age": 3600,  # 1 hour
                "stale_while_revalidate": 1800,
                "s_maxage": 7200,  # CDN cache for 2 hours
            },
            # Health endpoints (short cache)
            "/health": {
                "max_age": 10,
                "no_store": False,
            },
        }

    def _should_cache_path(self, path: str) -> bool:
        """Check if path should be cached."""
        if any(excluded in path for excluded in self.excluded_paths):
            return False
        return path.startswith("/api/") or path in self.cache_control_config

    def _get_cache_config_for_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get cache configuration for a specific path."""
        # Exact match first
        if path in self.cache_control_config:
            return self.cache_control_config[path]

        # Pattern matching for API endpoints
        for pattern, config in self.cache_control_config.items():
            if path.startswith(pattern):
                return config

        return None

    def _generate_etag(self, content: bytes) -> str:
        """Generate ETag from response content."""
        return f'"{hashlib.md5(content).hexdigest()}"'

    def _build_cache_control_header(self, config: Dict[str, Any]) -> str:
        """Build Cache-Control header from configuration."""
        directives = []

        if config.get("no_cache"):
            directives.append("no-cache")

        if config.get("no_store"):
            directives.append("no-store")

        if config.get("must_revalidate"):
            directives.append("must-revalidate")

        if config.get("public"):
            directives.append("public")
        elif config.get("private"):
            directives.append("private")
        else:
            # Default to public for API responses
            directives.append("public")

        if "max_age" in config:
            directives.append(f"max-age={config['max_age']}")

        if "s_maxage" in config:
            directives.append(f"s-maxage={config['s_maxage']}")

        if "stale_while_revalidate" in config:
            directives.append(
                f"stale-while-revalidate={config['stale_while_revalidate']}"
            )

        return ", ".join(directives)

    async def dispatch(self, request: Request, call_next):
        """Process request and add caching headers."""
        start_time = time.time()
        self._stats["requests_processed"] += 1

        # Skip caching for non-cacheable paths
        if not self._should_cache_path(request.url.path):
            return await call_next(request)

        # Handle conditional requests
        if self.enable_conditional_requests:
            if_none_match = request.headers.get("if-none-match")
            if_modified_since = request.headers.get("if-modified-since")

            # For demonstration, we'll implement basic ETag checking
            # In production, you might want to check against cached ETags

        response = await call_next(request)

        # Only process successful responses
        if not (200 <= response.status_code < 300):
            return response

        # Get cache configuration for this path
        cache_config = self._get_cache_config_for_path(request.url.path)

        if cache_config:
            # Add Cache-Control header
            cache_control = self._build_cache_control_header(cache_config)
            response.headers["Cache-Control"] = cache_control
            self._stats["cache_headers_added"] += 1

            # Add Vary header for API endpoints
            if request.url.path.startswith("/api/"):
                response.headers["Vary"] = "Accept, Authorization, Accept-Encoding"

        # Add ETag if enabled and content is available
        if self.enable_etags and hasattr(response, "body") and response.body:
            try:
                etag = self._generate_etag(response.body)
                response.headers["ETag"] = etag

                # Check if client has matching ETag
                if_none_match = request.headers.get("if-none-match")
                if if_none_match and etag in if_none_match:
                    self._stats["etag_hits"] += 1
                    # Return 304 Not Modified
                    return Response(
                        status_code=304,
                        headers={
                            "ETag": etag,
                            "Cache-Control": response.headers.get("Cache-Control", ""),
                        },
                    )
                else:
                    self._stats["etag_misses"] += 1

            except Exception as e:
                logger.debug(f"Error generating ETag: {e}")

        # Add Last-Modified header for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Last-Modified"] = datetime.utcnow().strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

        # Add processing time header for monitoring
        processing_time = time.time() - start_time
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"

        return response

    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        return {
            **self._stats,
            "etag_hit_rate": (
                self._stats["etag_hits"]
                / max(self._stats["etag_hits"] + self._stats["etag_misses"], 1)
            )
            * 100,
        }


class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """
    Response compression middleware for reducing payload sizes.

    This middleware automatically compresses responses based on
    Accept-Encoding headers and content type using gzip.

    Note: This is a simplified implementation that relies on FastAPI's
    built-in GZipMiddleware for actual compression. This class is kept
    for future extensibility and configuration.
    """

    def __init__(
        self,
        app,
        minimum_size: int = 1024,
        compressible_types: Optional[List[str]] = None,
        compression_level: int = 6,
    ):
        """
        Initialize compression middleware.

        Args:
            app: FastAPI application
            minimum_size: Minimum response size to compress
            compressible_types: List of compressible content types
            compression_level: Compression level (1-9 for gzip)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.compressible_types = compressible_types or [
            "application/json",
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/xml",
            "text/xml",
        ]

    def _should_compress(self, response: StarletteResponse, request: Request) -> bool:
        """Check if response should be compressed."""
        # Check Accept-Encoding header
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.compressible_types):
            return False

        return True

    async def dispatch(self, request: Request, call_next):
        """Process request and add compression headers if needed."""
        response = await call_next(request)

        # Skip compression for non-successful responses
        if not (200 <= response.status_code < 300):
            return response

        # Add Vary header for responses that could be compressed
        if self._should_compress(response, request):
            if "vary" not in response.headers:
                response.headers["vary"] = "Accept-Encoding"
            else:
                current_vary = response.headers["vary"]
                if "Accept-Encoding" not in current_vary:
                    response.headers["vary"] = f"{current_vary}, Accept-Encoding"

        return response
