"""
FastAPI Application Factory

Creates and configures the FastAPI application with proper dependency injection,
middleware, and route registration.
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import os
import sys
from typing import AsyncGenerator

# Add src to path for imports
sys.path.append(os.path.dirname(__file__))

from api.health import router as health_router
from api.routes.signals import router as signals_router
from api.routes.market_data import router as market_data_router
from api.routes.performance import router as performance_router
from api.routes.auth import router as auth_router
from api.middleware.error_handler import ErrorHandlerMiddleware
from api.middleware.logging_middleware import LoggingMiddleware
from api.middleware.http_cache import HTTPCacheMiddleware
from api.middleware.response_optimization import ResponseOptimizationMiddleware
from api.middleware.rate_limiting import RateLimitMiddleware
from api.middleware.security_headers import create_security_middleware_stack
from api.dependencies.simple_container import get_container
from infrastructure.monitoring.error_tracking import initialize_error_tracking
from services.cache_service import CacheServiceFactory


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting 4ex.ninja Trading Platform API")

    # Initialize error tracking if Sentry DSN is available
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")

    if sentry_dsn:
        try:
            initialize_error_tracking(sentry_dsn, environment)
            logger.info("Sentry error tracking initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")

    # Initialize dependency container
    container = get_container()
    logger.info("Dependency container initialized")

    # Initialize and warm cache
    try:
        cache_service = await CacheServiceFactory.create_crossover_cache_service()
        warm_count = await cache_service.warm_cache()
        logger.info(f"Cache warming completed. Warmed {warm_count} entries")
    except Exception as e:
        logger.warning(f"Cache warming failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down 4ex.ninja Trading Platform API")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """

    app = FastAPI(
        title="4ex.ninja Trading Platform API",
        description="Professional forex trading signals platform with real-time market analysis",
        version="1.0.0",
        docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
        lifespan=lifespan,
    )

    # Configure CORS
    origins = [
        "http://localhost:3000",  # Frontend development
        "http://localhost:3001",  # Alternative frontend port
        "https://4ex.ninja",  # Production domain
        "https://www.4ex.ninja",  # Production www domain
    ]

    # Add environment-specific origins
    if os.getenv("ENVIRONMENT") == "development":
        origins.extend(
            [
                "http://127.0.0.1:3000",
                "http://0.0.0.0:3000",
            ]
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Add trusted host middleware for production
    if os.getenv("ENVIRONMENT") == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["4ex.ninja", "www.4ex.ninja", "api.4ex.ninja"],
        )

    # Add custom middleware (order matters - last added is executed first)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        ResponseOptimizationMiddleware,
        enable_keepalive=True,
        max_response_size_mb=10,
        enable_timing_headers=True,
    )
    app.add_middleware(
        HTTPCacheMiddleware,
        enable_etags=True,
        enable_conditional_requests=True,
        excluded_paths=[
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/cache/invalidate",
        ],
    )

    # Add GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add comprehensive security middleware stack
    create_security_middleware_stack(app)

    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(signals_router, prefix="/api/v1")
    app.include_router(market_data_router, prefix="/api/v1")
    app.include_router(performance_router, prefix="/api/v1")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "4ex.ninja Trading Platform API",
            "version": "1.0.0",
            "status": "operational",
            "docs": (
                "/docs"
                if os.getenv("ENVIRONMENT") != "production"
                else "Contact support for API documentation"
            ),
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info",
    )
