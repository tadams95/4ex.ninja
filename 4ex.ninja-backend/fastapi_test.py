"""
Quick FastAPI test to verify logging middleware works correctly.
This demonstrates Day 6 backend logging infrastructure with real HTTP requests.
"""

from fastapi import FastAPI
import logging

# Import our logging infrastructure
from src.infrastructure.logging import (
    setup_logging,
    setup_middleware,
    get_logger,
    get_correlation_id
)

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(title="Logging Test", version="1.0.0")

# Setup our logging middleware
setup_middleware(
    app,
    log_requests=True,
    log_responses=True, 
    log_performance=True,
    performance_threshold=0.1  # 100ms threshold
)

logger = get_logger("api.test")

@app.get("/")
async def root():
    """Root endpoint to test logging."""
    correlation_id = get_correlation_id()
    logger.info("Root endpoint accessed", extra={
        "correlation_id": correlation_id,
        "endpoint": "/",
        "action": "test"
    })
    
    return {
        "message": "4ex.ninja Logging Test",
        "correlation_id": correlation_id,
        "status": "logging_active"
    }

@app.get("/test/slow")
async def slow_endpoint():
    """Slow endpoint to test performance monitoring."""
    import time
    time.sleep(0.15)  # 150ms delay
    
    return {
        "message": "Slow operation completed",
        "correlation_id": get_correlation_id()
    }

@app.get("/health")
async def health():
    """Health endpoint (excluded from detailed logging)."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting 4ex.ninja Logging Test API on http://127.0.0.1:8000")
    print("📊 Test endpoints:")
    print("  GET  /           - Root with logging")
    print("  GET  /test/slow  - Slow endpoint (performance alert)")
    print("  GET  /health     - Health check (minimal logging)")
    print("  GET  /docs       - API documentation")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
