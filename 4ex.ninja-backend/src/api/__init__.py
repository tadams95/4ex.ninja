"""
API Package

FastAPI application components including routes, middleware, and dependencies.
"""

from .health import router as health_router

__all__ = ["health_router"]
