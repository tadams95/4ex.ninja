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

router = APIRouter(prefix="/market-data", tags=["market-data"])
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
    timeframe: Optional[str] = Query(
        None, description="Timeframe filter (e.g., H1, H4, D)"
    ),
    since: Optional[datetime] = Query(
        None, description="Get data points after this time"
    ),
    market_data_repository=Depends(get_market_data_repository),
) -> List[Dict[str, Any]]:
    """
    Get market data with optional filtering.
    """
    try:
        logger.info(
            f"Fetching market data: instrument={instrument}, timeframe={timeframe}, limit={limit}"
        )

        if not market_data_repository:
            # Return mock data if repository not available
            base_time = datetime.utcnow() - timedelta(hours=limit)
            mock_data = []

            for i in range(min(limit, 10)):  # Return up to 10 mock candles
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
                    }
                )

            return mock_data

        # Use repository to fetch market data (when available)
        market_data = []

        return market_data

    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/latest/{instrument}", response_model=Dict[str, Any])
async def get_latest_price(
    instrument: str,
    market_data_repository=Depends(get_market_data_repository),
) -> Dict[str, Any]:
    """
    Get the latest price for a specific instrument.
    """
    try:
        logger.info(f"Fetching latest price for: {instrument}")

        if not market_data_repository:
            # Return mock data if repository not available
            return {
                "instrument": instrument,
                "timestamp": datetime.utcnow().isoformat(),
                "bid": 1.1200,
                "ask": 1.1205,
                "spread": 0.0005,
                "last_update": datetime.utcnow().isoformat(),
            }

        # Use repository to fetch latest price (when available)
        latest_price = None

        if not latest_price:
            raise HTTPException(status_code=404, detail="Instrument not found")

        return latest_price

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest price for {instrument}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest price")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_market_stats(
    instrument: Optional[str] = Query(None, description="Instrument filter"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours for statistics"),
    market_data_repository=Depends(get_market_data_repository),
) -> Dict[str, Any]:
    """
    Get market statistics summary.
    """
    try:
        logger.info(f"Fetching market statistics for {instrument} over {hours} hours")

        if not market_data_repository:
            # Return mock statistics if repository not available
            return {
                "instrument": instrument or "ALL",
                "period_hours": hours,
                "volatility": 0.0045,
                "average_spread": 0.0003,
                "trading_volume": 125000,
                "price_change_24h": 0.0012,
                "price_change_percent": 0.1,
                "high_24h": 1.1250,
                "low_24h": 1.1180,
                "generated_at": datetime.utcnow().isoformat(),
            }

        # Use repository to calculate statistics (when available)
        stats = {}

        return stats

    except Exception as e:
        logger.error(f"Error fetching market statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market statistics")
