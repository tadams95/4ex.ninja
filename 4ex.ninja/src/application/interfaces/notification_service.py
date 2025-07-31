"""
Notification Service Interface
Defines the interface for notification and alerting system.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ...core.entities.signal import Signal


class NotificationType(Enum):
    """Types of notifications."""

    SIGNAL_GENERATED = "signal_generated"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    STRATEGY_ACTIVATED = "strategy_activated"
    STRATEGY_DEACTIVATED = "strategy_deactivated"
    SYSTEM_ERROR = "system_error"
    MARKET_ALERT = "market_alert"
    DAILY_SUMMARY = "daily_summary"


class NotificationChannel(Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class INotificationService(ABC):
    """
    Notification service interface for alerts and communications.
    """

    @abstractmethod
    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: List[NotificationChannel],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a notification through specified channels.

        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channels: Delivery channels
            priority: Notification priority
            data: Optional additional data

        Returns:
            True if notification sent successfully
        """
        pass

    @abstractmethod
    async def send_signal_notification(
        self, signal: Signal, notification_type: NotificationType
    ) -> bool:
        """
        Send signal-related notification.

        Args:
            signal: The trading signal
            notification_type: Type of signal notification

        Returns:
            True if notification sent successfully
        """
        pass

    @abstractmethod
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """
        Send email notification.

        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text)
            html_body: Optional HTML email body
            attachments: Optional list of attachment file paths

        Returns:
            True if email sent successfully
        """
        pass

    @abstractmethod
    async def send_sms(self, phone_numbers: List[str], message: str) -> bool:
        """
        Send SMS notification.

        Args:
            phone_numbers: List of recipient phone numbers
            message: SMS message

        Returns:
            True if SMS sent successfully
        """
        pass

    @abstractmethod
    async def send_push_notification(
        self,
        user_ids: List[str],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send push notification to mobile devices.

        Args:
            user_ids: List of user identifiers
            title: Notification title
            message: Notification message
            data: Optional additional data

        Returns:
            True if push notification sent successfully
        """
        pass

    @abstractmethod
    async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send webhook notification.

        Args:
            webhook_url: Webhook URL
            payload: JSON payload to send
            headers: Optional additional headers

        Returns:
            True if webhook sent successfully
        """
        pass

    @abstractmethod
    async def send_telegram_message(
        self, chat_ids: List[str], message: str, parse_mode: str = "HTML"
    ) -> bool:
        """
        Send Telegram message.

        Args:
            chat_ids: List of Telegram chat IDs
            message: Message to send
            parse_mode: Message parse mode (HTML, Markdown, etc.)

        Returns:
            True if message sent successfully
        """
        pass

    @abstractmethod
    async def configure_notification_preferences(
        self,
        user_id: str,
        preferences: Dict[NotificationType, List[NotificationChannel]],
    ) -> bool:
        """
        Configure user notification preferences.

        Args:
            user_id: User identifier
            preferences: Notification preferences by type

        Returns:
            True if preferences updated successfully
        """
        pass

    @abstractmethod
    async def get_notification_history(
        self,
        user_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get notification history.

        Args:
            user_id: Optional user filter
            notification_type: Optional notification type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of notifications to return

        Returns:
            List of notification records
        """
        pass

    @abstractmethod
    async def create_notification_template(
        self,
        template_name: str,
        notification_type: NotificationType,
        title_template: str,
        message_template: str,
        variables: List[str],
    ) -> bool:
        """
        Create notification template.

        Args:
            template_name: Template name
            notification_type: Type of notification
            title_template: Title template with variables
            message_template: Message template with variables
            variables: List of template variables

        Returns:
            True if template created successfully
        """
        pass

    @abstractmethod
    async def send_daily_summary(self, user_id: str) -> bool:
        """
        Send daily trading summary.

        Args:
            user_id: User identifier

        Returns:
            True if summary sent successfully
        """
        pass

    @abstractmethod
    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: NotificationPriority = NotificationPriority.HIGH,
    ) -> bool:
        """
        Send system alert notification.

        Args:
            alert_type: Type of system alert
            message: Alert message
            severity: Alert severity level

        Returns:
            True if alert sent successfully
        """
        pass

    @abstractmethod
    async def test_notification_channels(self) -> Dict[NotificationChannel, bool]:
        """
        Test all configured notification channels.

        Returns:
            Dictionary mapping channels to test results
        """
        pass
