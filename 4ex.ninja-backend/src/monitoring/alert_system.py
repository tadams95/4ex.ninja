"""
Alert System

Manages alerts and notifications for the 4ex.ninja monitoring dashboard.
Handles regime changes, performance alerts, and system notifications.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import redis
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert type classifications"""

    REGIME_CHANGE = "regime_change"
    STRATEGY_HEALTH = "strategy_health"
    PERFORMANCE = "performance"
    SYSTEM = "system"


@dataclass
class Alert:
    """Alert data structure"""

    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


class AlertSystem:
    """
    Real-time alert and notification system

    Manages alerts for regime changes, performance issues,
    and system notifications for the monitoring dashboard.
    """

    def __init__(self, redis_host="localhost", redis_port=6379):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, port=redis_port, decode_responses=True
            )
            self.redis_client.ping()
        except:
            logger.warning("Redis connection failed, using in-memory storage")
            self.redis_client = None

        # Configuration
        self.alerts_key = "monitoring_alerts"
        self.alert_settings_key = "alert_settings"

        # In-memory storage fallback
        self._memory_storage = {"alerts": [], "settings": {}, "last_update": None}

        # Default alert settings
        self.default_settings = {
            "regime_change_enabled": True,
            "performance_alerts_enabled": True,
            "health_alerts_enabled": True,
            "min_severity": "warning",
            "max_alerts_per_hour": 20,
        }

        self.is_initialized = False

    async def initialize(self):
        """Initialize the alert system"""
        try:
            logger.info("Initializing Alert System...")

            # Load or create alert settings
            await self._load_alert_settings()

            # Clean up old alerts
            await self._cleanup_old_alerts()

            self.is_initialized = True
            logger.info("Alert System initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Alert System: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the alert system"""
        try:
            # Test Redis connection if available
            redis_health = True
            if self.redis_client:
                try:
                    redis_health = self.redis_client.ping()
                except:
                    redis_health = False

            # Check alert processing
            recent_alerts = await self.get_recent_alerts(limit=10)
            alert_processing_healthy = True

            return {
                "status": (
                    "healthy"
                    if redis_health and alert_processing_healthy
                    else "degraded"
                ),
                "redis_connected": redis_health,
                "alert_processing_healthy": alert_processing_healthy,
                "recent_alerts_count": len(recent_alerts),
                "initialized": self.is_initialized,
            }

        except Exception as e:
            logger.error(f"Alert system health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def send_alert(self, alert_type: str, data: Dict[str, Any]) -> str:
        """Send a new alert"""
        try:
            # Check alert settings
            settings = await self._get_alert_settings()

            if not self._should_send_alert(alert_type, settings):
                logger.debug(f"Alert type {alert_type} is disabled or filtered")
                return ""

            # Create alert
            alert = self._create_alert(alert_type, data)

            # Store alert
            await self._store_alert(alert)

            logger.info(f"Alert sent: {alert.title} ({alert.severity.value})")

            return alert.id

        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return ""

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            # Get alerts from storage
            alerts_data = []
            if self.redis_client:
                try:
                    alerts_data = self.redis_client.lrange(self.alerts_key, 0, limit)
                except:
                    pass

            if not alerts_data:
                alerts_data = self._memory_storage.get("alerts", [])

            alerts = []
            # Ensure alerts_data is a list and iterable
            if isinstance(alerts_data, list):
                for alert_item in alerts_data[:limit]:
                    try:
                        if isinstance(alert_item, str):
                            alert_dict = json.loads(alert_item)
                        elif isinstance(alert_item, dict):
                            alert_dict = alert_item
                        else:
                            continue  # Skip unknown types

                        alerts.append(alert_dict)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Error parsing alert item: {e}")
                        continue

            return alerts

        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            # Get all alerts
            alerts = await self.get_recent_alerts(limit=1000)

            # Find and update the alert
            for alert_dict in alerts:
                if alert_dict.get("id") == alert_id:
                    alert_dict["acknowledged"] = True
                    alert_dict["acknowledged_at"] = datetime.now().isoformat()

                    # Update storage (simplified - in production, use more efficient method)
                    await self._update_alert_storage(alerts)

                    logger.info(f"Alert {alert_id} acknowledged")
                    return True

            logger.warning(f"Alert {alert_id} not found")
            return False

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False

    def _create_alert(self, alert_type: str, data: Dict[str, Any]) -> Alert:
        """Create an alert from type and data"""
        alert_id = str(uuid.uuid4())
        timestamp = datetime.now()

        if alert_type == "regime_change":
            return Alert(
                id=alert_id,
                alert_type=AlertType.REGIME_CHANGE,
                severity=AlertSeverity.INFO,
                title="Market Regime Change",
                message=f"Market regime changed from {data.get('old_regime', 'unknown')} to {data.get('new_regime', 'unknown')}",
                timestamp=timestamp,
                data=data,
            )
        elif alert_type == "strategy_health":
            severity = (
                AlertSeverity.CRITICAL
                if data.get("severity") == "critical"
                else AlertSeverity.WARNING
            )
            return Alert(
                id=alert_id,
                alert_type=AlertType.STRATEGY_HEALTH,
                severity=severity,
                title="Strategy Health Alert",
                message=f"Strategy health issue detected: {data.get('issues', ['Unknown issue'])[0]}",
                timestamp=timestamp,
                data=data,
            )
        elif alert_type == "performance":
            return Alert(
                id=alert_id,
                alert_type=AlertType.PERFORMANCE,
                severity=AlertSeverity.WARNING,
                title="Performance Alert",
                message=data.get("message", "Performance alert triggered"),
                timestamp=timestamp,
                data=data,
            )
        elif alert_type == "system":
            severity = (
                AlertSeverity.CRITICAL
                if data.get("critical", False)
                else AlertSeverity.WARNING
            )
            return Alert(
                id=alert_id,
                alert_type=AlertType.SYSTEM,
                severity=severity,
                title="System Alert",
                message=data.get("message", "System alert triggered"),
                timestamp=timestamp,
                data=data,
            )
        else:
            return Alert(
                id=alert_id,
                alert_type=AlertType.SYSTEM,
                severity=AlertSeverity.INFO,
                title="Unknown Alert",
                message=f"Unknown alert type: {alert_type}",
                timestamp=timestamp,
                data=data,
            )

    def _should_send_alert(self, alert_type: str, settings: Dict[str, Any]) -> bool:
        """Check if alert should be sent based on settings"""
        try:
            # Check if alert type is enabled
            if alert_type == "regime_change" and not settings.get(
                "regime_change_enabled", True
            ):
                return False
            elif alert_type == "strategy_health" and not settings.get(
                "health_alerts_enabled", True
            ):
                return False
            elif alert_type == "performance" and not settings.get(
                "performance_alerts_enabled", True
            ):
                return False

            # Check rate limiting (simplified)
            # In production, implement proper rate limiting
            return True

        except Exception as e:
            logger.error(f"Error checking alert settings: {e}")
            return True  # Default to sending alerts

    async def _store_alert(self, alert: Alert):
        """Store alert in persistent storage"""
        try:
            alert_dict = {
                "id": alert.id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "data": alert.data,
                "acknowledged": alert.acknowledged,
                "acknowledged_at": (
                    alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                ),
            }

            alert_json = json.dumps(alert_dict, default=str)

            if self.redis_client:
                try:
                    self.redis_client.lpush(self.alerts_key, alert_json)
                    self.redis_client.ltrim(
                        self.alerts_key, 0, 999
                    )  # Keep last 1000 alerts
                except:
                    pass

            # Fallback to memory storage
            if "alerts" not in self._memory_storage:
                self._memory_storage["alerts"] = []

            self._memory_storage["alerts"].insert(0, alert_dict)
            if len(self._memory_storage["alerts"]) > 1000:
                self._memory_storage["alerts"] = self._memory_storage["alerts"][:1000]

        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    async def _load_alert_settings(self):
        """Load alert settings"""
        try:
            settings = None
            if self.redis_client:
                try:
                    settings = self.redis_client.get(self.alert_settings_key)
                except:
                    pass

            if settings:
                if isinstance(settings, str):
                    self._memory_storage["settings"] = json.loads(settings)
                else:
                    self._memory_storage["settings"] = settings
            else:
                # Use default settings
                self._memory_storage["settings"] = self.default_settings.copy()
                await self._save_alert_settings()

        except Exception as e:
            logger.error(f"Error loading alert settings: {e}")
            self._memory_storage["settings"] = self.default_settings.copy()

    async def _get_alert_settings(self) -> Dict[str, Any]:
        """Get current alert settings"""
        return self._memory_storage.get("settings", self.default_settings.copy())

    async def _save_alert_settings(self):
        """Save alert settings"""
        try:
            settings = self._memory_storage.get("settings", {})
            settings_json = json.dumps(settings)

            if self.redis_client:
                try:
                    self.redis_client.set(self.alert_settings_key, settings_json)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error saving alert settings: {e}")

    async def _update_alert_storage(self, alerts: List[Dict[str, Any]]):
        """Update alert storage (simplified implementation)"""
        try:
            # Clear existing alerts and store updated list
            if self.redis_client:
                try:
                    self.redis_client.delete(self.alerts_key)
                    for alert in alerts:
                        alert_json = json.dumps(alert, default=str)
                        self.redis_client.rpush(self.alerts_key, alert_json)
                except:
                    pass

            # Update memory storage
            self._memory_storage["alerts"] = alerts

        except Exception as e:
            logger.error(f"Error updating alert storage: {e}")

    async def _cleanup_old_alerts(self):
        """Clean up alerts older than 30 days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=30)
            alerts = await self.get_recent_alerts(limit=1000)

            # Filter out old alerts
            recent_alerts = []
            for alert in alerts:
                alert_time = datetime.fromisoformat(alert["timestamp"])
                if alert_time > cutoff_time:
                    recent_alerts.append(alert)

            # Update storage with filtered alerts
            if len(recent_alerts) != len(alerts):
                await self._update_alert_storage(recent_alerts)
                logger.info(f"Cleaned up {len(alerts) - len(recent_alerts)} old alerts")

        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up Alert System...")
            # Close Redis connection if needed
            if self.redis_client:
                try:
                    self.redis_client.close()
                except:
                    pass

        except Exception as e:
            logger.error(f"Error during Alert System cleanup: {e}")
