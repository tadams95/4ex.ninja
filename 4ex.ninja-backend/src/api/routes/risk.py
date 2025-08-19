"""
Risk Management API Routes

Provides endpoints for VaR (Value at Risk) monitoring and correlation matrix data
for the Phase 2 dashboard implementation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List
import logging
from datetime import datetime, timezone, timedelta
import asyncio

# Import the Phase 2 risk management systems
try:
    from risk.var_monitor import VaRMonitor
    from risk.correlation_manager import CorrelationManager
    from risk.correlation_trends import CorrelationTrendAnalyzer
    from backtesting.portfolio_manager import (
        PortfolioState,
        Position,
        StrategyAllocation,
    )
except ImportError as e:
    logging.warning(f"Risk modules import failed: {e}. Using fallback implementation.")
    VaRMonitor = None
    CorrelationManager = None
    CorrelationTrendAnalyzer = None
    PortfolioState = None

# Import fallback mock data generators
try:
    from api.fallback.correlation_trends_mock import (
        generate_mock_correlation_trends,
        generate_mock_correlation_forecast,
        generate_mock_market_regime,
    )

    FALLBACK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Fallback mock data not available: {e}")
    FALLBACK_AVAILABLE = False

router = APIRouter(prefix="/api/risk", tags=["risk"])
logger = logging.getLogger(__name__)

# Initialize risk management systems
var_monitor = None
correlation_manager = None
trend_analyzer = None


async def get_var_monitor():
    """Dependency to get VaRMonitor instance"""
    global var_monitor
    if var_monitor is None and VaRMonitor is not None:
        try:
            var_monitor = VaRMonitor()
            logger.info("VaRMonitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VaRMonitor: {e}")
            var_monitor = None
    return var_monitor


async def get_correlation_manager():
    """Dependency to get CorrelationManager instance"""
    global correlation_manager
    if correlation_manager is None and CorrelationManager is not None:
        try:
            correlation_manager = CorrelationManager()
            logger.info("CorrelationManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CorrelationManager: {e}")
            correlation_manager = None
    return correlation_manager


async def get_trend_analyzer():
    """Dependency to get CorrelationTrendAnalyzer instance"""
    global trend_analyzer, correlation_manager
    if trend_analyzer is None and CorrelationTrendAnalyzer is not None:
        try:
            if correlation_manager is None:
                correlation_manager = await get_correlation_manager()
            trend_analyzer = CorrelationTrendAnalyzer(correlation_manager)
            logger.info("CorrelationTrendAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CorrelationTrendAnalyzer: {e}")
            trend_analyzer = None
    return trend_analyzer


def create_mock_portfolio_state() -> Any:
    """Create a mock portfolio state for dashboard purposes"""
    if PortfolioState is None:
        return None

    try:
        # Create mock positions for major currency pairs
        mock_positions = {
            "EUR_USD": Position(
                position_id="pos_001",
                pair="EUR_USD",
                direction="BUY",
                entry_price=1.0850,
                position_size=10000.0,
                stop_loss=1.0800,
                take_profit=1.0920,
                entry_time=datetime.now(timezone.utc),
                strategy_name="swing_001",
                unrealized_pnl=150.0,
            ),
            "GBP_USD": Position(
                position_id="pos_002",
                pair="GBP_USD",
                direction="BUY",
                entry_price=1.2650,
                position_size=8000.0,
                stop_loss=1.2600,
                take_profit=1.2720,
                entry_time=datetime.now(timezone.utc),
                strategy_name="swing_002",
                unrealized_pnl=-120.0,
            ),
            "AUD_USD": Position(
                position_id="pos_003",
                pair="AUD_USD",
                direction="BUY",
                entry_price=0.6750,
                position_size=12000.0,
                stop_loss=0.6700,
                take_profit=0.6820,
                entry_time=datetime.now(timezone.utc),
                strategy_name="swing_003",
                unrealized_pnl=180.0,
            ),
            "USD_JPY": Position(
                position_id="pos_004",
                pair="USD_JPY",
                direction="SELL",  # Short position
                entry_price=149.50,
                position_size=15000.0,
                stop_loss=150.00,
                take_profit=148.80,
                entry_time=datetime.now(timezone.utc),
                strategy_name="swing_004",
                unrealized_pnl=300.0,
            ),
        }

        # Create the portfolio state with empty strategy allocations for now
        portfolio_state = PortfolioState(
            total_balance=100000.0,
            available_balance=50000.0,
            total_risk=0.06,  # 6% total portfolio risk
            active_positions=mock_positions,
            strategy_allocations={},  # Keep empty for now
            correlation_matrix={},
            last_updated=datetime.now(timezone.utc),
        )

        return portfolio_state

    except Exception as e:
        logger.error(f"Failed to create mock portfolio state: {e}")
        return None


@router.get("/var-summary")
async def get_var_summary() -> dict:
    """Get VaR summary statistics for the dashboard"""
    try:
        logger.info("Fetching VaR summary")

        # Get mock portfolio state for calculation
        portfolio_state = create_mock_portfolio_state()
        if portfolio_state is None:
            raise HTTPException(
                status_code=500, detail="Unable to initialize portfolio state"
            )

        var_monitor = await get_var_monitor()
        if not var_monitor:
            raise HTTPException(
                status_code=503, detail="VaR monitoring system unavailable"
            )

        # Calculate VaR with portfolio state - returns Dict[str, VaRResult]
        var_results = await var_monitor.calculate_portfolio_var(portfolio_state)

        # Extract VaR values from results
        parametric_var = var_results.get("parametric")
        historical_var = var_results.get("historical")
        monte_carlo_var = var_results.get("monte_carlo")

        # Format response for dashboard
        var_summary = {
            "portfolio_var": {
                "parametric": parametric_var.value if parametric_var else 0,
                "historical": historical_var.value if historical_var else 0,
                "monte_carlo": monte_carlo_var.value if monte_carlo_var else 0,
                "confidence_level": (
                    parametric_var.confidence_level if parametric_var else 0.95
                ),
            },
            "risk_metrics": {
                "total_exposure": portfolio_state.total_balance
                - portfolio_state.available_balance,
                "risk_utilization": 0.65,  # Mock value
                "var_limit": 5000.0,  # Mock limit
                "breaches_today": 0,  # Mock breaches
            },
            "position_breakdown": [
                {
                    "pair": pair,
                    "exposure": abs(position.position_size * position.entry_price),
                    "var_contribution": 0,  # Would need individual position VaR
                    "pnl": position.unrealized_pnl,
                }
                for pair, position in portfolio_state.active_positions.items()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }

        logger.info("VaR summary calculated successfully")
        return var_summary

    except Exception as e:
        logger.error(f"Error fetching VaR summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch VaR summary: {e}")


@router.get("/correlation-matrix")
async def get_correlation_matrix() -> dict:
    """Get correlation matrix for currency pairs in the portfolio"""
    try:
        logger.info("Fetching correlation matrix")

        # Get mock portfolio state for calculation
        portfolio_state = create_mock_portfolio_state()
        if portfolio_state is None:
            raise HTTPException(
                status_code=500, detail="Unable to initialize portfolio state"
            )

        correlation_manager = await get_correlation_manager()
        if not correlation_manager:
            raise HTTPException(
                status_code=503, detail="Correlation management system unavailable"
            )

        # Calculate correlation matrix with portfolio state - returns pandas DataFrame
        correlation_df = await correlation_manager.calculate_correlation_matrix(
            portfolio_state
        )

        # Convert DataFrame to dictionary for JSON response
        correlation_matrix = {}
        high_correlations = []

        if not correlation_df.empty:
            # Convert to nested dictionary
            correlation_matrix = correlation_df.to_dict()

            # Find high correlations (above threshold)
            threshold = 0.4
            for pair1 in correlation_df.index:
                for pair2 in correlation_df.columns:
                    if pair1 != pair2:
                        try:
                            # Simple numpy/pandas-safe conversion
                            corr_float = float(str(correlation_df.loc[pair1, pair2]))
                        except (ValueError, TypeError):
                            corr_float = 0.0

                        if abs(corr_float) > threshold:
                            high_correlations.append(
                                {
                                    "pair1": pair1,
                                    "pair2": pair2,
                                    "correlation": corr_float,
                                }
                            )

        # Format response for dashboard
        correlation_summary = {
            "matrix": correlation_matrix,
            "risk_alerts": {
                "high_correlations": high_correlations,
                "breach_count": len(high_correlations),
                "threshold": 0.4,
            },
            "pairs_analysis": [
                {
                    "pair": pair,
                    "correlations": correlation_matrix.get(pair, {}),
                    "average_correlation": (
                        sum(correlation_matrix.get(pair, {}).values())
                        / max(len(correlation_matrix.get(pair, {})), 1)
                        if correlation_matrix.get(pair)
                        else 0
                    ),
                }
                for pair in portfolio_state.active_positions.keys()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }

        logger.info("Correlation matrix calculated successfully")
        return correlation_summary

    except Exception as e:
        logger.error(f"Error fetching correlation matrix: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch correlation matrix: {e}"
        )


@router.get("/correlation-trends")
async def get_correlation_trends(
    hours_back: int = Query(
        168,
        ge=24,
        le=720,
        description="Hours of history for trend analysis (default: 1 week)",
    )
) -> dict:
    """Get correlation trend analysis for currency pairs"""
    try:
        logger.info(f"Fetching correlation trends with {hours_back}-hour lookback")

        # For Phase 2 demo, use fallback mock data since full system has dependency issues
        if FALLBACK_AVAILABLE:
            logger.info("Using fallback mock correlation trends data for Phase 2 demo")
            return generate_mock_correlation_trends(hours_back)
        else:
            raise HTTPException(
                status_code=503,
                detail="Correlation trend analysis system unavailable and no fallback data",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching correlation trends: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch correlation trends: {e}"
        )


@router.get("/correlation-forecast")
async def get_correlation_forecast() -> dict:
    """Get correlation movement predictions for currency pairs"""
    try:
        logger.info("Generating correlation forecasts")

        # Try to use the real implementation first
        trend_analyzer = await get_trend_analyzer()

        if trend_analyzer and CorrelationTrendAnalyzer is not None:
            try:
                # Use real implementation (when available)
                logger.info("Using real correlation forecast system")
                # Implementation would go here when the full system is ready
                pass
            except Exception as e:
                logger.warning(
                    f"Real forecast system failed: {e}, falling back to mock data"
                )

        # Use fallback mock data
        if FALLBACK_AVAILABLE:
            logger.info("Using fallback mock correlation forecast data")
            return generate_mock_correlation_forecast()
        else:
            raise HTTPException(
                status_code=503,
                detail="Correlation forecast system unavailable and no fallback data",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating correlation forecast: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate correlation forecast: {e}"
        )


@router.get("/correlation-regime")
async def get_correlation_regime() -> dict:
    """Get market regime analysis affecting correlation patterns"""
    try:
        logger.info("Analyzing correlation market regime")

        # Try to use the real implementation first
        trend_analyzer = await get_trend_analyzer()

        if trend_analyzer and CorrelationTrendAnalyzer is not None:
            try:
                # Use real implementation (when available)
                regimes = await trend_analyzer.detect_regime_shifts()
                alerts = await trend_analyzer.generate_trend_alerts()

                response = {
                    "current_regime": regimes.get("current"),
                    "regime_characteristics": {},
                    "trend_alerts": alerts,
                    "alert_summary": {
                        "total_alerts": len(alerts),
                        "high_severity": sum(
                            1 for a in alerts if a.get("severity") == "high"
                        ),
                        "medium_severity": sum(
                            1 for a in alerts if a.get("severity") == "medium"
                        ),
                        "low_severity": sum(
                            1 for a in alerts if a.get("severity") == "low"
                        ),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "success",
                }

                # Format regime characteristics if available
                if "current" in regimes:
                    current_regime = regimes["current"]
                    response["regime_characteristics"] = {
                        "regime_type": current_regime.regime_type,
                        "expected_correlation_range": {
                            "min": current_regime.expected_correlation_range[0],
                            "max": current_regime.expected_correlation_range[1],
                        },
                        "confidence": current_regime.regime_confidence,
                        "characteristics": current_regime.characteristics,
                    }

                logger.info(
                    f"Market regime analysis completed: {len(alerts)} alerts generated"
                )
                return response

            except Exception as e:
                logger.warning(
                    f"Real regime analyzer failed: {e}, falling back to mock data"
                )

        # Use fallback mock data
        if FALLBACK_AVAILABLE:
            logger.info("Using fallback mock market regime data")
            return generate_mock_market_regime()
        else:
            raise HTTPException(
                status_code=503,
                detail="Correlation regime analysis system unavailable and no fallback data",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing correlation regime: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze correlation regime: {e}"
        )


@router.get("/status")
async def get_risk_status() -> Dict[str, Any]:
    """
    Get overall risk system status for health checking.

    Returns:
        Dict containing system status and availability of risk components.
    """
    try:
        var_available = VaRMonitor is not None
        correlation_available = CorrelationManager is not None

        status = {
            "risk_system_status": (
                "operational"
                if (var_available and correlation_available)
                else "degraded"
            ),
            "var_monitor_available": var_available,
            "correlation_manager_available": correlation_available,
            "fallback_mode": not (var_available and correlation_available),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Risk status check: {status['risk_system_status']}")
        return status

    except Exception as e:
        logger.error(f"Error checking risk status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check risk status: {str(e)}"
        )
