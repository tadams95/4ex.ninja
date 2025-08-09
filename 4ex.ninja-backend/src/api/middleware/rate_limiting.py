"""
Rate limiting middleware for 4ex.ninja API.

Provides flexible rate limiting with different limits for different endpoints
and IP-based tracking. Uses in-memory storage by default with optional Redis support.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import logging
import hashlib
import os

from ..auth.config import auth_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm with in-memory storage.
    Optional Redis support can be added later.
    """

    def __init__(self):
        self._memory_store: Dict[str, list] = {}
        self._cleanup_interval = 300  # Clean up every 5 minutes
        self._last_cleanup = time.time()

    async def is_allowed(
        self, key: str, limit: int, window: int, current_time: Optional[float] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed based on rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., IP address)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            current_time: Current timestamp (for testing)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if current_time is None:
            current_time = time.time()

        # Periodic cleanup of old entries
        if current_time - self._last_cleanup > self._cleanup_interval:
            await self._cleanup_expired_entries(current_time)
            self._last_cleanup = current_time

        return await self._check_memory_rate_limit(key, limit, window, current_time)

    async def _cleanup_expired_entries(self, current_time: float):
        """Clean up expired entries to prevent memory leaks."""
        try:
            expired_keys = []
            for key, requests in self._memory_store.items():
                # Remove entries older than 24 hours
                cutoff_time = current_time - 86400  # 24 hours
                self._memory_store[key] = [
                    req_time for req_time in requests if req_time > cutoff_time
                ]

                # Mark empty lists for deletion
                if not self._memory_store[key]:
                    expired_keys.append(key)

            # Remove empty entries
            for key in expired_keys:
                del self._memory_store[key]

            logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")
        except Exception as e:
            logger.warning(f"Rate limit cleanup failed: {e}")

    async def _check_memory_rate_limit(
        self, key: str, limit: int, window: int, current_time: float
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using in-memory store."""
        if key not in self._memory_store:
            self._memory_store[key] = []

        requests = self._memory_store[key]

        # Remove expired entries
        expire_time = current_time - window
        requests[:] = [req_time for req_time in requests if req_time > expire_time]

        # Add current request
        requests.append(current_time)

        request_count = len(requests)
        remaining = max(0, limit - request_count)
        reset_time = int(current_time + window)

        rate_limit_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": window if request_count > limit else 0,
        }

        return request_count <= limit, rate_limit_info


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""

    def __init__(self, app):
        self.app = app
        self.rate_limiter = RateLimiter()

        # Rate limit configurations
        self.default_limits = {
            "requests": auth_settings.RATE_LIMIT_REQUESTS,
            "window": auth_settings.RATE_LIMIT_WINDOW,
        }

        self.auth_limits = {
            "requests": auth_settings.AUTH_RATE_LIMIT_REQUESTS,
            "window": auth_settings.AUTH_RATE_LIMIT_WINDOW,
        }

        # Paths that require stricter rate limiting
        self.auth_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/token",
        }

        # Paths to exclude from rate limiting
        self.excluded_paths = {"/health", "/docs", "/redoc", "/openapi.json"}

    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object for easier handling
        from fastapi import Request

        request = Request(scope, receive)

        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            await self.app(scope, receive, send)
            return

        # Get client identifier
        client_ip = self._get_client_ip(request)

        # Determine rate limits based on path
        if request.url.path in self.auth_paths:
            limits = self.auth_limits
            rate_limit_key = f"auth:{client_ip}"
        else:
            limits = self.default_limits
            rate_limit_key = f"api:{client_ip}"

        # Check rate limit
        is_allowed, rate_info = await self.rate_limiter.is_allowed(
            rate_limit_key, limits["requests"], limits["window"]
        )

        if not is_allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {rate_info['limit']} per {limits['window']} seconds",
                    "retry_after": rate_info["retry_after"],
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["retry_after"]),
                },
            )
            await response(scope, receive, send)
            return

        # Create a custom send function that adds rate limit headers
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", []))
                message["headers"].extend(
                    [
                        (b"x-ratelimit-limit", str(rate_info["limit"]).encode()),
                        (
                            b"x-ratelimit-remaining",
                            str(rate_info["remaining"]).encode(),
                        ),
                        (b"x-ratelimit-reset", str(rate_info["reset"]).encode()),
                    ]
                )
            await send(message)

        # Process request
        await self.app(scope, receive, send_with_headers)

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address, handling proxies and load balancers.

        Args:
            request: Request object (can be FastAPI Request or raw scope)

        Returns:
            Client IP address
        """
        try:
            # Handle both Request object and raw scope
            if hasattr(request, "headers"):
                # FastAPI Request object
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    return forwarded_for.split(",")[0].strip()

                real_ip = request.headers.get("X-Real-IP")
                if real_ip:
                    return real_ip

                return request.client.host if request.client else "unknown"
            else:
                # Raw ASGI scope
                client = request.get("client")
                return client[0] if client else "unknown"
        except Exception:
            return "unknown"


# Factory function to create rate limit dependency
def create_rate_limit_dependency(requests: int, window: int):
    """
    Create a rate limit dependency for specific endpoints.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds

    Returns:
        Dependency function for FastAPI
    """

    async def rate_limit_dependency(request: Request):
        """Rate limit dependency for specific endpoints."""
        rate_limiter = RateLimiter()
        client_ip = request.client.host if request.client else "unknown"

        # Create a unique key for this endpoint
        endpoint_key = f"endpoint:{request.url.path}:{client_ip}"

        is_allowed, rate_info = await rate_limiter.is_allowed(
            endpoint_key, requests, window
        )

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests to this endpoint. Limit: {requests} per {window} seconds",
                    "retry_after": rate_info["retry_after"],
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["retry_after"]),
                },
            )

    return rate_limit_dependency
