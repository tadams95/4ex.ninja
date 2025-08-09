"""
Logging Middleware

Request and response logging middleware for FastAPI.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import json
from typing import Optional

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """

    def __init__(
        self, app, log_request_body: bool = False, log_response_body: bool = False
    ):
        """
        Initialize logging middleware.

        Args:
            app: FastAPI application
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next):
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with logging
        """
        start_time = time.time()

        # Extract request details
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": self._get_client_ip(request),
        }

        # Log request body if enabled (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Only log if it's likely JSON and not too large
                    if len(body) < 1024:  # 1KB limit
                        try:
                            request_data["body"] = json.loads(body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            request_data["body"] = "<binary or invalid JSON>"
                    else:
                        request_data["body"] = f"<body too large: {len(body)} bytes>"
            except Exception as e:
                logger.warning(f"Failed to read request body: {e}")

        # Log incoming request
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        logger.debug(f"Request details: {json.dumps(request_data, default=str)}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Extract response details
            response_data = {
                "status_code": response.status_code,
                "headers": self._sanitize_headers(dict(response.headers)),
                "process_time": round(process_time, 3),
            }

            # Log response
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                f"Response: {request.method} {request.url.path} "
                f"-> {response.status_code} in {process_time:.3f}s",
            )
            logger.debug(f"Response details: {json.dumps(response_data, default=str)}")

            # Add custom headers for debugging
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {process_time:.3f}s - {str(exc)}",
                exc_info=True,
            )
            raise

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.

        Args:
            request: HTTP request

        Returns:
            Client IP address or None
        """
        # Check for forwarded IP headers (common in production)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP if multiple
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        if request.client:
            return request.client.host

        return None

    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Remove sensitive headers from logging.

        Args:
            headers: Dictionary of headers

        Returns:
            Sanitized headers dictionary
        """
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "authentication",
        }

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized
