"""
4ex.ninja Clean Backend
Production-focused FastAPI application for optimal MA strategy (fast_ma=50, slow_ma=200).
Achieves 18.0-19.8% returns with conservative_moderate_daily parameters.
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
    StrategyConfigResponse,
    PerformanceResponse,
    GenerateSignalRequest,
    StrategyConfig,
)
from services.ma_strategy_service import MAStrategyService
from services.signal_service import SignalService
from services.data_service import DataService
from services.notification_service import NotificationService
from services.scheduler_service import ForexSchedulerService
from config.settings import get_settings, OPTIMAL_STRATEGY_CONFIG


# Initialize FastAPI app
app = FastAPI(
    title="4ex.ninja Clean Backend",
    description="Production-focused backend for optimal MA trading strategy",
    version="1.0.0",
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
ma_strategy_service = MAStrategyService()
signal_service = SignalService()
data_service = DataService()
notification_service = NotificationService()
scheduler_service = ForexSchedulerService(data_service, signal_service)
settings = get_settings()

# App startup time for uptime calculation
startup_time = time.time()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    import logging
    logging.info("🚀 Starting 4ex.ninja Backend...")
    
    # Start the forex market scheduler
    await scheduler_service.start_scheduler()
    logging.info("✅ All services initialized successfully")


@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown."""
    import logging
    logging.info("⏹️ Shutting down 4ex.ninja Backend...")
    
    # Stop the scheduler gracefully
    await scheduler_service.stop_scheduler()
    logging.info("✅ All services stopped successfully")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "4ex.ninja Clean Backend",
        "version": "1.0.0",
        "status": "operational",
        "strategy": "conservative_moderate_daily (MA 50/200)",
        "expected_return": "18.0-19.8%",
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        uptime = time.time() - startup_time
        strategy_count = len(OPTIMAL_STRATEGY_CONFIG)

        # Get latest signal time from signal service
        recent_signals = await signal_service.get_all_recent_signals(limit=1)
        last_signal_time = recent_signals[0].timestamp if recent_signals else None

        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime,
            strategy_count=strategy_count,
            last_signal_time=last_signal_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/strategy/config", response_model=StrategyConfigResponse)
async def get_all_strategy_configs():
    """Get all optimal strategy configurations."""
    try:
        configs = {}
        for pair_key, config_data in OPTIMAL_STRATEGY_CONFIG.items():
            configs[pair_key] = StrategyConfig(**config_data)

        return StrategyConfigResponse(
            success=True,
            message=f"Retrieved {len(configs)} optimal strategy configurations",
            configs=configs,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get strategy configs: {str(e)}"
        )


@app.get("/strategy/config/{pair}", response_model=StrategyConfigResponse)
async def get_strategy_config(pair: str):
    """Get strategy configuration for a specific pair."""
    try:
        config = await ma_strategy_service.get_strategy_config(pair)
        return StrategyConfigResponse(
            success=True, message=f"Retrieved configuration for {pair}", config=config
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get strategy config: {str(e)}"
        )


@app.post("/signals/generate", response_model=SignalResponse)
async def generate_signal(request: GenerateSignalRequest):
    """Generate trading signal for a specific pair."""
    try:
        # Extract currency pair from request (e.g., "EUR_USD_D" -> "EUR_USD")
        pair_parts = request.pair.split("_")
        if len(pair_parts) < 2:
            raise ValueError("Invalid pair format. Use format like 'EUR_USD_D'")

        currency_pair = f"{pair_parts[0]}_{pair_parts[1]}"

        # Get historical data
        price_data = await data_service.get_historical_data(currency_pair)

        # Generate signal
        signal = await signal_service.generate_signal_for_pair(
            request.pair, price_data, request.force_recalculate
        )

        return SignalResponse(
            success=True,
            message=f"Generated {signal.signal_type} signal for {request.pair}",
            signal=signal,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate signal: {str(e)}"
        )


@app.post("/signals/generate-all", response_model=SignalResponse)
async def generate_all_signals():
    """Generate signals for all supported pairs."""
    try:
        # Get historical data for all pairs
        all_price_data = await data_service.get_historical_data_for_all_pairs()

        # Generate signals for all pairs
        signals = await signal_service.generate_signals_for_all_pairs(all_price_data)

        return SignalResponse(
            success=True,
            message=f"Generated {len(signals)} signals for all supported pairs",
            signals=signals,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate signals: {str(e)}"
        )


