"""
Application-wide logging middleware and utilities.
Provides request/response logging, performance monitoring,
correlation IDs, and user context tracking.

This module provides both generic logging utilities and FastAPI-specific middleware.
The FastAPI components are optional and will only be available if FastAPI is installed.
"""

import time
import uuid
import logging
from typing import Callable, Optional, Dict, Any, TYPE_CHECKING
from contextvars import ContextVar

# Try to import psutil (optional)
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .config import get_logger

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
request_start_time_var: ContextVar[Optional[float]] = ContextVar(
    "request_start_time", default=None
)

# Check if FastAPI is available
try:
    import fastapi
    import starlette

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

if TYPE_CHECKING or FASTAPI_AVAILABLE:
    from fastapi import FastAPI, Request, Response
    from fastapi.routing import APIRoute
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp


class BaseLoggerMixin:
    """Base logging functionality that works without FastAPI."""

    def __init__(self, logger_name: str = "app.middleware"):
        self.logger = get_logger(logger_name)
        self.performance_logger = get_logger("performance")
        self.audit_logger = get_logger("audit")

    def log_operation(
        self,
        operation: str,
        duration: Optional[float] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **extra_data,
    ) -> None:
        """Log an operation with context."""
        log_data = {
            "operation": operation,
            "correlation_id": correlation_id or get_correlation_id(),
            "user_id": user_id or get_user_id(),
            **extra_data,
        }

        if duration is not None:
            log_data["duration"] = round(duration, 3)

        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}

        self.logger.info(f"Operation: {operation}", extra=log_data)

    def log_error(
        self,
        error: Exception,
        operation: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **extra_data,
    ) -> None:
        """Log an error with context."""
        log_data = {
            "operation": operation,
            "error": str(error),
            "error_type": type(error).__name__,
            "correlation_id": correlation_id or get_correlation_id(),
            "user_id": user_id or get_user_id(),
            **extra_data,
        }

        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}

        self.logger.error(
            f"Error in {operation}: {str(error)}", extra=log_data, exc_info=True
        )

    def log_performance(
        self,
        operation: str,
        duration: float,
        threshold: float = 1.0,
        correlation_id: Optional[str] = None,
        **extra_data,
    ) -> None:
        """Log performance metrics."""
        log_data = {
            "operation": operation,
            "duration": round(duration, 3),
            "correlation_id": correlation_id or get_correlation_id(),
            **extra_data,
        }

        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}

        if duration > threshold:
            self.performance_logger.warning(
                f"Slow operation: {operation} took {duration:.3f}s", extra=log_data
            )
        else:
            self.performance_logger.info(
                f"Operation performance: {operation}", extra=log_data
            )


def get_correlation_id() -> Optional[str]:
    """Get current request correlation ID."""
    return correlation_id_var.get()


