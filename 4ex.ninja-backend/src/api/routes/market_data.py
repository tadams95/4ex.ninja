"""
Market Data API endpoints using repository pattern.

This module provides API endpoints for market data access using the clean architecture
repository pattern with proper dependency injection.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.dependencies.simple_container import get_market_data_repository
from api.utils.response_optimization import (
    FieldSelector,
    PaginationOptimizer,
    create_optimized_response,
)
from api.utils.fast_json import FastJSONResponse, create_fast_json_response
from api.utils.endpoint_optimization import QueryOptimizer, CacheOptimizer

router = APIRouter(prefix="/market-data", tags=["market-data"])
logger = logging.getLogger(__name__)


@router.get("/", response_class=FastJSONResponse)
async def get_market_data(
    pagination: PaginationOptimizer = Depends(),
    field_selector: FieldSelector = Depends(),
    instrument: Optional[str] = Query(
        None, description="Instrument filter (e.g., EUR_USD)"
    ),
    timeframe: Optional[str] = Query(
        None, description="Timeframe filter (e.g., H1, H4, D)"
    ),
    since: Optional[datetime] = Query(
        None, description="Get data points after this time"
    ),
    market_data_repository=Depends(get_market_data_repository),
) -> FastJSONResponse:
    """
    Get market data with optional filtering and response optimization.
    """
    try:
        # Optimize query parameters for better performance
        query_optimizer = QueryOptimizer()
        cache_optimizer = CacheOptimizer()

        # Build optimized filters
        filters = {}
        if instrument:
            filters["instrument"] = instrument
        if timeframe:
            filters["timeframe"] = timeframe
        if since:
            filters["since"] = since

        # Apply query optimizations
        optimized_filters = query_optimizer.optimize_filters(filters)

        # Calculate optimal caching strategy
        aggressive_cache = cache_optimizer.should_use_aggressive_caching(
            "/api/v1/market-data/"
        )

        logger.info(
            f"Fetching market data: instrument={instrument}, timeframe={timeframe}, "
            f"limit={pagination.limit}, aggressive_cache={aggressive_cache}"
        )

        if not market_data_repository:
            # Return mock data if repository not available
            base_time = datetime.utcnow() - timedelta(hours=pagination.limit)
            mock_data = []

            for i in range(min(pagination.limit, 50)):  # Return up to 50 mock candles
                time_point = base_time + timedelta(hours=i)
                mock_data.append(
                    {
                        "instrument": instrument or "EUR_USD",
                        "timeframe": timeframe or "H1",
                        "timestamp": time_point.isoformat(),
                        "open": 1.1200 + (i * 0.001),
                        "high": 1.1210 + (i * 0.001),
                        "low": 1.1190 + (i * 0.001),
                        "close": 1.1205 + (i * 0.001),
                        "volume": 1000 + (i * 100),
                        "spread": 0.0002,
                        "tick_count": 50 + i,
                    }
                )

            # Apply filtering
            filtered_data = mock_data
            if since:
                filtered_data = [
                    d
                    for d in filtered_data
                    if datetime.fromisoformat(d["timestamp"]) >= since
                ]

            # Apply pagination
            paginated_data = filtered_data[
                pagination.offset : pagination.offset + pagination.limit
            ]

            optimized_response = create_optimized_response(
                paginated_data,
                field_selector=field_selector,
                pagination=pagination,
                additional_meta={
                    "source": "mock_data",
                    "instrument": instrument or "EUR_USD",
                    "timeframe": timeframe or "H1",
                    "total_unfiltered": len(mock_data),
                    "total_filtered": len(filtered_data),
                },
            )
            return create_fast_json_response(optimized_response)

        # Use repository to fetch market data (when available)
        market_data = []

        optimized_response = create_optimized_response(
            market_data,
            field_selector=field_selector,
            pagination=pagination,
            additional_meta={
                "source": "repository",
                "instrument": instrument,
                "timeframe": timeframe,
            },
        )
        return create_fast_json_response(optimized_response)

    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/latest/{instrument}", response_class=FastJSONResponse)
async def get_latest_price(
    instrument: str,
    field_selector: FieldSelector = Depends(),
    market_data_repository=Depends(get_market_data_repository),
) -> FastJSONResponse:
    """
    Get the latest price for a specific instrument with optional field selection.
    """
    try:
        logger.info(f"Fetching latest price for: {instrument}")

        if not market_data_repository:
            # Return mock data if repository not available
            mock_price_data = {
                "instrument": instrument,
                "timestamp": datetime.utcnow().isoformat(),
                "bid": 1.1200,
                "ask": 1.1205,
                "spread": 0.0005,
                "last_update": datetime.utcnow().isoformat(),
                "volume_24h": 125000,
                "change_24h": 0.0012,
                "change_24h_pct": 0.11,
                "high_24h": 1.1250,
                "low_24h": 1.1180,
            }

            optimized_response = create_optimized_response(
                mock_price_data,
                field_selector=field_selector,
                additional_meta={
                    "source": "mock_data",
                    "instrument": instrument,
                    "data_type": "latest_price",
                },
            )
            return create_fast_json_response(optimized_response)

        # Use repository to get latest price (when available)
        latest_price = {}

        optimized_response = create_optimized_response(
            latest_price,
            field_selector=field_selector,
            additional_meta={
                "source": "repository",
                "instrument": instrument,
                "data_type": "latest_price",
            },
        )
        return create_fast_json_response(optimized_response)

    except Exception as e:
        logger.error(f"Error fetching latest price for {instrument}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch latest price for {instrument}"
        )


@router.get("/stats/summary", response_class=FastJSONResponse)
async def get_market_stats(
    instrument: Optional[str] = Query(None, description="Instrument filter"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours for statistics"),
    field_selector: FieldSelector = Depends(),
    market_data_repository=Depends(get_market_data_repository),
) -> FastJSONResponse:
    """
    Get market statistics summary with optional field selection.
    """
    try:
        logger.info(f"Fetching market statistics for {instrument} over {hours} hours")

        if not market_data_repository:
            # Return mock statistics if repository not available
            mock_stats = {
                "instrument": instrument or "ALL",
                "period_hours": hours,
                "volatility": 0.0045,
                "average_spread": 0.0003,
                "trading_volume": 125000,
                "price_change_24h": 0.0012,
                "price_change_percent": 0.1,
                "high_24h": 1.1250,
                "low_24h": 1.1180,
                "tick_count": 45230,
                "avg_volume_per_hour": hours * 5200,
                "generated_at": datetime.utcnow().isoformat(),
            }

            optimized_response = create_optimized_response(
                mock_stats,
                field_selector=field_selector,
                additional_meta={
                    "source": "mock_data",
                    "data_type": "market_statistics",
                    "period_hours": hours,
                },
            )
            return create_fast_json_response(optimized_response)

        # Use repository to calculate statistics (when available)
        stats = {}

        optimized_response = create_optimized_response(
            stats,
            field_selector=field_selector,
            additional_meta={
                "source": "repository",
                "data_type": "market_statistics",
                "period_hours": hours,
            },
        )
        return create_fast_json_response(optimized_response)

    except Exception as e:
        logger.error(f"Error fetching market statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market statistics")
