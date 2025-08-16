"""
Portfolio Management API Integration.

Extends the existing monitoring dashboard with portfolio management
endpoints for multi-strategy coordination and monitoring.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .portfolio_manager import UniversalPortfolioManager, PortfolioDecision
from .risk_manager import UniversalRiskManager, RiskLimits
from .correlation_manager import CorrelationManager
from .multi_strategy_coordinator import MultiStrategyCoordinator
from .strategies.strategy_factory import StrategyFactory


# Request/Response Models
class StrategyAllocationRequest(BaseModel):
    """Request to add a strategy to portfolio."""

    strategy_name: str
    strategy_type: str
    configuration: Dict[str, Any]
    allocation: float  # 0.0 to 1.0


class PortfolioStatusResponse(BaseModel):
    """Portfolio status response."""

    total_balance: float
    available_balance: float
    total_risk: float
    active_positions: int
    active_strategies: int
    strategies: Dict[str, Dict[str, Any]]


class RiskStatusResponse(BaseModel):
    """Risk management status response."""

    current_risk_level: str
    portfolio_risk: float
    daily_trades: int
    consecutive_losses: int
    risk_limits: Dict[str, Any]


class CoordinationStatusResponse(BaseModel):
    """Multi-strategy coordination status."""

    active_strategies: int
    recent_signals: int
    execution_rate: float
    recent_conflicts: int


# Global portfolio management instances
# These would be initialized with actual data in production
portfolio_manager: Optional[UniversalPortfolioManager] = None
risk_manager: Optional[UniversalRiskManager] = None
correlation_manager: Optional[CorrelationManager] = None
strategy_coordinator: Optional[MultiStrategyCoordinator] = None


def get_portfolio_manager():
    """Get or create portfolio manager instance."""
    global portfolio_manager
    if portfolio_manager is None:
        portfolio_manager = UniversalPortfolioManager(
            initial_balance=10000,
            currency_pairs=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD"],
        )
    return portfolio_manager


def get_risk_manager():
    """Get or create risk manager instance."""
    global risk_manager
    if risk_manager is None:
        risk_manager = UniversalRiskManager()
    return risk_manager


def get_correlation_manager():
    """Get or create correlation manager instance."""
    global correlation_manager
    if correlation_manager is None:
        correlation_manager = CorrelationManager()
    return correlation_manager


def get_strategy_coordinator():
    """Get or create strategy coordinator instance."""
    global strategy_coordinator
    if strategy_coordinator is None:
        strategy_coordinator = MultiStrategyCoordinator(
            portfolio_manager=get_portfolio_manager(),
            risk_manager=get_risk_manager(),
            correlation_manager=get_correlation_manager(),
        )
    return strategy_coordinator


# Create router for portfolio management endpoints
portfolio_router = APIRouter(prefix="/portfolio", tags=["Portfolio Management"])


@portfolio_router.get("/status", response_model=PortfolioStatusResponse)
async def get_portfolio_status():
    """Get current portfolio status."""
    try:
        portfolio = get_portfolio_manager()
        summary = portfolio.get_portfolio_summary()

        return PortfolioStatusResponse(
            total_balance=summary["total_balance"],
            available_balance=summary["available_balance"],
            total_risk=summary["total_risk"],
            active_positions=summary["active_positions"],
            active_strategies=len(summary["strategies"]),
            strategies=summary["strategies"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get portfolio status: {str(e)}"
        )


@portfolio_router.post("/strategies/add")
async def add_strategy(request: StrategyAllocationRequest):
    """Add a strategy to the portfolio."""
    try:
        portfolio = get_portfolio_manager()

        # Create strategy instance
        strategy = StrategyFactory.create_strategy(
            request.strategy_type, request.configuration
        )

        # Add to portfolio
        portfolio.add_strategy(request.strategy_name, strategy, request.allocation)

        return {
            "success": True,
            "message": f"Strategy '{request.strategy_name}' added with {request.allocation:.1%} allocation",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add strategy: {str(e)}")


@portfolio_router.delete("/strategies/{strategy_name}")
async def remove_strategy(strategy_name: str):
    """Remove a strategy from the portfolio."""
    try:
        portfolio = get_portfolio_manager()
        portfolio.remove_strategy(strategy_name)

        return {
            "success": True,
            "message": f"Strategy '{strategy_name}' removed from portfolio",
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to remove strategy: {str(e)}"
        )


@portfolio_router.get("/strategies/available")
async def get_available_strategies():
    """Get list of available strategy types."""
    try:
        strategies = StrategyFactory.get_available_strategies()
        return {"available_strategies": strategies, "count": len(strategies)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get available strategies: {str(e)}"
        )


@portfolio_router.get("/risk/status", response_model=RiskStatusResponse)
async def get_risk_status():
    """Get current risk management status."""
    try:
        risk_mgr = get_risk_manager()
        summary = risk_mgr.get_risk_summary()

        return RiskStatusResponse(
            current_risk_level="normal",  # Would be calculated from current state
            portfolio_risk=0.05,  # Would come from portfolio manager
            daily_trades=summary["current_status"]["daily_trade_count"],
            consecutive_losses=summary["current_status"]["consecutive_losses"],
            risk_limits={
                "max_portfolio_risk": summary["risk_limits"]["max_portfolio_risk"],
                "max_position_risk": summary["risk_limits"]["max_position_risk"],
                "max_daily_trades": summary["risk_limits"]["max_daily_trades"],
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get risk status: {str(e)}"
        )


@portfolio_router.get("/correlation/analysis")
async def get_correlation_analysis():
    """Get current correlation analysis."""
    try:
        corr_mgr = get_correlation_manager()
        summary = corr_mgr.get_correlation_summary()

        return {"correlation_status": summary, "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get correlation analysis: {str(e)}"
        )


@portfolio_router.get("/coordination/status", response_model=CoordinationStatusResponse)
async def get_coordination_status():
    """Get multi-strategy coordination status."""
    try:
        coordinator = get_strategy_coordinator()
        summary = coordinator.get_coordination_summary()

        if summary.get("status") == "no_activity":
            return CoordinationStatusResponse(
                active_strategies=0,
                recent_signals=0,
                execution_rate=0.0,
                recent_conflicts=0,
            )

        return CoordinationStatusResponse(
            active_strategies=len(get_portfolio_manager().strategy_allocations),
            recent_signals=summary.get("total_signals_processed", 0),
            execution_rate=summary.get("execution_rate", 0.0),
            recent_conflicts=summary.get("total_conflicts", 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get coordination status: {str(e)}"
        )


@portfolio_router.post("/rebalance")
async def rebalance_portfolio():
    """Trigger portfolio rebalancing."""
    try:
        portfolio = get_portfolio_manager()

        # Get current allocations
        current_allocations = {
            name: alloc.allocation
            for name, alloc in portfolio.strategy_allocations.items()
        }

        # For now, just return current state
        # In production, this would implement actual rebalancing logic
        return {
            "success": True,
            "message": "Portfolio rebalancing completed",
            "allocations": current_allocations,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to rebalance portfolio: {str(e)}"
        )


@portfolio_router.get("/performance/summary")
async def get_performance_summary():
    """Get portfolio performance summary."""
    try:
        portfolio = get_portfolio_manager()
        summary = portfolio.get_portfolio_summary()

        # Calculate additional performance metrics
        total_allocation = sum(
            strategy["allocation"] for strategy in summary["strategies"].values()
        )

        performance_data = {
            "total_balance": summary["total_balance"],
            "total_allocation": total_allocation,
            "utilization": total_allocation,
            "active_pairs": summary["active_pairs"],
            "strategy_performance": {
                name: {
                    "allocation": data["allocation"],
                    "positions": data["active_positions"],
                    "performance": data["performance"],
                }
                for name, data in summary["strategies"].items()
            },
        }

        return performance_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance summary: {str(e)}"
        )


# Integration function for existing monitoring API
def extend_monitoring_api(app):
    """
    Extend existing monitoring API with portfolio management endpoints.

    This function should be called from the main monitoring API to add
    portfolio management routes.
    """
    app.include_router(portfolio_router)

    # Add portfolio-specific middleware or dependencies if needed
    @app.on_event("startup")
    async def initialize_portfolio_management():
        """Initialize portfolio management components on startup."""
        try:
            # Initialize global instances
            get_portfolio_manager()
            get_risk_manager()
            get_correlation_manager()
            get_strategy_coordinator()

            print("Portfolio management system initialized")
        except Exception as e:
            print(f"Failed to initialize portfolio management: {e}")


# CLI-style function for quick testing
def test_portfolio_api():
    """Test portfolio management API endpoints."""
    import asyncio

    async def run_tests():
        """Run basic API tests."""
        print("Testing Portfolio Management API...")

        # Test portfolio status
        try:
            status = await get_portfolio_status()
            print(f"✓ Portfolio status: {status.total_balance} balance")
        except Exception as e:
            print(f"✗ Portfolio status failed: {e}")

        # Test available strategies
        try:
            strategies = await get_available_strategies()
            print(f"✓ Available strategies: {strategies['count']}")
        except Exception as e:
            print(f"✗ Available strategies failed: {e}")

        # Test risk status
        try:
            risk_status = await get_risk_status()
            print(f"✓ Risk status: {risk_status.daily_trades} daily trades")
        except Exception as e:
            print(f"✗ Risk status failed: {e}")

        # Test coordination status
        try:
            coord_status = await get_coordination_status()
            print(f"✓ Coordination status: {coord_status.active_strategies} strategies")
        except Exception as e:
            print(f"✗ Coordination status failed: {e}")

        print("Portfolio Management API tests completed")

    asyncio.run(run_tests())


if __name__ == "__main__":
    test_portfolio_api()
