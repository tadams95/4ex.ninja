"""
API Routes Package

FastAPI route definitions for different resource endpoints.
"""

from .signals import router as signals_router
from .market_data import router as market_data_router
from .performance import router as performance_router

__all__ = ["signals_router", "market_data_router", "performance_router"]
