"""
Signal Notification Service for 4ex.ninja

This service handles real-time notification delivery for trading signals,
integrating with Discord, email, and other notification channels.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

from core.entities.signal import Signal
from infrastructure.monitoring.alerts import alert_manager
from infrastructure.monitoring.discord_alerts import send_signal_to_discord
from infrastructure.external_services.discord_service import UserTier

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels."""

    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"  # Future implementation
    PUSH = "push"  # Future implementation


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SignalNotificationService:
    """
    Comprehensive signal notification service.

    Handles routing and delivery of trading signal notifications
    across multiple channels with priority-based routing.
    """

    def __init__(self):
        self.enabled_channels = self._get_enabled_channels()
        self.notification_queue = asyncio.Queue()
        self.processing = False

    def _get_enabled_channels(self) -> List[NotificationChannel]:
        """Determine which notification channels are available."""
        import os

        enabled = []

        # Check Discord webhooks
        discord_webhooks = [
            "DISCORD_WEBHOOK_SIGNALS_FREE",
            "DISCORD_WEBHOOK_SIGNALS_PREMIUM",
            "DISCORD_WEBHOOK_ALERTS_CRITICAL",
        ]

        if any(os.getenv(webhook) for webhook in discord_webhooks):
            enabled.append(NotificationChannel.DISCORD)

        # Check email configuration
        if (
            os.getenv("SMTP_HOST")
            and os.getenv("SMTP_USERNAME")
            and os.getenv("SMTP_PASSWORD")
        ):
            enabled.append(NotificationChannel.EMAIL)

        # Check general webhook
        if os.getenv("DISCORD_WEBHOOK_URL"):
            enabled.append(NotificationChannel.WEBHOOK)

        logger.info(f"Enabled notification channels: {[ch.value for ch in enabled]}")
        return enabled

    async def notify_signal_generated(
        self,
        signal: Signal,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_tier: UserTier = UserTier.FREE,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notifications for a newly generated signal.

        Args:
            signal: The trading signal to notify about
            priority: Notification priority level
            user_tier: User subscription tier
            additional_context: Additional context information

        Returns:
            Dict[str, bool]: Success status for each channel
        """
        results = {}

        try:
            # Enhanced context with signal metadata
            context = {
                "signal_type": "new_signal",
                "priority": priority.value,
                "user_tier": user_tier.value,
                "confidence_level": self._get_confidence_level(signal.confidence_score),
                "market_session": self._get_market_session(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                **(additional_context or {}),
            }

            # Send to Discord if enabled
            if NotificationChannel.DISCORD in self.enabled_channels:
                try:
                    discord_success = await send_signal_to_discord(
                        signal=signal,
                        alert_type="signal_generated",
                        additional_context=context,
                    )
                    results["discord"] = discord_success

                    if discord_success:
                        logger.info(
                            f"Signal {signal.signal_id} sent to Discord successfully"
                        )
                    else:
                        logger.warning(
                            f"Failed to send signal {signal.signal_id} to Discord"
                        )

                except Exception as e:
                    logger.error(
                        f"Discord notification error for signal {signal.signal_id}: {str(e)}"
                    )
                    results["discord"] = False

            # Send to Email if enabled and priority is high enough
            if NotificationChannel.EMAIL in self.enabled_channels and priority in [
                NotificationPriority.HIGH,
                NotificationPriority.URGENT,
            ]:
                try:
                    email_success = await self._send_email_notification(signal, context)
                    results["email"] = email_success
                except Exception as e:
                    logger.error(
                        f"Email notification error for signal {signal.signal_id}: {str(e)}"
                    )
                    results["email"] = False

            # Send to general webhook if enabled
            if NotificationChannel.WEBHOOK in self.enabled_channels:
                try:
                    webhook_success = await self._send_webhook_notification(
                        signal, context
                    )
                    results["webhook"] = webhook_success
                except Exception as e:
                    logger.error(
                        f"Webhook notification error for signal {signal.signal_id}: {str(e)}"
                    )
                    results["webhook"] = False

            # Log overall success
            successful_channels = sum(1 for success in results.values() if success)
            total_channels = len(results)

            if successful_channels == total_channels and total_channels > 0:
                logger.info(
                    f"Signal {signal.signal_id} sent to all {total_channels} channels successfully"
                )
            elif successful_channels > 0:
                logger.warning(
                    f"Signal {signal.signal_id} sent to {successful_channels}/{total_channels} channels"
                )
            else:
                logger.error(
                    f"Failed to send signal {signal.signal_id} to any notification channels"
                )

            return results

        except Exception as e:
            logger.error(f"Signal notification error: {str(e)}")
            return {}

    async def notify_signal_updated(
        self,
        signal: Signal,
        update_type: str,
        previous_values: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notifications for signal updates (price changes, status changes, etc.).

        Args:
            signal: The updated signal
            update_type: Type of update (price_change, status_change, etc.)
            previous_values: Previous values before update
            additional_context: Additional context

        Returns:
            Dict[str, bool]: Success status for each channel
        """
        try:
            context = {
                "signal_type": "signal_update",
                "update_type": update_type,
                "previous_values": previous_values,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                **(additional_context or {}),
            }

            # Only send updates for significant changes to avoid spam
            if self._is_significant_update(update_type, signal, previous_values):
                return await self.notify_signal_generated(
                    signal=signal,
                    priority=NotificationPriority.LOW,
                    additional_context=context,
                )
            else:
                logger.debug(
                    f"Skipping notification for minor signal update: {signal.signal_id}"
                )
                return {}

        except Exception as e:
            logger.error(f"Signal update notification error: {str(e)}")
            return {}

    async def notify_signal_filled(
        self,
        signal: Signal,
        fill_price: float,
        fill_time: datetime,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notifications when a signal is filled/executed.

        Args:
            signal: The filled signal
            fill_price: Actual fill price
            fill_time: Time of fill
            additional_context: Additional context

        Returns:
            Dict[str, bool]: Success status for each channel
        """
        try:
            context = {
                "signal_type": "signal_filled",
                "fill_price": fill_price,
                "fill_time": fill_time.isoformat(),
                "slippage": abs(float(signal.entry_price) - fill_price),
                **(additional_context or {}),
            }

            return await self.notify_signal_generated(
                signal=signal,
                priority=NotificationPriority.HIGH,
                additional_context=context,
            )

        except Exception as e:
            logger.error(f"Signal fill notification error: {str(e)}")
            return {}

    async def start_notification_processor(self):
        """Start the background notification processor."""
        if self.processing:
            logger.warning("Notification processor already running")
            return

        self.processing = True
        logger.info("Starting signal notification processor")

        try:
            while self.processing:
                try:
                    # Process notifications from queue with timeout
                    notification_task = await asyncio.wait_for(
                        self.notification_queue.get(), timeout=1.0
                    )

                    await self._process_notification_task(notification_task)
                    self.notification_queue.task_done()

                except asyncio.TimeoutError:
                    # No notifications in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Notification processor error: {str(e)}")

        except Exception as e:
            logger.error(f"Notification processor fatal error: {str(e)}")
        finally:
            self.processing = False
            logger.info("Signal notification processor stopped")

    async def stop_notification_processor(self):
        """Stop the background notification processor."""
        self.processing = False
        logger.info("Stopping signal notification processor")

    def _get_confidence_level(self, confidence_score: Optional[float]) -> str:
        """Get human-readable confidence level."""
        if not confidence_score:
            return "Unknown"

        if confidence_score >= 0.9:
            return "Very High"
        elif confidence_score >= 0.8:
            return "High"
        elif confidence_score >= 0.7:
            return "Medium"
        elif confidence_score >= 0.6:
            return "Low"
        else:
            return "Very Low"

    def _get_market_session(self) -> str:
        """Determine current market session."""
        import pytz

        now_utc = datetime.now(timezone.utc)

        # Convert to major market timezones
        london_time = now_utc.astimezone(pytz.timezone("Europe/London"))
        new_york_time = now_utc.astimezone(pytz.timezone("America/New_York"))
        tokyo_time = now_utc.astimezone(pytz.timezone("Asia/Tokyo"))
        sydney_time = now_utc.astimezone(pytz.timezone("Australia/Sydney"))

        london_hour = london_time.hour
        new_york_hour = new_york_time.hour
        tokyo_hour = tokyo_time.hour
        sydney_hour = sydney_time.hour

        # Determine active session
        if 0 <= sydney_hour < 7:
            return "Sydney Open"
        elif 0 <= tokyo_hour < 9:
            return "Tokyo Open"
        elif 8 <= london_hour < 17:
            return "London Open"
        elif 8 <= new_york_hour < 17:
            return "New York Open"
        else:
            return "After Hours"

    def _is_significant_update(
        self, update_type: str, signal: Signal, previous_values: Dict[str, Any]
    ) -> bool:
        """Determine if an update is significant enough to notify about."""
        # Always notify for status changes
        if update_type == "status_change":
            return True

        # Notify for significant price changes (>1% from entry)
        if update_type == "price_change":
            if signal.current_price and signal.entry_price:
                price_change_pct = (
                    abs(
                        (float(signal.current_price) - float(signal.entry_price))
                        / float(signal.entry_price)
                    )
                    * 100
                )
                return price_change_pct > 1.0

        # Notify for confidence score changes >10%
        if update_type == "confidence_change":
            if signal.confidence_score and previous_values.get("confidence_score"):
                confidence_change = abs(
                    signal.confidence_score - previous_values["confidence_score"]
                )
                return confidence_change > 0.1

        return False

    async def _send_email_notification(
        self, signal: Signal, context: Dict[str, Any]
    ) -> bool:
        """Send email notification for signal."""
        try:
            # This would integrate with the existing email alert system
            # For now, we'll create a basic implementation

            from infrastructure.monitoring.alerts import Alert, AlertSeverity, AlertType

            alert = Alert(
                alert_type=AlertType.SIGNAL_PROCESSING_FAILURE,  # We can add a new type for signals
                severity=AlertSeverity.INFO,
                title=f"Trading Signal: {signal.signal_type.value} {signal.pair}",
                message=f"New {signal.signal_type.value} signal generated for {signal.pair} at {signal.entry_price}",
                timestamp=datetime.now(timezone.utc),
                context=context,
            )

            # Send through existing alert system
            return await alert_manager.trigger_alert(alert)

        except Exception as e:
            logger.error(f"Email notification error: {str(e)}")
            return False

    async def _send_webhook_notification(
        self, signal: Signal, context: Dict[str, Any]
    ) -> bool:
        """Send webhook notification for signal."""
        try:
            # This would use the existing webhook infrastructure
            import aiohttp
            import os

            webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
            if not webhook_url:
                return False

            payload = {
                "content": f"🚨 New {signal.signal_type.value} signal: {signal.pair} at {signal.entry_price}",
                "embeds": [
                    {
                        "title": f"{signal.signal_type.value} Signal - {signal.pair}",
                        "description": (
                            f"Confidence: {signal.confidence_score:.1%}"
                            if signal.confidence_score
                            else "New signal generated"
                        ),
                        "color": (
                            0x00FF00 if signal.signal_type.value == "BUY" else 0xFF0000
                        ),
                        "fields": [
                            {
                                "name": "Entry Price",
                                "value": str(signal.entry_price),
                                "inline": True,
                            },
                            {
                                "name": "Timeframe",
                                "value": signal.timeframe,
                                "inline": True,
                            },
                            {
                                "name": "Timestamp",
                                "value": signal.timestamp.isoformat(),
                                "inline": False,
                            },
                        ],
                    }
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status == 204

        except Exception as e:
            logger.error(f"Webhook notification error: {str(e)}")
            return False

    async def _process_notification_task(self, task: Dict[str, Any]):
        """Process a notification task from the queue."""
        try:
            task_type = task.get("type")

            if task_type == "signal_generated":
                await self.notify_signal_generated(**task.get("params", {}))
            elif task_type == "signal_updated":
                await self.notify_signal_updated(**task.get("params", {}))
            elif task_type == "signal_filled":
                await self.notify_signal_filled(**task.get("params", {}))
            else:
                logger.warning(f"Unknown notification task type: {task_type}")

        except Exception as e:
            logger.error(f"Error processing notification task: {str(e)}")


# Global notification service instance
notification_service: Optional[SignalNotificationService] = None


def get_signal_notification_service() -> SignalNotificationService:
    """Get or create the global signal notification service."""
    global notification_service
    if notification_service is None:
        notification_service = SignalNotificationService()
    return notification_service


# Convenience functions for easy integration


async def notify_new_signal(
    signal: Signal,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    user_tier: UserTier = UserTier.FREE,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """
    Convenience function to notify about a new signal.

    Args:
        signal: The trading signal
        priority: Notification priority
        user_tier: User subscription tier
        additional_context: Additional context

    Returns:
        Dict[str, bool]: Success status for each channel
    """
    service = get_signal_notification_service()
    return await service.notify_signal_generated(
        signal=signal,
        priority=priority,
        user_tier=user_tier,
        additional_context=additional_context,
    )


async def notify_signal_update(
    signal: Signal,
    update_type: str,
    previous_values: Dict[str, Any],
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """
    Convenience function to notify about signal updates.

    Args:
        signal: The updated signal
        update_type: Type of update
        previous_values: Previous values
        additional_context: Additional context

    Returns:
        Dict[str, bool]: Success status for each channel
    """
    service = get_signal_notification_service()
    return await service.notify_signal_updated(
        signal=signal,
        update_type=update_type,
        previous_values=previous_values,
        additional_context=additional_context,
    )


async def notify_signal_fill(
    signal: Signal,
    fill_price: float,
    fill_time: datetime,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """
    Convenience function to notify about signal fills.

    Args:
        signal: The filled signal
        fill_price: Fill price
        fill_time: Fill time
        additional_context: Additional context

    Returns:
        Dict[str, bool]: Success status for each channel
    """
    service = get_signal_notification_service()
    return await service.notify_signal_filled(
        signal=signal,
        fill_price=fill_price,
        fill_time=fill_time,
        additional_context=additional_context,
    )
