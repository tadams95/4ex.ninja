"""
Integration module for AsyncNotificationService

This module provides easy integration of the AsyncNotificationService
with existing code and replaces blocking Discord calls.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.entities.signal import Signal
from infrastructure.monitoring.alerts import Alert
from infrastructure.services.async_notification_service import (
    get_async_notification_service,
    AsyncNotificationService,
    NotificationPriority,
)
from infrastructure.external_services.discord_service import UserTier

logger = logging.getLogger(__name__)


class NotificationIntegration:
    """
    Integration layer for async notifications.

    This service provides a simple interface for sending notifications
    asynchronously and manages the lifecycle of the notification service.
    """

    def __init__(self):
        self.async_service: Optional[AsyncNotificationService] = None
        self._startup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the async notification service."""
        if self.async_service is not None:
            logger.warning("NotificationIntegration already initialized")
            return

        try:
            self.async_service = get_async_notification_service()
            await self.async_service.start()
            logger.info("AsyncNotificationService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AsyncNotificationService: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown the async notification service."""
        if self.async_service is not None:
            await self.async_service.stop()
            self.async_service = None
            logger.info("AsyncNotificationService shutdown completed")

    async def send_signal_notification(
        self,
        signal: Signal,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_tier: UserTier = UserTier.FREE,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a signal notification asynchronously.

        Args:
            signal: Trading signal to send
            priority: Notification priority
            user_tier: User tier for channel routing
            additional_context: Additional context data

        Returns:
            bool: True if queued successfully
        """
        if self.async_service is None:
            logger.error("AsyncNotificationService not initialized")
            return False

        try:
            # Determine priority based on signal confidence if not specified
            if priority == NotificationPriority.NORMAL and signal.confidence_score:
                if signal.confidence_score >= 0.9:
                    priority = NotificationPriority.URGENT
                elif signal.confidence_score >= 0.8:
                    priority = NotificationPriority.HIGH

            success = await self.async_service.queue_notification(
                signal_data=signal,
                priority=priority,
                user_tier=user_tier,
                additional_context=additional_context,
            )

            if success:
                logger.debug(f"Signal notification queued: {signal.signal_id}")
            else:
                logger.warning(
                    f"Failed to queue signal notification: {signal.signal_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error sending signal notification: {str(e)}")
            return False

    async def send_alert_notification(
        self, alert: Alert, priority: Optional[NotificationPriority] = None
    ) -> bool:
        """
        Send an alert notification asynchronously.

        Args:
            alert: System alert to send
            priority: Notification priority (auto-determined if None)

        Returns:
            bool: True if queued successfully
        """
        if self.async_service is None:
            logger.error("AsyncNotificationService not initialized")
            return False

        try:
            # Auto-determine priority based on alert severity if not specified
            if priority is None:
                from infrastructure.monitoring.alerts import AlertSeverity

                severity_priority_map = {
                    AlertSeverity.CRITICAL: NotificationPriority.URGENT,
                    AlertSeverity.HIGH: NotificationPriority.HIGH,
                    AlertSeverity.MEDIUM: NotificationPriority.NORMAL,
                    AlertSeverity.LOW: NotificationPriority.LOW,
                    AlertSeverity.INFO: NotificationPriority.LOW,
                }
                priority = severity_priority_map.get(
                    alert.severity, NotificationPriority.NORMAL
                )

            success = await self.async_service.queue_notification(
                signal_data=alert,
                priority=priority,
                user_tier=UserTier.ADMIN,  # Alerts typically go to admin channels
                additional_context=None,
            )

            if success:
                logger.debug(f"Alert notification queued: {alert.alert_id}")
            else:
                logger.warning(f"Failed to queue alert notification: {alert.alert_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get notification service metrics."""
        if self.async_service is None:
            return {"error": "Service not initialized"}

        return self.async_service.get_metrics()

    def is_healthy(self) -> bool:
        """Check if the notification service is healthy."""
        if self.async_service is None:
            return False

        metrics = self.async_service.get_metrics()

        # Check various health indicators
        queue_depth = metrics.get("queue_depth", 0)
        circuit_breaker_state = metrics.get("circuit_breaker_state", "open")
        running = metrics.get("running", False)

        # Service is healthy if:
        # 1. It's running
        # 2. Queue depth is not excessively high
        # 3. Circuit breaker is not permanently open
        return (
            running
            and queue_depth < 500  # Arbitrary threshold
            and circuit_breaker_state != "open"
        )


# Global integration instance
_notification_integration: Optional[NotificationIntegration] = None


def get_notification_integration() -> NotificationIntegration:
    """Get or create the global notification integration."""
    global _notification_integration
    if _notification_integration is None:
        _notification_integration = NotificationIntegration()
    return _notification_integration


async def initialize_async_notifications():
    """Initialize async notifications system."""
    integration = get_notification_integration()
    await integration.initialize()


async def cleanup_async_notifications():
    """Cleanup async notifications system."""
    global _notification_integration
    if _notification_integration:
        await _notification_integration.shutdown()
        _notification_integration = None


# Convenience functions for easy integration
async def send_signal_async(
    signal: Signal,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    user_tier: UserTier = UserTier.FREE,
    additional_context: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send a signal notification asynchronously.

    This function provides a simple interface for sending signal notifications
    without needing to manage the integration service directly.
    """
    integration = get_notification_integration()
    return await integration.send_signal_notification(
        signal=signal,
        priority=priority,
        user_tier=user_tier,
        additional_context=additional_context,
    )


async def send_alert_async(
    alert: Alert, priority: Optional[NotificationPriority] = None
) -> bool:
    """
    Send an alert notification asynchronously.

    This function provides a simple interface for sending alert notifications
    without needing to manage the integration service directly.
    """
    integration = get_notification_integration()
    return await integration.send_alert_notification(alert=alert, priority=priority)


def ensure_async_notifications_started():
    """
    Ensure async notifications are started.

    This function can be called from synchronous code to ensure
    the notification system is initialized. It creates a background
    task if needed.
    """
    integration = get_notification_integration()

    if integration.async_service is None:
        # Create a background task to initialize the service
        def start_service():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create a task
                    asyncio.create_task(integration.initialize())
                else:
                    # If no loop is running, run it
                    asyncio.run(integration.initialize())
            except Exception as e:
                logger.error(f"Failed to start async notifications: {str(e)}")

        # Try to start in the current event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(integration.initialize())
            else:
                # No event loop, create one
                import threading

                thread = threading.Thread(target=start_service)
                thread.daemon = True
                thread.start()
        except RuntimeError:
            # No event loop in current thread
            import threading

            thread = threading.Thread(target=start_service)
            thread.daemon = True
            thread.start()


# Export main components
__all__ = [
    "NotificationIntegration",
    "get_notification_integration",
    "initialize_async_notifications",
    "cleanup_async_notifications",
    "send_signal_async",
    "send_alert_async",
    "ensure_async_notifications_started",
    "NotificationPriority",
    "UserTier",
]
