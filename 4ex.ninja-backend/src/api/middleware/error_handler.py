"""
Error Handler Middleware

Centralized error handling for FastAPI requests.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from infrastructure.monitoring.error_tracking import error_tracker

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    error_tracker = None

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling and logging API errors.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle any errors.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with proper error handling
        """
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Log request completion
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"completed in {process_time:.3f}s "
                f"with status {response.status_code}"
            )

            return response

        except HTTPException as exc:
            # Handle known HTTP exceptions
            logger.warning(
                f"{request.method} {request.url.path} "
                f"failed with HTTP {exc.status_code}: {exc.detail}"
            )

            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code,
                    "path": str(request.url.path),
                },
            )

        except Exception as exc:
            # Handle unexpected errors
            process_time = time.time() - start_time

            logger.error(
                f"{request.method} {request.url.path} "
                f"failed after {process_time:.3f}s: {str(exc)}",
                exc_info=True,
            )

            # Track error in monitoring system
            if MONITORING_AVAILABLE and error_tracker:
                try:
                    from infrastructure.monitoring.error_tracking import (
                        ErrorCategory,
                        ErrorSeverity,
                    )

                    error_tracker.capture_error(
                        exception=exc,
                        category=ErrorCategory.API_ERROR,
                        severity=ErrorSeverity.ERROR,
                        context={
                            "request_method": request.method,
                            "request_path": str(request.url.path),
                            "process_time": process_time,
                        },
                    )
                except Exception as tracking_error:
                    logger.error(f"Failed to track error: {tracking_error}")

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "status_code": 500,
                    "path": str(request.url.path),
                    "message": "An unexpected error occurred. Please try again later.",
                },
            )
