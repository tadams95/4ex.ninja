"""
Simple FastAPI application to test the Day 6 logging middleware.
This demonstrates the complete logging infrastructure working with actual HTTP requests.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import time
import logging

# Import our logging infrastructure
from src.infrastructure.logging import (
    setup_logging,
    setup_middleware,
    get_logger,
    BaseLoggerMixin,
    get_correlation_id,
    log_with_context,
)

# Setup logging first
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="4ex.ninja Logging Test API",
    description="Test API for Day 6 backend logging infrastructure",
    version="1.0.0",
)

# Setup our logging middleware
setup_middleware(
    app,
    log_requests=True,
    log_responses=True,
    log_performance=True,
    log_user_context=True,
    performance_threshold=0.1,  # 100ms threshold for demo
)

# Get logger for our routes
logger = get_logger("api.test")


class TestService(BaseLoggerMixin):
    """Example service using our logging mixin."""

    def __init__(self):
        super().__init__("service.test")

    def slow_operation(self, duration: float = 0.15):
        """Simulate a slow operation."""
        start_time = time.time()
        time.sleep(duration)
        elapsed = time.time() - start_time

        self.log_performance(
            "slow_operation",
            elapsed,
            threshold=0.1,
            requested_duration=duration,
            actual_duration=elapsed,
        )

        return {"operation": "slow_operation", "duration": elapsed}

    def failing_operation(self):
        """Simulate a failing operation."""
        try:
            raise ValueError("Simulated service error")
        except Exception as e:
            self.log_error(
                e,
                "failing_operation",
                service_name="TestService",
                error_category="simulation",
            )
            raise


# Initialize service
test_service = TestService()


@app.get("/")
async def root():
    """Root endpoint with basic logging."""
    log_with_context(
        logger,
        logging.INFO,
        "Root endpoint accessed",
        endpoint="/",
        user_action="browse",
    )

    return {
        "message": "4ex.ninja Logging Test API",
        "correlation_id": get_correlation_id(),
        "status": "operational",
    }


@app.get("/health")
async def health():
    """Health check endpoint (excluded from detailed logging)."""
    return {"status": "healthy", "service": "logging-test-api"}


@app.get("/test/fast")
async def fast_operation():
    """Fast operation to test normal performance logging."""
    log_with_context(
        logger, logging.INFO, "Fast operation requested", operation_type="fast"
    )

    return {
        "operation": "fast",
        "correlation_id": get_correlation_id(),
        "message": "This should be fast",
    }


@app.get("/test/slow")
async def slow_operation():
    """Slow operation to test performance threshold alerts."""
    log_with_context(
        logger, logging.INFO, "Slow operation requested", operation_type="slow"
    )

    result = test_service.slow_operation(0.2)  # 200ms delay

    return {
        "operation": "slow",
        "correlation_id": get_correlation_id(),
        "result": result,
    }


@app.get("/test/error")
async def error_operation():
    """Operation that triggers an error to test error logging."""
    log_with_context(
        logger, logging.INFO, "Error operation requested", operation_type="error"
    )

    try:
        test_service.failing_operation()
    except ValueError as e:
        # Log at route level too
        logger.error(
            f"Route error in /test/error: {str(e)}",
            extra={
                "correlation_id": get_correlation_id(),
                "route": "/test/error",
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail="Simulated error for testing")


from typing import Optional


@app.post("/test/user-action")
async def user_action(data: Optional[dict] = None):
    """POST endpoint to test user action auditing."""
    log_with_context(
        logger,
        logging.INFO,
        "User action endpoint accessed",
        operation_type="user_action",
        data_received=bool(data),
    )

    return {
        "message": "User action logged",
        "correlation_id": get_correlation_id(),
        "data_received": data or {},
    }


@app.get("/test/context")
async def context_test():
    """Test correlation ID and context tracking."""
    correlation_id = get_correlation_id()

    log_with_context(
        logger,
        logging.INFO,
        "Context test endpoint",
        context_test=True,
        correlation_verified=bool(correlation_id),
    )

    return {
        "correlation_id": correlation_id,
        "message": "Check logs for correlation ID tracking",
        "context_working": bool(correlation_id),
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting 4ex.ninja Logging Test API")
    print("📊 Logging middleware active with:")
    print("  - Request/response logging")
    print("  - Performance monitoring (>100ms threshold)")
    print("  - User action auditing")
    print("  - Correlation ID tracking")
    print("  - Error logging with context")
    print()
    print("🔗 Test endpoints:")
    print("  GET  /                  - Root endpoint")
    print("  GET  /health           - Health check (minimal logging)")
    print("  GET  /test/fast        - Fast operation")
    print("  GET  /test/slow        - Slow operation (triggers performance alert)")
    print("  GET  /test/error       - Error operation")
    print("  POST /test/user-action - User action (audit logging)")
    print("  GET  /test/context     - Context tracking test")
    print()

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
