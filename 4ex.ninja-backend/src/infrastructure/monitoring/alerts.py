"""
Critical System Alerting Module

This module provides comprehensive alerting for critical system failures,
including signal processing failures, database connectivity issues, and external API downtime.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from abc import ABC, abstractmethod
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts that can be triggered."""

    SIGNAL_PROCESSING_FAILURE = "signal_processing_failure"
    DATABASE_CONNECTIVITY = "database_connectivity"
    EXTERNAL_API_DOWNTIME = "external_api_downtime"
    SYSTEM_RESOURCE_EXHAUSTION = "system_resource_exhaustion"
    AUTHENTICATION_FAILURE = "authentication_failure"
    DATA_CORRUPTION = "data_corruption"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"


class AlertSeverity(Enum):
    """Alert severity levels."""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action required within 1 hour
    MEDIUM = "medium"  # Action required within 4 hours
    LOW = "low"  # Action required within 24 hours
    INFO = "info"  # Informational only


class AlertStatus(Enum):
    """Alert status states."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Represents a system alert."""

    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    alert_id: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalation_level: int = 0

    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = f"{self.alert_type.value}_{int(self.timestamp.timestamp())}"


class AlertChannel(ABC):
    """Abstract base class for alert notification channels."""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert through this channel."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the channel is available."""
        pass


class LogAlertChannel(AlertChannel):
    """Alert channel that sends alerts to the logging system."""

    def __init__(self, logger_name: str = "alerts"):
        self.logger = logging.getLogger(logger_name)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to logs."""
        try:
            log_level = {
                AlertSeverity.CRITICAL: logging.CRITICAL,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.INFO: logging.INFO,
            }.get(alert.severity, logging.INFO)

            message = (
                f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}"
            )
            if alert.context:
                message += f" | Context: {json.dumps(alert.context)}"

            self.logger.log(log_level, message)
            return True

        except Exception as e:
            logger.error(f"Failed to send alert to logs: {str(e)}")
            return False

    def is_available(self) -> bool:
        """Log channel is always available."""
        return True


class EmailAlertChannel(AlertChannel):
    """Alert channel that sends alerts via email."""

    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        self.enabled = smtp_config.get("enabled", False)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        if not self.enabled:
            logger.debug("Email alerts disabled")
            return False

        try:
            import smtplib
            import os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Get SMTP configuration from environment
            smtp_host = os.getenv("SMTP_HOST", self.smtp_config.get("host", ""))
            smtp_port = int(os.getenv("SMTP_PORT", str(self.smtp_config.get("port", 587))))
            smtp_username = os.getenv("SMTP_USERNAME", self.smtp_config.get("username", ""))
            smtp_password = os.getenv("SMTP_PASSWORD", self.smtp_config.get("password", ""))
            from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username)
            to_emails = os.getenv("ALERT_TO_EMAILS", "").split(",")

            if not all([smtp_host, smtp_port, smtp_username, smtp_password, to_emails[0]]):
                logger.warning("Email configuration incomplete, skipping email alert")
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create email body
            body = f"""
Alert Details:
- Type: {alert.alert_type.value}
- Severity: {alert.severity.value}
- Time: {alert.timestamp.isoformat()}
- Message: {alert.message}

Context:
{alert.context}

