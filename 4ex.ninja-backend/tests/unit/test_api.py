"""
API Tests - Basic FastAPI functionality tests

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

    def process_data(self, data: dict) -> dict:
        """Example method that uses structured logging."""
        self.log_info(
            "Processing data",
            extra={
                "data_size": len(data),
                "correlation_id": get_correlation_id(),
                "operation": "data_processing",
            },
        )

        # Simulate some processing
        processed = {
            "original": data,
            "processed_at": time.time(),
            "status": "processed",
        }

        self.log_info(
            "Data processing completed",
            extra={
                "output_size": len(processed),
                "correlation_id": get_correlation_id(),
                "operation": "data_processing",
            },
        )

        return processed


# Initialize service
test_service = TestService()


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {"message": "4ex.ninja Logging Test API", "status": "active"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check performed")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "correlation_id": get_correlation_id(),
    }


@app.get("/test/simple")
async def simple_test():
    """Simple test endpoint that logs basic information."""
    correlation_id = get_correlation_id()

    logger.info(
        "Simple test endpoint called",
        extra={"correlation_id": correlation_id, "endpoint": "/test/simple"},
    )

    return {
        "message": "Simple test successful",
        "correlation_id": correlation_id,
        "timestamp": time.time(),
    }


@app.get("/test/slow")
async def slow_test():
    """Test endpoint that simulates slow operation."""
    correlation_id = get_correlation_id()

    logger.info(
        "Slow test endpoint called",
        extra={"correlation_id": correlation_id, "endpoint": "/test/slow"},
    )

    # Simulate slow operation
    time.sleep(0.2)  # 200ms - will trigger performance warning

    logger.info(
        "Slow operation completed",
        extra={"correlation_id": correlation_id, "duration": "200ms"},
    )

    return {
        "message": "Slow test completed",
        "correlation_id": correlation_id,
        "timestamp": time.time(),
    }


@app.post("/test/data")
async def process_test_data(data: dict):
    """Test endpoint that processes data using our service."""
    correlation_id = get_correlation_id()

    log_with_context(
        "Processing test data request",
        level=logging.INFO,
        context={
            "correlation_id": correlation_id,
            "endpoint": "/test/data",
            "input_keys": list(data.keys()),
        },
    )

    try:
        result = test_service.process_data(data)

        log_with_context(
            "Test data processing successful",
            level=logging.INFO,
            context={"correlation_id": correlation_id, "success": True},
        )

        return {"success": True, "result": result, "correlation_id": correlation_id}

    except Exception as e:
        log_with_context(
            "Test data processing failed",
            level=logging.ERROR,
            context={
                "correlation_id": correlation_id,
                "error": str(e),
                "success": False,
            },
        )

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/error")
async def error_test():
    """Test endpoint that generates an error."""
    correlation_id = get_correlation_id()

    logger.warning(
        "Error test endpoint called - this will generate an error",
        extra={"correlation_id": correlation_id, "endpoint": "/test/error"},
    )

    try:
        # Simulate an error
        raise ValueError("This is a test error for logging demonstration")

    except ValueError as e:
        logger.error(
            "Test error occurred",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )

        raise HTTPException(status_code=400, detail=str(e))


@app.get("/test/user/{user_id}")
async def user_test(user_id: str):
    """Test endpoint with user context."""
    correlation_id = get_correlation_id()

    logger.info(
        "User test endpoint called",
        extra={
            "correlation_id": correlation_id,
            "user_id": user_id,
            "endpoint": "/test/user/{user_id}",
        },
    )

    return {
        "message": f"User test for {user_id}",
        "user_id": user_id,
        "correlation_id": correlation_id,
        "timestamp": time.time(),
    }


@app.get("/test/trading/signal")
async def trading_signal_test():
    """Test endpoint that simulates trading signal processing."""
    correlation_id = get_correlation_id()

    logger.info(
        "Trading signal test started",
        extra={"correlation_id": correlation_id, "operation": "signal_generation"},
    )

    # Simulate signal processing
    signal_data = {
        "pair": "EUR_USD",
        "action": "BUY",
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
        "confidence": 0.85,
    }

    logger.info(
        "Trading signal generated",
        extra={
            "correlation_id": correlation_id,
            "pair": signal_data["pair"],
            "action": signal_data["action"],
            "confidence": signal_data["confidence"],
            "operation": "signal_generation",
        },
    )

    return {
        "signal": signal_data,
        "correlation_id": correlation_id,
        "timestamp": time.time(),
        "status": "generated",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting test API server")

    uvicorn.run(
        "test_api:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
