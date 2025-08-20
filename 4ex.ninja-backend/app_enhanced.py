"""
4ex.ninja Enhanced Backend
Production-focused FastAPI application for Enhanced Daily Strategy (Phase 1).
Achieves 522% returns with 60.87% win rate using Phase 1 enhancements:
- Session-Based Trading
- Support/Resistance Confluence
- Dynamic Position Sizing
"""

import asyncio
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.signal_models import (
    TradingSignal,
    HealthCheckResponse,
    SignalResponse,
    PerformanceResponse,
)
from services.signal_service import SignalService
from services.data_service import DataService
from services.notification_service import NotificationService
from services.scheduler_service import ForexSchedulerService
from services.enhanced_daily_production_service import EnhancedDailyProductionService
from config.settings import get_settings


# Initialize FastAPI app
app = FastAPI(
    title="4ex.ninja Enhanced Backend",
    description="Production-focused backend for Enhanced Daily Strategy",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
signal_service = SignalService()
data_service = DataService()
notification_service = NotificationService()
scheduler_service = ForexSchedulerService(data_service, signal_service)
enhanced_daily_service = EnhancedDailyProductionService()
settings = get_settings()

# App startup time for uptime calculation
startup_time = time.time()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    import logging

    logging.info("🚀 Starting 4ex.ninja Enhanced Backend...")

    # Start the forex market scheduler
    await scheduler_service.start_scheduler()
    logging.info("✅ All services initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    import logging

    logging.info("⏹️ Shutting down 4ex.ninja Enhanced Backend...")

    # Stop the scheduler gracefully
    await scheduler_service.stop_scheduler()
    logging.info("✅ All services stopped successfully")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "4ex.ninja Enhanced Backend",
        "version": "2.0.0",
        "status": "operational",
        "strategy": "Enhanced Daily Strategy (Phase 1)",
        "backtest_performance": {
            "return_percent": 522.91,
            "win_rate_percent": 60.87,
            "max_drawdown_percent": 3.46,
        },
        "endpoints": {
            "scan": "/scan",
            "signals": "/signals",
            "config": "/config",
            "performance": "/performance",
        },
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check data service
        data_health = await data_service.health_check()

        # Check enhanced daily service
        enhanced_healthy = len(enhanced_daily_service.monitored_pairs) > 0

        # Check scheduler
        scheduler_status = scheduler_service.get_scheduler_status()

        return HealthCheckResponse(
            status="healthy" if data_health and enhanced_healthy else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            services={
                "data_service": "healthy" if data_health else "unhealthy",
                "enhanced_daily": "healthy" if enhanced_healthy else "unhealthy",
                "scheduler": (
                    "healthy" if scheduler_status["is_running"] else "unhealthy"
                ),
            },
            version="2.0.0",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/config")
async def get_strategy_config():
    """Get Enhanced Daily Strategy configuration."""
    return {
        "success": True,
        "strategy": "Enhanced Daily Strategy (Phase 1)",
        "config": {
            "enhancements": [
                "Session-Based Trading (JPY pairs during Asian session)",
                "Support/Resistance Confluence Detection",
                "Dynamic Position Sizing",
            ],
            "expected_improvements": {
                "trade_quality": "+30%",
                "win_rate": "+15%",
                "returns": "+25%",
            },
            "backtest_results": {
                "return_percent": 522.91,
                "win_rate_percent": 60.87,
                "max_drawdown_percent": 3.46,
                "total_trades": 230,
                "sharpe_ratio": 0.51,
            },
            "monitored_pairs": enhanced_daily_service.monitored_pairs,
            "phase": "Phase 1 - Quick Wins",
            "status": "Production Ready",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/scan")
async def scan_all_pairs():
    """Scan all pairs using Enhanced Daily Strategy."""
    try:
        results = await enhanced_daily_service.get_enhanced_market_analysis()
        return {
            "success": True,
            "strategy": "Enhanced Daily Strategy (Phase 1)",
            "data": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Enhanced Daily scan failed: {str(e)}"
        )


@app.get("/signals", response_model=SignalResponse)
async def get_current_signals():
    """Get current Enhanced Daily Strategy signals."""
    try:
        signals = await enhanced_daily_service.generate_enhanced_signals()
        return SignalResponse(
            success=True,
            signals=signals,
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "strategy": "Enhanced Daily Strategy (Phase 1)",
                "signal_count": len(signals),
                "active_pairs": enhanced_daily_service.monitored_pairs,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Enhanced Daily signal generation failed: {str(e)}"
        )


@app.get("/signals/{pair}")
async def get_pair_signals(pair: str):
    """Get Enhanced Daily Strategy signals for specific pair."""
    try:
        # Get all signals and filter for the specific pair
        all_signals = await enhanced_daily_service.generate_enhanced_signals()
        pair_signals = [s for s in all_signals if s.get("pair") == pair]

        return {
            "success": True,
            "strategy": "Enhanced Daily Strategy (Phase 1)",
            "pair": pair,
            "signals": pair_signals,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced Daily signal retrieval failed for {pair}: {str(e)}",
        )


@app.get("/performance", response_model=PerformanceResponse)
async def get_overall_performance():
    """Get Enhanced Daily Strategy overall performance metrics."""
    try:
        return PerformanceResponse(
            success=True,
            performance={
                "strategy": "Enhanced Daily Strategy (Phase 1)",
                "live_metrics": enhanced_daily_service.performance_metrics,
                "active_signals": len(enhanced_daily_service.active_signals),
                "monitored_pairs": enhanced_daily_service.monitored_pairs,
                "backtest_performance": {
                    "return_percent": 522.91,
                    "win_rate_percent": 60.87,
                    "max_drawdown_percent": 3.46,
                    "total_trades": 230,
                    "sharpe_ratio": 0.51,
                },
            },
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced Daily performance retrieval failed: {str(e)}",
        )


@app.get("/performance/{pair}")
async def get_pair_performance(pair: str):
    """Get Enhanced Daily Strategy performance for specific pair."""
    try:
        if pair not in enhanced_daily_service.monitored_pairs:
            raise HTTPException(
                status_code=404,
                detail=f"Pair {pair} not monitored by Enhanced Daily Strategy",
            )

        return {
            "success": True,
            "strategy": "Enhanced Daily Strategy (Phase 1)",
            "pair": pair,
            "performance": {
                "monitored": True,
                "metrics": enhanced_daily_service.performance_metrics.get(pair, {}),
                "active_signals": [
                    s
                    for s in enhanced_daily_service.active_signals.values()
                    if s.get("pair") == pair
                ],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Performance retrieval failed for {pair}: {str(e)}"
        )


@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get forex market scheduler status."""
    try:
        status = scheduler_service.get_scheduler_status()
        return {
            "success": True,
            "scheduler": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler status: {str(e)}"
        )


@app.post("/scheduler/restart")
async def restart_scheduler():
    """Restart the forex market scheduler."""
    try:
        await scheduler_service.stop_scheduler()
        await scheduler_service.start_scheduler()
        return {
            "success": True,
            "message": "Scheduler restarted successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restart scheduler: {str(e)}"
        )


@app.get("/data/health")
async def get_data_health():
    """Get data service health status."""
    try:
        health = await data_service.health_check()
        return {
            "success": True,
            "data_service_healthy": health,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Data health check failed: {str(e)}"
        )


@app.post("/notifications/test")
async def test_notifications():
    """Test notification system."""
    try:
        test_message = {
            "title": "4ex.ninja Enhanced Backend Test",
            "message": "Enhanced Daily Strategy notification system working!",
            "timestamp": datetime.utcnow().isoformat(),
        }

        success = await notification_service.send_notification(test_message)

        return {
            "success": success,
            "message": (
                "Test notification sent" if success else "Test notification failed"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Notification test failed: {str(e)}"
        )


@app.get("/status")
async def get_system_status():
    """Get comprehensive system status."""
    try:
        # Get signal statistics
        signal_stats = await signal_service.get_signal_statistics()

        # Get data health
        data_health = await data_service.health_check()

        # Get enhanced daily metrics
        enhanced_metrics = enhanced_daily_service.performance_metrics

        return {
            "system_status": "operational",
            "uptime_seconds": time.time() - startup_time,
            "strategy": "Enhanced Daily Strategy (Phase 1)",
            "backtest_performance": {
                "return_percent": 522.91,
                "win_rate_percent": 60.87,
                "max_drawdown_percent": 3.46,
                "total_trades": 230,
            },
            "live_performance": enhanced_metrics,
            "signal_statistics": signal_stats,
            "data_health": data_health,
            "monitored_pairs": enhanced_daily_service.monitored_pairs,
            "active_signals": len(enhanced_daily_service.active_signals),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system status: {str(e)}"
        )


# Exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
