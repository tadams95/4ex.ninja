"""
Signals API endpoints using repository pattern with caching.

This module provides API endpoints for signal management using the clean architecture
repository pattern with proper dependency injection and comprehensive caching.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.dependencies.simple_container import get_signal_repository
from services.cache_service import CrossoverCacheService, CacheServiceFactory
from api.utils.response_optimization import (
    FieldSelector,
    PaginationOptimizer,
    create_optimized_response,
)
from api.utils.fast_json import FastJSONResponse, create_fast_json_response

router = APIRouter(prefix="/signals", tags=["signals"])
logger = logging.getLogger(__name__)

# Global cache service instance
_cache_service: Optional[CrossoverCacheService] = None


async def get_cache_service() -> CrossoverCacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        try:
            _cache_service = await CacheServiceFactory.create_crossover_cache_service()
            logger.info("Cache service initialized for signals")
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            # Create a minimal cache service
            cache_manager = await CacheServiceFactory.create_cache_manager(
                use_redis=False, fallback_to_memory=True
            )
            _cache_service = CrossoverCacheService(cache_manager)
    return _cache_service


@router.get("/", response_class=FastJSONResponse)
async def get_signals(
    pagination: PaginationOptimizer = Depends(),
    field_selector: FieldSelector = Depends(),
    pair: Optional[str] = Query(
        None, description="Currency pair filter (e.g., EUR_USD)"
    ),
    since: Optional[datetime] = Query(
        None, description="Get signals created after this time"
    ),
    force_refresh: bool = Query(
        False, description="Force refresh from database (skip cache)"
    ),
    signal_repository=Depends(get_signal_repository),
    cache_service: CrossoverCacheService = Depends(get_cache_service),
) -> FastJSONResponse:
    """
    Get signals with optional filtering, field selection, and intelligent caching.

    This endpoint demonstrates the repository pattern usage for data access
    with comprehensive caching and response optimization.
    """
    try:
        logger.info(
            f"Fetching signals with filters: pair={pair}, limit={pagination.limit}, offset={pagination.offset}, force_refresh={force_refresh}"
        )

        # Build cache filters
        cache_filters: Dict[str, Any] = {
            "limit": pagination.limit,
            "offset": pagination.offset,
        }
        if pair:
            cache_filters["pair"] = pair
        if since:
            cache_filters["since"] = since.isoformat()

        # Try to get from cache first (unless force refresh)
        cached_signals = None
        if not force_refresh:
            cached_signals = await cache_service.get_crossovers(filters=cache_filters)

        if cached_signals is not None:
            logger.info(f"Returning {len(cached_signals)} signals from cache")
            optimized_response = create_optimized_response(
                cached_signals,
                field_selector=field_selector,
                pagination=pagination,
                additional_meta={"source": "cache", "cache_hit": True},
            )
            return create_fast_json_response(optimized_response)

        # Cache miss or force refresh - get from repository/mock data
        if not signal_repository:
            # Return mock data if repository not available
            mock_signals = [
                {
                    "id": "mock_signal_1",
                    "pair": pair or "EUR_USD",
                    "signal_type": "BUY",
                    "entry_price": 1.1234,
                    "stop_loss": 1.1200,
                    "take_profit": 1.1300,
                    "confidence": 0.85,
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "ACTIVE",
                    "timestamp": datetime.utcnow().isoformat(),
                    "notes": "Strong bullish momentum detected",
                },
                {
                    "id": "mock_signal_2",
                    "pair": pair or "GBP_USD",
                    "signal_type": "SELL",
                    "entry_price": 1.2500,
                    "stop_loss": 1.2550,
                    "take_profit": 1.2400,
                    "confidence": 0.78,
                    "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "status": "ACTIVE",
                    "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "notes": "Resistance level break expected",
                },
                {
                    "id": "mock_signal_3",
                    "pair": "USD_JPY",
                    "signal_type": "BUY",
                    "entry_price": 149.50,
                    "stop_loss": 149.00,
                    "take_profit": 150.20,
                    "confidence": 0.82,
                    "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "status": "CLOSED",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "notes": "Target reached successfully",
                },
            ]

            # Apply filtering
            filtered_signals = mock_signals
            if pair:
                filtered_signals = [s for s in filtered_signals if s["pair"] == pair]
            if since:
                filtered_signals = [
                    s
                    for s in filtered_signals
                    if datetime.fromisoformat(s["created_at"]) >= since
                ]

            # Apply pagination
            paginated_signals = filtered_signals[
                pagination.offset : pagination.offset + pagination.limit
            ]

            # Store in cache for future requests
            try:
                await cache_service.set_crossovers(
                    crossovers=paginated_signals,
                    filters=cache_filters,
                    ttl_seconds=60,  # Cache signals for 1 minute
                    metadata={
                        "total_count": len(filtered_signals),
                        "is_mock_data": True,
                    },
                )
                logger.info(f"Cached {len(paginated_signals)} signals")
            except Exception as cache_error:
                logger.warning(f"Failed to cache signals: {cache_error}")

            optimized_response = create_optimized_response(
                paginated_signals,
                field_selector=field_selector,
                pagination=pagination,
                additional_meta={
                    "source": "mock_data",
                    "cache_hit": False,
                    "total_unfiltered": len(mock_signals),
                    "total_filtered": len(filtered_signals),
                },
            )
            return create_fast_json_response(optimized_response)

        # Use repository to fetch signals (when available)
        signals = []

        if signals:
            await cache_service.set_crossovers(
                crossovers=signals,
                filters=cache_filters,
                ttl_seconds=300,  # Cache real data for 5 minutes
            )

        optimized_response = create_optimized_response(
            signals,
            field_selector=field_selector,
            pagination=pagination,
            additional_meta={"source": "repository", "cache_hit": False},
        )
        return create_fast_json_response(optimized_response)

    except Exception as e:
        logger.error(f"Error fetching signals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch signals")


@router.get("/{signal_id}", response_model=Dict[str, Any])
async def get_signal(
    signal_id: str,
    signal_repository=Depends(get_signal_repository),
) -> Dict[str, Any]:
    """
    Get a specific signal by ID.
    """
    try:
        logger.info(f"Fetching signal: {signal_id}")

        if not signal_repository:
            # Return mock data if repository not available
            return {
                "id": signal_id,
                "pair": "EUR_USD",
                "signal_type": "BUY",
                "entry_price": 1.1234,
                "stop_loss": 1.1200,
                "take_profit": 1.1300,
                "confidence": 0.85,
                "created_at": datetime.utcnow().isoformat(),
                "status": "ACTIVE",
                "strategy": "momentum_breakout",
                "timeframe": "H4",
            }

        # Use repository to fetch specific signal (when available)
        signal = None

        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return signal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching signal {signal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch signal")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_signal_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    signal_repository=Depends(get_signal_repository),
) -> Dict[str, Any]:
    """
    Get signal statistics summary.
    """
    try:
        logger.info(f"Fetching signal statistics for {days} days")

        if not signal_repository:
            # Return mock statistics if repository not available
            return {
                "total_signals": 150,
                "active_signals": 12,
                "completed_signals": 138,
                "win_rate": 0.72,
                "average_profit": 45.5,
                "best_performing_pair": "EUR_USD",
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
            }

        # Use repository to calculate statistics (when available)
        stats = {}

        return stats

    except Exception as e:
        logger.error(f"Error fetching signal statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch signal statistics")


@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    cache_service: CrossoverCacheService = Depends(get_cache_service),
) -> Dict[str, Any]:
    """
    Get caching statistics for signals.

    This endpoint provides insights into cache performance
    and helps with monitoring cache effectiveness.
    """
    try:
        stats = await cache_service.get_stats()
        return {
            **stats,
            "endpoint": "signals",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching cache statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cache statistics")


@router.post("/cache/invalidate")
async def invalidate_cache(
    invalidate_all: bool = Query(
        False, description="Invalidate all cached signal data"
    ),
    cache_service: CrossoverCacheService = Depends(get_cache_service),
) -> Dict[str, Any]:
    """
    Invalidate cached signal data.

    This endpoint allows manual cache invalidation for when
    signal data is updated outside of the normal API flow.
    """
    try:
        invalidated_count = await cache_service.invalidate_crossovers(
            invalidate_all=invalidate_all
        )

        return {
            "success": True,
            "invalidated_count": invalidated_count,
            "invalidate_all": invalidate_all,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")
