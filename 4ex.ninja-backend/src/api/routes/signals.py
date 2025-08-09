"""
Signals API endpoints using repository pattern.

This module provides API endpoints for signal management using the clean architecture
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

from api.dependencies.simple_container import get_signal_repository

router = APIRouter(prefix="/signals", tags=["signals"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Dict[str, Any]])
async def get_signals(
    limit: int = Query(50, ge=1, le=1000, description="Number of signals to retrieve"),
    offset: int = Query(0, ge=0, description="Number of signals to skip"),
    pair: Optional[str] = Query(
        None, description="Currency pair filter (e.g., EUR_USD)"
    ),
    since: Optional[datetime] = Query(
        None, description="Get signals created after this time"
    ),
    signal_repository=Depends(get_signal_repository),
) -> List[Dict[str, Any]]:
    """
    Get signals with optional filtering.

    This endpoint demonstrates the repository pattern usage for data access.
    """
    try:
        logger.info(
            f"Fetching signals with filters: pair={pair}, limit={limit}, offset={offset}"
        )

        if not signal_repository:
            # Return mock data if repository not available
            return [
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
                },
            ]

        # Use repository to fetch signals (when available)
        # This would use the actual repository methods when implemented
        signals = []

        return signals

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