def get_user_id() -> Optional[str]:
    """Get current request user ID."""
    return user_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def set_user_id(user_id: str) -> None:
    """Set user ID for current context."""
    user_id_var.set(user_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def log_with_context(logger: logging.Logger, level: int, message: str, **extra) -> None:
    """Log message with automatic context injection."""
    context = {
        "correlation_id": get_correlation_id(),
        "user_id": get_user_id(),
        **extra,
    }

    # Remove None values
    context = {k: v for k, v in context.items() if v is not None}

    logger.log(level, message, extra=context)


# FastAPI-specific components (only available if FastAPI is installed)
if FASTAPI_AVAILABLE:

    class LoggingMiddleware(BaseHTTPMiddleware):
        """Middleware for comprehensive request/response logging and monitoring."""

        def __init__(
            self,
            app: ASGIApp,
            logger_name: str = "api.middleware",
            log_requests: bool = True,
            log_responses: bool = True,
            log_performance: bool = True,
            log_user_context: bool = True,
            exclude_paths: Optional[list] = None,
            performance_threshold: float = 1.0,  # seconds
        ):
            super().__init__(app)
            self.logger = get_logger(logger_name)
            self.performance_logger = get_logger("performance")
            self.audit_logger = get_logger("audit")

            self.log_requests = log_requests
            self.log_responses = log_responses
            self.log_performance = log_performance
            self.log_user_context = log_user_context
            self.exclude_paths = exclude_paths or [
                "/health",
                "/metrics",
                "/favicon.ico",
            ]
            self.performance_threshold = performance_threshold

        async def dispatch(self, request: Request, call_next: Callable) -> Response:
            """Process request through logging middleware."""

            # Skip logging for excluded paths
            if self._should_exclude_path(request.url.path):
                return await call_next(request)

            # Setup request context
            correlation_id = self._setup_request_context(request)
            start_time = time.time()
            start_cpu_time = time.process_time()
            start_memory = self._get_memory_usage()

            # Log incoming request
            if self.log_requests:
                self._log_request(request, correlation_id)

            # Process request
            try:
                response = await call_next(request)

                # Calculate performance metrics
                end_time = time.time()
                end_cpu_time = time.process_time()
                end_memory = self._get_memory_usage()

                duration = end_time - start_time
                cpu_time = end_cpu_time - start_cpu_time
                memory_delta = end_memory - start_memory

                # Log response
                if self.log_responses:
                    self._log_response(request, response, duration, correlation_id)

                # Log performance metrics
                if self.log_performance:
                    self._log_performance(
                        request,
                        response,
                        duration,
                        cpu_time,
                        memory_delta,
                        correlation_id,
                    )

                # Log user actions for audit trail
                if self.log_user_context and self._is_user_action(request):
                    self._log_user_action(request, response, correlation_id)

                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id

                return response

            except Exception as exc:
                # Log error
                end_time = time.time()
                duration = end_time - start_time

                self.logger.error(
                    f"Request failed: {request.method} {request.url.path}",
                    extra={
                        "correlation_id": correlation_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration": duration,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                        "user_id": self._get_user_id(request),
                    },
                    exc_info=True,
                )
                raise

        def _setup_request_context(self, request: Request) -> str:
            """Setup request context with correlation ID and user info."""

            # Get or generate correlation ID
            correlation_id = (
                request.headers.get("X-Correlation-ID")
                or request.headers.get("X-Request-ID")
                or str(uuid.uuid4())
            )

            # Get user ID from request (could be from JWT, session, etc.)
            user_id = self._get_user_id(request)

            # Set context variables
            correlation_id_var.set(correlation_id)
            user_id_var.set(user_id)
            request_start_time_var.set(time.time())

            return correlation_id

        def _should_exclude_path(self, path: str) -> bool:
            """Check if path should be excluded from logging."""
            return any(path.startswith(excluded) for excluded in self.exclude_paths)

        def _get_user_id(self, request: Request) -> Optional[str]:
            """Extract user ID from request."""
            # This would integrate with your authentication system
            # Could check JWT token, session, etc.

            # Check for user ID in headers
            user_id = request.headers.get("X-User-ID")
            if user_id:
                return user_id

            # Check for user in request state (set by auth middleware)
            if hasattr(request.state, "user") and request.state.user:
                return getattr(request.state.user, "id", None)

            return None

        def _get_memory_usage(self) -> float:
            """Get current memory usage in MB."""
            if not PSUTIL_AVAILABLE:
                return 0.0

            try:
                import psutil

                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024  # Convert to MB
            except Exception:
                return 0.0

        def _log_request(self, request: Request, correlation_id: str) -> None:
            """Log incoming request details."""

            # Get request body size
            content_length = request.headers.get("content-length")
            body_size = int(content_length) if content_length else 0

            self.logger.info(
                f"Request: {request.method} {request.url.path}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers),
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                    "content_type": request.headers.get("content-type"),
                    "body_size": body_size,
                    "user_id": self._get_user_id(request),
                },
            )

        def _log_response(
            self,
            request: Request,
            response: Response,
            duration: float,
            correlation_id: str,
        ) -> None:
            """Log response details."""

            # Get response body size
            content_length = response.headers.get("content-length")
            body_size = int(content_length) if content_length else 0

            log_level = logging.INFO
            if response.status_code >= 400:
                log_level = (
                    logging.WARNING if response.status_code < 500 else logging.ERROR
                )

            self.logger.log(
                log_level,
                f"Response: {response.status_code} for {request.method} {request.url.path}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": round(duration, 3),
                    "response_size": body_size,
                    "content_type": response.headers.get("content-type"),
                    "user_id": self._get_user_id(request),
                },
            )

        def _log_performance(
            self,
            request: Request,
            response: Response,
            duration: float,
            cpu_time: float,
            memory_delta: float,
            correlation_id: str,
        ) -> None:
            """Log performance metrics."""

            performance_data = {
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": round(duration, 3),
                "cpu_time": round(cpu_time, 3),
                "memory_delta": round(memory_delta, 2),
                "user_id": self._get_user_id(request),
            }

            # Log slow requests with higher severity
            if duration > self.performance_threshold:
                self.performance_logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {duration:.3f}s",
                    extra=performance_data,
                )
            else:
                self.performance_logger.info(
                    f"Request performance: {request.method} {request.url.path}",
                    extra=performance_data,
                )

        def _log_user_action(
            self, request: Request, response: Response, correlation_id: str
        ) -> None:
            """Log user actions for audit trail."""

            user_id = self._get_user_id(request)
            if not user_id:
                return

            # Only log actions that modify data
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                self.audit_logger.info(
                    f"User action: {request.method} {request.url.path}",
                    extra={
                        "correlation_id": correlation_id,
                        "user_id": user_id,
                        "action": f"{request.method} {request.url.path}",
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "client_ip": self._get_client_ip(request),
                        "user_agent": request.headers.get("user-agent"),
                        "timestamp": time.time(),
                    },
                )

        def _is_user_action(self, request: Request) -> bool:
            """Check if request represents a user action worth auditing."""
            # Skip authentication endpoints and health checks
            skip_paths = ["/auth/", "/health", "/metrics", "/docs", "/openapi.json"]
            return not any(request.url.path.startswith(path) for path in skip_paths)

        def _get_client_ip(self, request: Request) -> str:
            """Get client IP address from request."""
            # Check for forwarded headers (proxy/load balancer)
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()

            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip

            # Fallback to direct client IP
            return request.client.host if request.client else "unknown"

    class StructuredLoggingRoute(APIRoute):
        """Custom route class that adds structured logging to FastAPI routes."""

        def get_route_handler(self) -> Callable:
            """Override route handler to add logging context."""
            original_route_handler = super().get_route_handler()

            async def custom_route_handler(request: Request) -> Response:
                # Add route-specific context
                logger = get_logger(f"api.{self.name or 'route'}")

                try:
                    response = await original_route_handler(request)
                    return response
                except Exception as exc:
                    # Log route-specific errors
                    correlation_id = correlation_id_var.get()
                    logger.error(
                        f"Route error in {self.name}: {str(exc)}",
                        extra={
                            "correlation_id": correlation_id,
                            "route_name": self.name,
                            "path": self.path,
                            "method": self.methods,
                            "user_id": user_id_var.get(),
                        },
                        exc_info=True,
                    )
                    raise

            return custom_route_handler

    def setup_middleware(app: FastAPI, **kwargs) -> None:
        """Setup logging middleware for FastAPI application."""
        app.add_middleware(LoggingMiddleware, **kwargs)

        # Replace default route class with structured logging route
        app.router.route_class = StructuredLoggingRoute
