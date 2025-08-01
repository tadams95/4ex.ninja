"""
Signals API endpoints using repository pattern.

This module demonstrates how to implement API endpoints using the new repository pattern
for clean separation of concerns and dependency injection.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...core.entities.signal import Signal, SignalType, SignalStatus
from ...core.interfaces.signal_repository import ISignalRepository
from ...infrastructure.configuration.repository_config import RepositoryServiceProvider
from ..dependencies.repository_provider import get_repository_provider

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Dict[str, Any]])
async def get_signals(
    limit: int = Query(50, ge=1, le=1000, description="Number of signals to retrieve"),
    offset: int = Query(0, ge=0, description="Number of signals to skip"),
    pair: Optional[str] = Query(
        None, description="Currency pair filter (e.g., EUR_USD)"
    ),
    signal_type: Optional[SignalType] = Query(None, description="Signal type filter"),
    status: Optional[SignalStatus] = Query(None, description="Signal status filter"),
    strategy_name: Optional[str] = Query(None, description="Strategy name filter"),
    timeframe: Optional[str] = Query(
        None, description="Timeframe filter (e.g., H4, D)"
    ),
    since: Optional[datetime] = Query(
        None, description="Get signals created after this time"
    ),
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> List[Dict[str, Any]]:
    """
    Get signals with optional filtering.

    This endpoint demonstrates the repository pattern usage for data access.
    """
    try:
        logger.info(
            f"Fetching signals with filters: pair={pair}, type={signal_type}, status={status}"
        )

        # Get repository from DI container
        signal_repository = await repository_provider.get_signal_repository()

        # Build filter criteria
        criteria = {}
        if pair:
            criteria["pair"] = pair
        if signal_type:
            criteria["signal_type"] = signal_type.value
        if status:
            criteria["status"] = status.value
        if strategy_name:
            criteria["strategy_name"] = strategy_name
        if timeframe:
            criteria["timeframe"] = timeframe
        if since:
            criteria["created_at"] = {"$gte": since}

        # Use repository to fetch data
        if criteria:
            signals = await signal_repository.find_by_criteria(
                criteria, limit=limit, offset=offset
            )
        else:
            signals = await signal_repository.get_all(limit=limit, offset=offset)

        # Convert to response format
        result = []
        for signal in signals:
            result.append(
                {
                    "signal_id": signal.signal_id,
                    "strategy_name": signal.strategy_name,
                    "pair": signal.pair,
                    "timeframe": signal.timeframe,
                    "signal_type": signal.signal_type.value,
                    "crossover_type": signal.crossover_type.value,
                    "entry_price": float(signal.entry_price),
                    "current_price": float(signal.current_price),
                    "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
                    "take_profit": (
                        float(signal.take_profit) if signal.take_profit else None
                    ),
                    "position_size": (
                        float(signal.position_size) if signal.position_size else None
                    ),
                    "fast_ma": signal.fast_ma,
                    "slow_ma": signal.slow_ma,
                    "atr_value": float(signal.atr_value) if signal.atr_value else None,
                    "status": signal.status.value,
                    "timestamp": signal.timestamp.isoformat(),
                    "confidence_score": signal.confidence_score,
                    "notes": signal.notes,
                    "created_at": signal.created_at.isoformat(),
                    "updated_at": signal.updated_at.isoformat(),
                }
            )

        logger.info(f"Successfully retrieved {len(result)} signals")
        return result

    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{signal_id}", response_model=Dict[str, Any])
async def get_signal(
    signal_id: str,
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> Dict[str, Any]:
    """
    Get a specific signal by ID.
    """
    try:
        logger.info(f"Fetching signal: {signal_id}")

        # Get repository from DI container
        signal_repository = await repository_provider.get_signal_repository()

        # Fetch signal
        signal = await signal_repository.get_by_id(signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        # Convert to response format
        result = {
            "signal_id": signal.signal_id,
            "strategy_name": signal.strategy_name,
            "pair": signal.pair,
            "timeframe": signal.timeframe,
            "signal_type": signal.signal_type.value,
            "crossover_type": signal.crossover_type.value,
            "entry_price": float(signal.entry_price),
            "current_price": float(signal.current_price),
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "take_profit": float(signal.take_profit) if signal.take_profit else None,
            "position_size": (
                float(signal.position_size) if signal.position_size else None
            ),
            "fast_ma": signal.fast_ma,
            "slow_ma": signal.slow_ma,
            "atr_value": float(signal.atr_value) if signal.atr_value else None,
            "status": signal.status.value,
            "timestamp": signal.timestamp.isoformat(),
            "confidence_score": signal.confidence_score,
            "notes": signal.notes,
            "created_at": signal.created_at.isoformat(),
            "updated_at": signal.updated_at.isoformat(),
        }

        logger.info(f"Successfully retrieved signal: {signal_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/strategy/{strategy_name}")
async def get_signals_by_strategy(
    strategy_name: str,
    limit: int = Query(50, ge=1, le=1000),
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> List[Dict[str, Any]]:
    """
    Get all signals for a specific strategy.
    """
    try:
        logger.info(f"Fetching signals for strategy: {strategy_name}")

        # Get repository from DI container
        signal_repository = await repository_provider.get_signal_repository()

        # Fetch signals by strategy - using find_by_criteria since no get_by_strategy_id method
        criteria = {"strategy_name": strategy_name}
        signals = await signal_repository.find_by_criteria(criteria, limit=limit)

        # Convert to response format
        result = []
        for signal in signals:
            result.append(
                {
                    "signal_id": signal.signal_id,
                    "strategy_name": signal.strategy_name,
                    "pair": signal.pair,
                    "timeframe": signal.timeframe,
                    "signal_type": signal.signal_type.value,
                    "crossover_type": signal.crossover_type.value,
                    "entry_price": float(signal.entry_price),
                    "current_price": float(signal.current_price),
                    "status": signal.status.value,
                    "timestamp": signal.timestamp.isoformat(),
                    "notes": signal.notes,
                }
            )

        logger.info(
            f"Successfully retrieved {len(result)} signals for strategy {strategy_name}"
        )
        return result

    except Exception as e:
        logger.error(f"Error fetching signals for strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/performance/{strategy_name}")
async def get_strategy_performance(
    strategy_name: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    repository_provider: RepositoryServiceProvider = Depends(get_repository_provider),
) -> Dict[str, Any]:
    """
    Get performance metrics for a strategy using repository pattern.
    """
    try:
        logger.info(f"Calculating performance for strategy: {strategy_name}")

        # Get repository from DI container
        signal_repository = await repository_provider.get_signal_repository()

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get signals for the strategy within date range
        criteria = {
            "strategy_name": strategy_name,
            "created_at": {"$gte": start_date, "$lte": end_date},
        }
        signals = await signal_repository.find_by_criteria(criteria)

        # Calculate basic performance metrics
        total_signals = len(signals)
        profitable_signals = sum(1 for s in signals if s.is_profitable())
        total_pnl = sum(float(s.get_pnl()) for s in signals)

        performance = {
            "strategy_name": strategy_name,
            "period_days": days,
            "total_signals": total_signals,
            "profitable_signals": profitable_signals,
            "win_rate": profitable_signals / total_signals if total_signals > 0 else 0,
            "total_pnl": total_pnl,
            "average_pnl": total_pnl / total_signals if total_signals > 0 else 0,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        logger.info(f"Successfully calculated performance for strategy {strategy_name}")
        return performance

    except Exception as e:
        logger.error(f"Error calculating performance for strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