Alert ID: {alert.alert_id}
Tags: {', '.join(alert.tags)}
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

            logger.info(f"Email alert sent successfully: {alert.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False

    def is_available(self) -> bool:
        """Check if email configuration is available."""
        return self.enabled and all(
            key in self.smtp_config for key in ["host", "port", "username", "password"]
        )


class WebhookAlertChannel(AlertChannel):
    """Alert channel that sends alerts to webhooks (Discord, Slack, etc.)."""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.enabled = bool(webhook_url)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to webhook."""
        if not self.enabled:
            logger.debug("Webhook alerts disabled")
            return False

        try:
            import aiohttp
            import os

            webhook_url = os.getenv("DISCORD_WEBHOOK_URL", self.webhook_url)
            if not webhook_url:
                logger.warning("No webhook URL configured")
                return False

            # Create Discord-compatible payload
            severity_colors = {
                AlertSeverity.CRITICAL: 16711680,  # Red
                AlertSeverity.HIGH: 16753920,      # Orange
                AlertSeverity.MEDIUM: 16776960,    # Yellow
                AlertSeverity.LOW: 65535,          # Cyan
                AlertSeverity.INFO: 5763719,       # Blue
            }

            payload = {
                "embeds": [
                    {
                        "title": f"🚨 {alert.title}",
                        "description": alert.message,
                        "color": severity_colors.get(alert.severity, 5763719),
                        "fields": [
                            {
                                "name": "Severity",
                                "value": alert.severity.value.upper(),
                                "inline": True,
                            },
                            {
                                "name": "Type",
                                "value": alert.alert_type.value.replace("_", " ").title(),
                                "inline": True,
                            },
                            {
                                "name": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": f"Alert ID: {alert.alert_id}",
                        },
                    }
                ]
            }

            # Add context if available
            if alert.context:
                context_text = "\n".join([f"**{k}**: {v}" for k, v in alert.context.items()])
                payload["embeds"][0]["fields"].append({
                    "name": "Context",
                    "value": context_text[:1000],  # Discord field limit
                    "inline": False,
                })

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 204:  # Discord success response
                        logger.info(f"Webhook alert sent successfully: {alert.title}")
                        return True
                    else:
                        logger.warning(f"Webhook responded with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")
            return False

    def is_available(self) -> bool:
        """Check if webhook is available."""
        return self.enabled


class AlertManager:
    """Manages system alerts including routing, escalation, and deduplication."""

    def __init__(self):
        self.channels: Dict[str, AlertChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self.suppression_rules: List[Dict[str, Any]] = []
        self.escalation_rules: List[Dict[str, Any]] = []

        # Alert thresholds and timing
        self.deduplication_window = 300  # 5 minutes
        self.escalation_intervals = {
            AlertSeverity.CRITICAL: 300,  # 5 minutes
            AlertSeverity.HIGH: 900,  # 15 minutes
            AlertSeverity.MEDIUM: 3600,  # 1 hour
            AlertSeverity.LOW: 14400,  # 4 hours
            AlertSeverity.INFO: 86400,  # 24 hours
        }

        # Setup default channels
        self._setup_default_channels()
        self._setup_default_rules()

    def _setup_default_channels(self):
        """Setup default alert channels."""
        import os
        
        # Always available log channel
        self.add_channel("logs", LogAlertChannel())

        # Email channel (enabled if environment variables are set)
        email_enabled = bool(
            os.getenv("SMTP_HOST") and 
            os.getenv("SMTP_USERNAME") and 
            os.getenv("SMTP_PASSWORD")
        )
        email_config = {
            "enabled": email_enabled,
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
        }
        self.add_channel("email", EmailAlertChannel(email_config))

        # Webhook channel (enabled if Discord webhook URL is set)
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.add_channel("webhook", WebhookAlertChannel(webhook_url))

    def _setup_default_rules(self):
        """Setup default alert routing rules."""
        # Critical alerts go to all channels
        self.add_alert_rule(
            {
                "severity": [AlertSeverity.CRITICAL],
                "channels": ["logs", "email", "webhook"],
                "immediate": True,
            }
        )

        # High severity alerts go to logs and email
        self.add_alert_rule(
            {
                "severity": [AlertSeverity.HIGH],
                "channels": ["logs", "email"],
                "immediate": True,
            }
        )

        # Medium and low severity alerts go to logs only
        self.add_alert_rule(
            {
                "severity": [
                    AlertSeverity.MEDIUM,
                    AlertSeverity.LOW,
                    AlertSeverity.INFO,
                ],
                "channels": ["logs"],
                "immediate": False,
            }
        )

        # Suppression rule for duplicate alerts
        self.add_suppression_rule(
            {
                "alert_type": "any",
                "deduplication_window": self.deduplication_window,
                "max_occurrences": 1,
            }
        )

    def add_channel(self, name: str, channel: AlertChannel):
        """Add an alert channel."""
        self.channels[name] = channel
        logger.info(f"Alert channel '{name}' added")

    def remove_channel(self, name: str):
        """Remove an alert channel."""
        if name in self.channels:
            del self.channels[name]
            logger.info(f"Alert channel '{name}' removed")

    def add_alert_rule(self, rule: Dict[str, Any]):
        """Add an alert routing rule."""
        self.alert_rules.append(rule)

    def add_suppression_rule(self, rule: Dict[str, Any]):
        """Add an alert suppression rule."""
        self.suppression_rules.append(rule)

    def add_escalation_rule(self, rule: Dict[str, Any]):
        """Add an alert escalation rule."""
        self.escalation_rules.append(rule)

    async def trigger_alert(self, alert: Alert) -> bool:
        """Trigger a new alert."""
        logger.info(f"Triggering alert: {alert.title}")

        # Check if alert should be suppressed
        if self._should_suppress_alert(alert):
            logger.info(f"Alert suppressed: {alert.alert_id}")
            return False

        # Add to active alerts
        if alert.alert_id:
            self.active_alerts[alert.alert_id] = alert

        # Add to history
        self.alert_history.append(alert)

        # Route alert to appropriate channels
        success = await self._route_alert(alert)

        # Schedule escalation if needed
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            asyncio.create_task(self._schedule_escalation(alert))

        return success

    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed based on suppression rules."""
        for rule in self.suppression_rules:
            if self._matches_suppression_rule(alert, rule):
                return True
        return False

    def _matches_suppression_rule(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if alert matches a suppression rule."""
        # Check for similar alerts in the deduplication window
        window_start = alert.timestamp.timestamp() - rule.get(
            "deduplication_window", 300
        )

        similar_alerts = [
            a
            for a in self.alert_history
            if (
                a.alert_type == alert.alert_type
                and a.timestamp.timestamp() > window_start
                and a.status == AlertStatus.ACTIVE
            )
        ]

        max_occurrences = rule.get("max_occurrences", 1)
        return len(similar_alerts) >= max_occurrences

    async def _route_alert(self, alert: Alert) -> bool:
        """Route alert to appropriate channels based on rules."""
        matching_channels = set()

        # Find matching rules
        for rule in self.alert_rules:
            if self._matches_alert_rule(alert, rule):
                channels = rule.get("channels", [])
                matching_channels.update(channels)

        # Send to matching channels
        success_count = 0
        total_channels = len(matching_channels)

        for channel_name in matching_channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]

                if channel.is_available():
                    try:
                        if await channel.send_alert(alert):
                            success_count += 1
                        else:
                            logger.warning(
                                f"Failed to send alert to channel: {channel_name}"
                            )
                    except Exception as e:
                        logger.error(f"Error sending alert to {channel_name}: {str(e)}")
                else:
                    logger.warning(f"Channel not available: {channel_name}")
            else:
                logger.warning(f"Unknown channel: {channel_name}")

        return success_count > 0 if total_channels > 0 else False

    def _matches_alert_rule(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if alert matches a routing rule."""
        # Check severity
        if "severity" in rule:
            if alert.severity not in rule["severity"]:
                return False

        # Check alert type
        if "alert_type" in rule:
            if alert.alert_type not in rule["alert_type"]:
                return False

        # Check tags
        if "tags" in rule:
            required_tags = set(rule["tags"])
            alert_tags = set(alert.tags)
            if not required_tags.issubset(alert_tags):
                return False

        return True

    async def _schedule_escalation(self, alert: Alert):
        """Schedule alert escalation if not acknowledged."""
        if not alert.alert_id:
            return

        escalation_interval = self.escalation_intervals.get(alert.severity, 3600)

        await asyncio.sleep(escalation_interval)

        # Check if alert is still active and not acknowledged
        current_alert = self.active_alerts.get(alert.alert_id)
        if (
            current_alert
            and current_alert.status == AlertStatus.ACTIVE
            and not current_alert.acknowledged_by
        ):

            # Escalate alert
            current_alert.escalation_level += 1
            escalated_alert = Alert(
                alert_type=current_alert.alert_type,
                severity=current_alert.severity,
                title=f"ESCALATED: {current_alert.title}",
                message=f"Alert escalated (level {current_alert.escalation_level}): {current_alert.message}",
                timestamp=datetime.now(timezone.utc),
                context=current_alert.context,
                escalation_level=current_alert.escalation_level,
            )

            await self.trigger_alert(escalated_alert)

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now(timezone.utc)

            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True

        return False

    async def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)

            # Remove from active alerts
            del self.active_alerts[alert_id]

            logger.info(f"Alert resolved: {alert_id} by {resolved_by or 'system'}")
            return True

        return False

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Alert]:
        """Get alerts with optional filtering."""
        alerts = self.alert_history.copy()

        # Filter by status
        if status:
            alerts = [a for a in alerts if a.status == status]

        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        return alerts[offset : offset + limit]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        resolved_count = len([a for a in self.alert_history if a.status == AlertStatus.RESOLVED])

        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by type
        type_counts = {}
        for alert in self.alert_history:
            alert_type = alert.alert_type.value
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

        # Count by status
        status_counts = {}
        for alert in self.alert_history:
            status = alert.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate average resolution time
        resolved_alerts = [
            a for a in self.alert_history 
            if a.resolved_at is not None and a.timestamp is not None
        ]
        avg_resolution_time = 0
        if resolved_alerts:
            total_resolution_time = 0
            for alert in resolved_alerts:
                if alert.resolved_at and alert.timestamp:
                    total_resolution_time += (alert.resolved_at - alert.timestamp).total_seconds()
            avg_resolution_time = total_resolution_time / len(resolved_alerts) if resolved_alerts else 0

        # Most frequent alert types
        most_frequent = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_count,
            "resolved_alerts": resolved_count,
            "by_severity": severity_counts,
            "by_type": type_counts,
            "by_status": status_counts,
            "average_resolution_time": avg_resolution_time,
            "most_frequent_alerts": most_frequent,
            "alerts_by_severity": severity_counts,  # Legacy compatibility
            "alerts_by_type": type_counts,  # Legacy compatibility
            "alerts_by_status": status_counts,  # Legacy compatibility
            "available_channels": {
                name: channel.is_available() for name, channel in self.channels.items()
            },
        }

    def get_channels_status(self) -> Dict[str, Any]:
        """Get status of all alert channels."""
        channels_info = {}
        for name, channel in self.channels.items():
            channels_info[name] = {
                "name": name,
                "type": channel.__class__.__name__,
                "available": channel.is_available(),
            }
        return channels_info

    def get_configuration(self) -> Dict[str, Any]:
        """Get current alert configuration."""
        return {
            "alert_rules": self.alert_rules.copy(),
            "suppression_rules": self.suppression_rules.copy(),
            "escalation_rules": self.escalation_rules.copy(),
            "deduplication_window": self.deduplication_window,
            "escalation_intervals": {
                severity.value: interval
                for severity, interval in self.escalation_intervals.items()
            },
        }