@app.get("/signals/recent", response_model=SignalResponse)
async def get_recent_signals(limit: int = 50):
    """Get recent signals across all pairs."""
    try:
        signals = await signal_service.get_all_recent_signals(limit=limit)

        return SignalResponse(
            success=True,
            message=f"Retrieved {len(signals)} recent signals",
            signals=signals,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent signals: {str(e)}"
        )


@app.get("/signals/active", response_model=SignalResponse)
async def get_active_signals():
    """Get currently active trading signals (BUY/SELL)."""
    try:
        signals = await signal_service.get_active_signals()

        return SignalResponse(
            success=True,
            message=f"Retrieved {len(signals)} active signals",
            signals=signals,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get active signals: {str(e)}"
        )


@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get forex market scheduler status and job information."""
    try:
        status = scheduler_service.get_scheduler_status()
        
        return {
            "success": True,
            "message": "Scheduler status retrieved successfully",
            "scheduler": status
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
            "message": "Scheduler restarted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restart scheduler: {str(e)}"
        )


@app.get("/signals/{pair}", response_model=SignalResponse)
async def get_signals_by_pair(pair: str, limit: int = 20):
    """Get recent signals for a specific pair."""
    try:
        signals = await signal_service.get_signals_by_pair(pair, limit=limit)

        return SignalResponse(
            success=True,
            message=f"Retrieved {len(signals)} signals for {pair}",
            signals=signals,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get signals for {pair}: {str(e)}"
        )


@app.get("/performance/{pair}", response_model=PerformanceResponse)
async def get_performance_metrics(pair: str):
    """Get performance metrics for a specific pair."""
    try:
        # Get recent signals for the pair
        signals = await signal_service.get_signals_by_pair(f"{pair}_D", limit=100)

        # Calculate performance metrics
        metrics = await ma_strategy_service.calculate_performance_metrics(signals, pair)

        return PerformanceResponse(
            success=True,
            message=f"Retrieved performance metrics for {pair}",
            metrics=metrics,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance metrics: {str(e)}"
        )


@app.get("/performance", response_model=PerformanceResponse)
async def get_all_performance_metrics():
    """Get performance metrics for all pairs."""
    try:
        all_metrics = {}
        supported_pairs = await ma_strategy_service.get_all_supported_pairs()

        for pair_key in supported_pairs:
            # Extract currency pair (e.g., "EUR_USD_D" -> "EUR_USD")
            pair_parts = pair_key.split("_")
            if len(pair_parts) >= 2:
                currency_pair = f"{pair_parts[0]}_{pair_parts[1]}"

                signals = await signal_service.get_signals_by_pair(pair_key, limit=100)
                metrics = await ma_strategy_service.calculate_performance_metrics(
                    signals, currency_pair
                )
                all_metrics[currency_pair] = metrics

        return PerformanceResponse(
            success=True,
            message=f"Retrieved performance metrics for {len(all_metrics)} pairs",
            all_metrics=all_metrics,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance metrics: {str(e)}"
        )


@app.get("/data/prices")
async def get_current_prices():
    """Get current prices for all supported pairs."""
    try:
        prices = await data_service.get_all_current_prices()

        return {
            "success": True,
            "message": f"Retrieved current prices for {len(prices)} pairs",
            "prices": prices,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get current prices: {str(e)}"
        )


@app.get("/data/health")
async def get_data_health():
    """Get data service health status."""
    try:
        health_info = await data_service.health_check()
        return health_info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Data health check failed: {str(e)}"
        )


@app.post("/notifications/test")
async def test_notification():
    """Send a test notification to Discord."""
    try:
        success = await notification_service.test_notification()

        if success:
            return {"success": True, "message": "Test notification sent successfully"}
        else:
            return {
                "success": False,
                "message": "Failed to send test notification (check webhook URL)",
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

        # Check optimal parameters
        optimal_params = await ma_strategy_service.validate_optimal_parameters()

        return {
            "system_status": "operational",
            "uptime_seconds": time.time() - startup_time,
            "optimal_parameters": optimal_params,
            "strategy_type": "conservative_moderate_daily",
            "ma_parameters": {"fast_ma": 50, "slow_ma": 200},
            "expected_returns": "18.0-19.8%",
            "signal_statistics": signal_stats,
            "data_health": data_health,
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
