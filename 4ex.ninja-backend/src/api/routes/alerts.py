"""
Alert Management API Endpoints

FastAPI endpoints for managing system alerts, viewing alert history,
and configuring alert settings.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timezone

from infrastructure.monitoring.alerts import (
    alert_manager,
    Alert,
    AlertType,
    AlertSeverity,
    AlertStatus,
)

# Initialize router
router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("/")
async def get_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=500, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
) -> Dict[str, Any]:
    """
    Get system alerts with optional filtering.
    """
    try:
        # Get alerts from alert manager
        alerts = alert_manager.get_alerts(
            status=status, severity=severity, limit=limit, offset=offset
        )

        # Convert alerts to dict format
        alert_data = []
        for alert in alerts:
            alert_data.append(
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "context": alert.context,
                    "tags": alert.tags,
                    "acknowledged_by": alert.acknowledged_by,
                    "acknowledged_at": (
                        alert.acknowledged_at.isoformat()
                        if alert.acknowledged_at
                        else None
                    ),
                    "resolved_at": (
                        alert.resolved_at.isoformat() if alert.resolved_at else None
                    ),
                    "escalation_level": alert.escalation_level,
                }
            )

        return {
            "alerts": alert_data,
            "total": len(alert_data),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alerts: {str(e)}"
        )


@router.get("/active")
async def get_active_alerts() -> Dict[str, Any]:
    """
    Get currently active alerts.
    """
    try:
        active_alerts = alert_manager.get_active_alerts()

        alert_data = []
        for alert in active_alerts:
            alert_data.append(
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "context": alert.context,
                    "tags": alert.tags,
                    "escalation_level": alert.escalation_level,
                }
            )

        # Sort by severity and timestamp
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4,
        }

        alert_data.sort(
            key=lambda x: (
                severity_order.get(AlertSeverity(x["severity"]), 5),
                x["timestamp"],
            )
        )

        return {
            "active_alerts": alert_data,
            "count": len(alert_data),
            "critical_count": len(
                [a for a in alert_data if a["severity"] == "critical"]
            ),
            "high_count": len([a for a in alert_data if a["severity"] == "high"]),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve active alerts: {str(e)}"
        )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = Query(..., description="User acknowledging the alert"),
) -> Dict[str, Any]:
    """
    Acknowledge an alert.
    """
    try:
        success = await alert_manager.acknowledge_alert(alert_id, acknowledged_by)

        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_by": acknowledged_by,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: str = Query(..., description="User resolving the alert"),
) -> Dict[str, Any]:
    """
    Resolve an alert.
    """
    try:
        success = await alert_manager.resolve_alert(alert_id, resolved_by)

        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_by": resolved_by,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to resolve alert: {str(e)}"
        )


@router.get("/statistics")
async def get_alert_statistics() -> Dict[str, Any]:
    """
    Get alert statistics and trends.
    """
    try:
        stats = alert_manager.get_alert_statistics()

        return {
            "total_alerts": stats.get("total_alerts", 0),
            "active_alerts": stats.get("active_alerts", 0),
            "resolved_alerts": stats.get("resolved_alerts", 0),
            "by_severity": stats.get("by_severity", {}),
            "by_type": stats.get("by_type", {}),
            "average_resolution_time": stats.get("average_resolution_time", 0),
            "most_frequent_alerts": stats.get("most_frequent_alerts", []),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alert statistics: {str(e)}"
        )


@router.get("/channels")
async def get_alert_channels() -> Dict[str, Any]:
    """
    Get configured alert channels and their status.
    """
    try:
        channels = alert_manager.get_channels_status()

        return {
            "channels": channels,
            "total_channels": len(channels),
            "available_channels": len(
                [c for c in channels.values() if c.get("available", False)]
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alert channels: {str(e)}"
        )


@router.post("/test")
async def test_alerts() -> Dict[str, Any]:
    """
    Send test alerts to verify alert system functionality.
    """
    try:
        # Send a test alert
        from infrastructure.monitoring.alerts import trigger_system_resource_alert

        await trigger_system_resource_alert(
            resource_type="cpu",
            current_value=95.0,
            threshold=90.0,
            context={"test": True, "endpoint": "/api/v1/alerts/test"},
        )

        return {
            "status": "success",
            "message": "Test alert sent successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send test alert: {str(e)}"
        )


@router.get("/config")
async def get_alert_config() -> Dict[str, Any]:
    """
    Get current alert configuration.
    """
    try:
        config = alert_manager.get_configuration()

        return {
            "alert_rules": config.get("alert_rules", []),
            "suppression_rules": config.get("suppression_rules", []),
            "escalation_rules": config.get("escalation_rules", []),
            "deduplication_window": config.get("deduplication_window", 300),
            "escalation_intervals": config.get("escalation_intervals", {}),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alert configuration: {str(e)}"
        )
