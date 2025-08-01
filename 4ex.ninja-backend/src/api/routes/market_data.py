"""
Market Data API endpoints using repository pattern.

This module demonstrates market data API endpoints that use the repository pattern
for clean data access and dependency injection.

Note: Since the actual MarketData entity structure is complex, this API provides
a simplified interface that demonstrates the repository pattern usage.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...infrastructure.configuration.repository_config import RepositoryServiceProvider
from ..dependencies.repository_provider import get_repository_provider

router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Dict[str, Any]])
async def get_market_data(
    limit: int = Query(
        100, ge=1, le=5000, description="Number of data points to retrieve"
    ),
    offset: int = Query(0, ge=0, description="Number of data points to skip"),
    instrument: Optional[str] = Query(
        None, description="Instrument filter (e.g., EUR_USD)"
    ),
    granularity: Optional[str] = Query(
        None, description="Granularity filter (e.g., H4, D)"
    ),
    since: Optional[datetime] = Query(None, description="Get data after this time"),
    until: Optional[datetime] = Query(None, description="Get data before this time"),
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> List[Dict[str, Any]]:
    """
    Get market data with optional filtering.

    This endpoint demonstrates the repository pattern usage for market data access.
    """
    try:
        logger.info(
            f"Fetching market data with filters: instrument={instrument}, granularity={granularity}"
        )

        # Get repository from DI container
        market_data_repository = await repository_provider.get_market_data_repository()

        # Build filter criteria
        criteria = {}
        if instrument:
            criteria["instrument"] = instrument
        if granularity:
            criteria["granularity"] = granularity

        # Add date range filter
        if since or until:
            date_filter = {}
            if since:
                date_filter["$gte"] = since
            if until:
                date_filter["$lte"] = until
            criteria["last_updated"] = date_filter

        # Use repository to fetch data
        if criteria:
            market_data = await market_data_repository.find_by_criteria(
                criteria, limit=limit, offset=offset
            )
        else:
            market_data = await market_data_repository.get_all(
                limit=limit, offset=offset
            )

        # Convert to response format
        result = []
        for data in market_data:
            # MarketData contains a list of candles, so we'll return summary info
            latest_candle = data.candles[-1] if data.candles else None
            if latest_candle:
                result.append(
                    {
                        "instrument": data.instrument,
                        "granularity": data.granularity.value,
                        "last_updated": data.last_updated.isoformat(),
                        "source": data.source,
                        "candle_count": len(data.candles),
                        "latest_candle": {
                            "time": latest_candle.time.isoformat(),
                            "open": float(latest_candle.open),
                            "high": float(latest_candle.high),
                            "low": float(latest_candle.low),
                            "close": float(latest_candle.close),
                            "volume": latest_candle.volume,
                            "complete": latest_candle.complete,
                        },
                    }
                )

        logger.info(f"Successfully retrieved {len(result)} market data points")
        return result

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/instruments/{instrument}")
async def get_market_data_by_instrument(
    instrument: str,
    granularity: Optional[str] = Query(None, description="Granularity filter"),
    limit: int = Query(100, ge=1, le=5000),
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> List[Dict[str, Any]]:
    """
    Get market data for a specific instrument.
    """
    try:
        logger.info(f"Fetching market data for instrument: {instrument}")

        # Get repository from DI container
        market_data_repository = await repository_provider.get_market_data_repository()

        # Build criteria
        criteria = {"instrument": instrument}
        if granularity:
            criteria["granularity"] = granularity

        # Fetch market data by instrument
        market_data = await market_data_repository.find_by_criteria(
            criteria, limit=limit
        )

        # Convert to response format
        result = []
        for data in market_data:
            latest_candle = data.candles[-1] if data.candles else None
            if latest_candle:
                result.append(
                    {
                        "instrument": data.instrument,
                        "granularity": data.granularity.value,
                        "last_updated": data.last_updated.isoformat(),
                        "source": data.source,
                        "candle_count": len(data.candles),
                        "latest_candle": {
                            "time": latest_candle.time.isoformat(),
                            "open": float(latest_candle.open),
                            "high": float(latest_candle.high),
                            "low": float(latest_candle.low),
                            "close": float(latest_candle.close),
                            "volume": latest_candle.volume,
                        },
                    }
                )

        logger.info(
            f"Successfully retrieved {len(result)} market data points for instrument {instrument}"
        )
        return result

    except Exception as e:
        logger.error(f"Error fetching market data for instrument {instrument}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/latest/{instrument}/{granularity}")
async def get_latest_market_data(
    instrument: str,
    granularity: str,
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> Dict[str, Any]:
    """
    Get the latest market data for a specific instrument and granularity.
    """
    try:
        logger.info(f"Fetching latest market data for {instrument} {granularity}")

        # Get repository from DI container
        market_data_repository = await repository_provider.get_market_data_repository()

        # Get latest data using repository method
        criteria = {"instrument": instrument, "granularity": granularity}
        market_data = await market_data_repository.find_by_criteria(
            criteria, limit=1, offset=0
        )

        if not market_data:
            raise HTTPException(
                status_code=404,
                detail=f"No market data found for {instrument} {granularity}",
            )

        data = market_data[0]
        latest_candle = data.candles[-1] if data.candles else None

        if not latest_candle:
            raise HTTPException(
                status_code=404,
                detail=f"No candle data found for {instrument} {granularity}",
            )

        # Convert to response format
        result = {
            "instrument": data.instrument,
            "granularity": data.granularity.value,
            "last_updated": data.last_updated.isoformat(),
            "source": data.source,
            "candle_count": len(data.candles),
            "latest_candle": {
                "time": latest_candle.time.isoformat(),
                "open": float(latest_candle.open),
                "high": float(latest_candle.high),
                "low": float(latest_candle.low),
                "close": float(latest_candle.close),
                "volume": latest_candle.volume,
                "complete": latest_candle.complete,
            },
        }

        logger.info(
            f"Successfully retrieved latest market data for {instrument} {granularity}"
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching latest market data for {instrument} {granularity}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