# Global alert manager instance
alert_manager = AlertManager()


# Convenience functions for triggering specific types of alerts


async def trigger_system_resource_alert(
    resource_type: str,
    current_value: float,
    threshold: float,
    context: Optional[Dict[str, Any]] = None,
    severity: AlertSeverity = AlertSeverity.HIGH,
):
    """Trigger a system resource exhaustion alert."""
    alert = Alert(
        alert_type=AlertType.SYSTEM_RESOURCE_EXHAUSTION,
        severity=severity,
        title=f"System Resource Alert: {resource_type.upper()}",
        message=f"{resource_type.upper()} usage is {current_value:.1f}%, exceeding threshold of {threshold:.1f}%",
        timestamp=datetime.now(timezone.utc),
        context=context or {},
        tags=["system_resources", resource_type.lower()],
    )

    return await alert_manager.trigger_alert(alert)


async def alert_signal_processing_failure(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: AlertSeverity = AlertSeverity.HIGH,
):
    """Trigger a signal processing failure alert."""
    alert = Alert(
        alert_type=AlertType.SIGNAL_PROCESSING_FAILURE,
        severity=severity,
        title="Signal Processing Failure",
        message=message,
        timestamp=datetime.now(timezone.utc),
        context=context or {},
        tags=["signal_processing", "trading"],
    )

    return await alert_manager.trigger_alert(alert)


