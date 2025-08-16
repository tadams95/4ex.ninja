"""
Phase 2 Real-Time Monitoring Dashboard API

Main FastAPI application providing endpoints for regime monitoring,
performance tracking, and real-time alerts for the 4ex.ninja platform.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    BackgroundTasks,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import redis
from pydantic import BaseModel

from .regime_monitor import RegimeMonitor
from .performance_tracker import PerformanceTracker
from .alert_system import AlertSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="4ex.ninja Monitoring Dashboard API",
    description="Real-time regime monitoring and performance tracking for forex strategies",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
regime_monitor = RegimeMonitor()
performance_tracker = PerformanceTracker()
alert_system = AlertSystem()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


# Pydantic models for API responses
class RegimeStatus(BaseModel):
    current_regime: str
    confidence: float
    regime_strength: float
    time_in_regime: int  # minutes
    last_change: datetime
    volatility_level: str
    trend_direction: str


class PerformanceSummary(BaseModel):
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_trade_duration: float
    total_trades: int
    current_positions: int


class RegimePerformance(BaseModel):
    regime_name: str
    return_pct: float
    sharpe_ratio: float
    win_rate: float
    avg_duration_days: float
    trade_count: int
    drawdown: float


class AlertMessage(BaseModel):
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None


# API Endpoints


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "4ex.ninja Monitoring Dashboard API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check with component status"""
    try:
        # Check component health
        regime_health = await regime_monitor.health_check()
        performance_health = await performance_tracker.health_check()
        alert_health = await alert_system.health_check()

        # Check live data provider health
        live_data_status = False
        if (
            hasattr(regime_monitor, "live_data_provider")
            and regime_monitor.live_data_provider
        ):
            live_data_status = regime_monitor.live_data_provider.is_available

        return {
            "status": "healthy",
            "components": {
                "regime_monitor": regime_health,
                "performance_tracker": performance_health,
                "alert_system": alert_health,
                "live_data_provider": {
                    "status": "healthy" if live_data_status else "unavailable",
                    "available": live_data_status,
                },
            },
            "active_websockets": len(manager.active_connections),
            "timestamp": datetime.now(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500, content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/regime/current", response_model=RegimeStatus)
async def get_current_regime():
    """Get current market regime status"""
    try:
        regime_data = await regime_monitor.get_current_regime()
        return RegimeStatus(**regime_data)
    except Exception as e:
        logger.error(f"Error getting current regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data-source/status")
async def get_data_source_status():
    """Get live data source status and health"""
    try:
        live_provider_status = False
        data_source = "simulation"

        if (
            hasattr(regime_monitor, "live_data_provider")
            and regime_monitor.live_data_provider
        ):
            live_provider_status = regime_monitor.live_data_provider.is_available
            if live_provider_status:
                data_source = "live"

        # Get the latest regime data to check timestamp
        current_regime = await regime_monitor.get_current_regime()
        last_update = current_regime.get("last_change", datetime.now())

        return {
            "data_source": data_source,
            "live_provider_available": live_provider_status,
            "last_update": last_update,
            "update_interval_seconds": regime_monitor.update_interval,
            "monitoring_pairs": regime_monitor.monitoring_pairs,
            "timestamp": datetime.now(),
        }
    except Exception as e:
        logger.error(f"Error getting data source status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/regime/history")
async def get_regime_history(timeframe: str = "1d", limit: int = 100):
    """Get historical regime changes"""
    try:
        history = await regime_monitor.get_regime_history(timeframe, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting regime history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/summary", response_model=PerformanceSummary)
async def get_performance_summary():
    """Get overall strategy performance summary"""
    try:
        summary = await performance_tracker.get_performance_summary()
        return PerformanceSummary(**summary)
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/by-regime", response_model=List[RegimePerformance])
async def get_performance_by_regime():
    """Get performance breakdown by market regime"""
    try:
        performance_data = await performance_tracker.get_performance_by_regime()
        return [RegimePerformance(**data) for data in performance_data]
    except Exception as e:
        logger.error(f"Error getting performance by regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/charts")
async def get_performance_charts(
    timeframe: str = "1d", chart_type: str = "equity_curve"
):
    """Get performance chart data"""
    try:
        chart_data = await performance_tracker.get_chart_data(timeframe, chart_type)
        return {"chart_data": chart_data}
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/recent")
async def get_recent_alerts(limit: int = 50):
    """Get recent alerts and notifications"""
    try:
        alerts = await alert_system.get_recent_alerts(limit)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        result = await alert_system.acknowledge_alert(alert_id)
        return {"acknowledged": result}
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/strategy/health")
async def get_strategy_health():
    """Get strategy health indicators"""
    try:
        health_data = await performance_tracker.get_strategy_health()
        return {"health": health_data}
    except Exception as e:
        logger.error(f"Error getting strategy health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time regime and performance updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time updates every 5 seconds
            await asyncio.sleep(5)

            # Get current data
            regime_data = await regime_monitor.get_current_regime()
            performance_data = await performance_tracker.get_performance_summary()

            # Send update
            update = {
                "type": "realtime_update",
                "timestamp": datetime.now().isoformat(),
                "data": {"regime": regime_data, "performance": performance_data},
            }

            await manager.send_personal_message(json.dumps(update), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Background task for monitoring
async def live_monitoring_task():
    """Enhanced background task with live data updates"""
    logger.info("Starting live monitoring task...")

    while True:
        try:
            # Update regime data with live market information
            await regime_monitor.update_live_regime_data()

            # Get current regime status for broadcasting
            current_regime = await regime_monitor.get_current_regime()

            # Broadcast current regime data via WebSocket
            regime_update = {
                "type": "regime_update",
                "timestamp": datetime.now().isoformat(),
                "data": current_regime,
            }
            await manager.broadcast(json.dumps(regime_update))

            # Check for regime changes
            regime_change = await regime_monitor.check_for_regime_change()
            if regime_change:
                alert = {
                    "type": "regime_change",
                    "timestamp": datetime.now().isoformat(),
                    "data": regime_change,
                }
                await manager.broadcast(json.dumps(alert))
                await alert_system.send_alert("regime_change", regime_change)

            # Check strategy health
            health_issues = await performance_tracker.check_strategy_health()
            if health_issues:
                alert = {
                    "type": "strategy_health",
                    "timestamp": datetime.now().isoformat(),
                    "data": health_issues,
                }
                await manager.broadcast(json.dumps(alert))
                await alert_system.send_alert("strategy_health", health_issues)

            await asyncio.sleep(30)  # Check every 30 seconds for live data

        except Exception as e:
            logger.error(f"Live monitoring task error: {e}")
            await asyncio.sleep(60)  # Wait longer on error


# Keep the old monitoring_task for backward compatibility
async def monitoring_task():
    """Background monitoring task (legacy)"""
    logger.info("Starting background monitoring task...")

    while True:
        try:
            # Check for regime changes
            regime_change = await regime_monitor.check_for_regime_change()
            if regime_change:
                alert = {
                    "type": "regime_change",
                    "timestamp": datetime.now().isoformat(),
                    "data": regime_change,
                }
                await manager.broadcast(json.dumps(alert))
                await alert_system.send_alert("regime_change", regime_change)

            # Check strategy health
            health_issues = await performance_tracker.check_strategy_health()
            if health_issues:
                alert = {
                    "type": "strategy_health",
                    "timestamp": datetime.now().isoformat(),
                    "data": health_issues,
                }
                await manager.broadcast(json.dumps(alert))
                await alert_system.send_alert("strategy_health", health_issues)

            await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Monitoring task error: {e}")
            await asyncio.sleep(60)  # Wait longer on error


@app.on_event("startup")
async def startup_event():
    """Initialize monitoring components on startup"""
    logger.info("Starting 4ex.ninja Monitoring Dashboard API...")

    # Initialize components
    await regime_monitor.initialize()
    await performance_tracker.initialize()
    await alert_system.initialize()

    # Start live monitoring task (new enhanced version)
    asyncio.create_task(live_monitoring_task())

    logger.info(
        "Monitoring Dashboard API started successfully with live data integration"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Monitoring Dashboard API...")

    # Close all WebSocket connections
    for connection in manager.active_connections:
        await connection.close()

    # Cleanup components
    await regime_monitor.cleanup()
    await performance_tracker.cleanup()
    await alert_system.cleanup()

    logger.info("Monitoring Dashboard API shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
