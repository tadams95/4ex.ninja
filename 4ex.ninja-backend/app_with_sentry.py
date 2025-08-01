"""
FastAPI Sentry Integration Example

Shows how to integrate Sentry monitoring with your FastAPI application.
"""

from fastapi import FastAPI, HTTPException
import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from infrastructure.monitoring.error_tracking import initialize_error_tracking, error_tracker  # type: ignore
    from infrastructure.monitoring.performance import performance_monitor  # type: ignore
    from api.health import router as health_router  # type: ignore

    MONITORING_AVAILABLE = True
except ImportError:
    print("Warning: Monitoring modules not available")
    MONITORING_AVAILABLE = False
    initialize_error_tracking = None
    error_tracker = None
    performance_monitor = None
    health_router = None

# Initialize Sentry with your DSN
SENTRY_DSN = "https://255fd05fd3c0d2e90c377b42829e8e5d@o4509766501990400.ingest.us.sentry.io/4509766604029952"


def create_app() -> FastAPI:
    """Create FastAPI app with Sentry monitoring."""

    # Initialize Sentry first
    if initialize_error_tracking is not None:
        initialize_error_tracking(SENTRY_DSN, "development")

    app = FastAPI(
        title="4ex.ninja Trading Platform",
        description="Forex trading signals platform with comprehensive monitoring",
        version="1.0.0",
    )

    # Include health monitoring routes if available
    if health_router is not None:
        app.include_router(health_router)

    @app.get("/")
    async def root():
        """Root endpoint with performance monitoring."""
        if performance_monitor is not None:
            with performance_monitor.time_sync("root_endpoint"):
                return {
                    "message": "4ex.ninja Trading Platform",
                    "status": "running",
                    "monitoring": "enabled",
                }
        else:
            return {
                "message": "4ex.ninja Trading Platform",
                "status": "running",
                "monitoring": "disabled",
            }

    @app.get("/test-error")
    async def test_error():
        """Test endpoint to generate an error for Sentry."""
        try:
            # Simulate an error
            raise ValueError("This is a test error for Sentry monitoring!")
        except Exception as e:
            # Capture the error with context if available
            event_id = None
            if error_tracker is not None:
                event_id = error_tracker.capture_api_error(
                    e, "/test-error", "GET", "test_user"
                )
            raise HTTPException(
                status_code=500,
                detail=f"Test error captured in Sentry with ID: {event_id}",
            )

    @app.get("/test-performance")
    async def test_performance():
        """Test endpoint for performance monitoring."""
        import time
        import random

        # Simulate some work with random duration
        if performance_monitor is not None:
            async with performance_monitor.time_async(
                "test_work", {"type": "simulation"}
            ):
                await asyncio.sleep(random.uniform(0.1, 0.5))

            # Track the operation
            performance_monitor.increment_counter(
                "test_operations", tags={"endpoint": "/test-performance"}
            )
        else:
            await asyncio.sleep(random.uniform(0.1, 0.5))

        return {"message": "Performance test completed"}

    return app


# Create the app
app = create_app()

if __name__ == "__main__":
    import uvicorn
    import asyncio

    print("🚀 Starting 4ex.ninja with Sentry monitoring...")
    print("📊 Health endpoints available at:")
    print("   - http://localhost:8000/health/")
    print("   - http://localhost:8000/health/detailed")
    print("   - http://localhost:8000/health/performance")
    print("🔥 Test error endpoint: http://localhost:8000/test-error")
    print("⚡ Test performance endpoint: http://localhost:8000/test-performance")

    uvicorn.run(app, host="0.0.0.0", port=8000)
