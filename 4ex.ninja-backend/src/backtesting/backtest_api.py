"""
Backtest API - REST endpoints for remote backtesting access
Simple, production-ready API integration with existing infrastructure
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import json
import os
from pathlib import Path

from .universal_backtesting_engine import UniversalBacktestingEngine
from .strategies.strategy_registry import strategy_registry
from .models import BacktestResult, Trade

# API Router for backtesting endpoints
backtest_router = APIRouter(prefix="/backtest", tags=["backtesting"])

# Global storage for backtest results (simple file-based storage)
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# Request/Response Models
class BacktestRequest(BaseModel):
    strategy_name: str
    strategy_config: Dict[str, Any]
    pair: str
    timeframe: str
    start_date: str  # ISO format
    end_date: str  # ISO format


class BacktestResponse(BaseModel):
    backtest_id: str
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None


class StrategyInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class BacktestStatus(BaseModel):
    backtest_id: str
    status: str
    progress: float
    results: Optional[Dict[str, Any]] = None


# Initialize components
engine = UniversalBacktestingEngine()


@backtest_router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run a backtest with specified strategy and parameters"""

    try:
        # Validate strategy exists
        available_strategies = strategy_registry.list_strategies()
        if request.strategy_name not in available_strategies:
            raise HTTPException(
                status_code=400, detail=f"Unknown strategy: {request.strategy_name}"
            )

        # Generate unique backtest ID
        backtest_id = str(uuid.uuid4())

        # Parse dates
        start_date = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))

        # Create strategy instance
        strategy = strategy_registry.get_strategy(
            request.strategy_name, request.strategy_config
        )

        # Run backtest (await the async method)
        results = await engine.run_backtest(
            strategy=strategy,
            pair=request.pair,
            timeframe=request.timeframe,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert results to serializable format
        results_dict = {
            "strategy_name": results.strategy_name,
            "total_trades": len(results.trades),
            "total_pnl": sum(trade.pnl for trade in results.trades),
            "win_rate": (
                len([t for t in results.trades if t.pnl > 0]) / len(results.trades)
                if results.trades
                else 0
            ),
            "trades": [
                {
                    "pair": trade.pair,
                    "direction": trade.direction,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "entry_time": (
                        trade.entry_time.isoformat() if trade.entry_time else None
                    ),
                    "exit_time": (
                        trade.exit_time.isoformat() if trade.exit_time else None
                    ),
                    "pnl": trade.pnl,
                    "size": trade.size,
                }
                for trade in results.trades
            ],
            "performance_metrics": (
                results.performance_metrics
                if hasattr(results, "performance_metrics")
                else {}
            ),
        }

        # Store results
        result_file = RESULTS_DIR / f"{backtest_id}.json"
        with open(result_file, "w") as f:
            json.dump(results_dict, f, indent=2)

        return BacktestResponse(
            backtest_id=backtest_id,
            status="completed",
            message="Backtest completed successfully",
            results=results_dict,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@backtest_router.get("/strategies", response_model=List[StrategyInfo])
async def get_available_strategies():
    """Get list of available strategies"""

    try:
        strategies = []
        for strategy_name in strategy_registry.list_strategies():
            try:
                info = strategy_registry.get_strategy_info(strategy_name)
                strategies.append(
                    StrategyInfo(
                        name=strategy_name,
                        description=info.get("description", ""),
                        parameters=info.get("default_config", {}),
                    )
                )
            except Exception as e:
                # Skip strategies that can't be loaded
                continue
        return strategies

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get strategies: {str(e)}"
        )


@backtest_router.get("/results/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest_results(backtest_id: str):
    """Retrieve stored backtest results"""

    try:
        result_file = RESULTS_DIR / f"{backtest_id}.json"

        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Backtest results not found")

        with open(result_file, "r") as f:
            results = json.load(f)

        return results

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backtest results not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve results: {str(e)}"
        )


@backtest_router.get("/results", response_model=List[Dict[str, Any]])
async def list_backtest_results():
    """List all stored backtest results"""

    try:
        results = []
        for result_file in RESULTS_DIR.glob("*.json"):
            try:
                with open(result_file, "r") as f:
                    data = json.load(f)
                results.append(
                    {
                        "backtest_id": result_file.stem,
                        "strategy_name": data.get("strategy_name", "unknown"),
                        "total_trades": data.get("total_trades", 0),
                        "total_pnl": data.get("total_pnl", 0),
                        "created_at": result_file.stat().st_mtime,
                    }
                )
            except Exception:
                continue  # Skip corrupted files

        # Sort by creation time (newest first)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list results: {str(e)}")


@backtest_router.delete("/results/{backtest_id}")
async def delete_backtest_results(backtest_id: str):
    """Delete stored backtest results"""

    try:
        result_file = RESULTS_DIR / f"{backtest_id}.json"

        if not result_file.exists():
            raise HTTPException(status_code=404, detail="Backtest results not found")

        result_file.unlink()
        return {"message": "Backtest results deleted successfully"}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backtest results not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete results: {str(e)}"
        )


# Health check endpoint
@backtest_router.get("/health")
async def health_check():
    """Health check for backtesting API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "available_strategies": len(strategy_registry.list_strategies()),
        "engine_status": "operational",
    }