async def alert_database_connectivity(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: AlertSeverity = AlertSeverity.CRITICAL,
):
    """Trigger a database connectivity alert."""
    alert = Alert(
        alert_type=AlertType.DATABASE_CONNECTIVITY,
        severity=severity,
        title="Database Connectivity Issue",
        message=message,
        timestamp=datetime.now(timezone.utc),
        context=context or {},
        tags=["database", "connectivity"],
    )

    return await alert_manager.trigger_alert(alert)


async def alert_external_api_downtime(
    api_name: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: AlertSeverity = AlertSeverity.HIGH,
):
    """Trigger an external API downtime alert."""
    alert = Alert(
        alert_type=AlertType.EXTERNAL_API_DOWNTIME,
        severity=severity,
        title=f"External API Downtime: {api_name}",
        message=message,
        timestamp=datetime.now(timezone.utc),
        context=context or {},
        tags=["external_api", "downtime", api_name.lower()],
    )

    return await alert_manager.trigger_alert(alert)


async def alert_circuit_breaker_triggered(
    service_name: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
):
    """Trigger a circuit breaker alert."""
    alert = Alert(
        alert_type=AlertType.CIRCUIT_BREAKER_TRIGGERED,
        severity=severity,
        title=f"Circuit Breaker Triggered: {service_name}",
        message=message,
        timestamp=datetime.now(timezone.utc),
        context=context or {},
        tags=["circuit_breaker", "resilience", service_name.lower()],
    )

    return await alert_manager.trigger_alert(alert)


# Alert decorators for automatic error detection


def alert_on_failure(
    alert_type: AlertType,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    title: Optional[str] = None,
):
    """Decorator to automatically trigger alerts on function failures."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                alert_title = title or f"Function Failure: {func.__name__}"
                await alert_manager.trigger_alert(
                    Alert(
                        alert_type=alert_type,
                        severity=severity,
                        title=alert_title,
                        message=f"Function {func.__name__} failed: {str(e)}",
                        timestamp=datetime.now(timezone.utc),
                        context={
                            "function": func.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs),
                            "exception": str(e),
                        },
                    )
                )
                raise

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                alert_title = title or f"Function Failure: {func.__name__}"
                # For sync functions, we can't await, so we log the alert
                logger.error(f"ALERT: {alert_title} - {str(e)}")
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
