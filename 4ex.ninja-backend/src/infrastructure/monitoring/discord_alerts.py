"""
Enhanced Discord Alert Channel for 4ex.ninja

This module extends the existing alert system with advanced Discord integration
for trading signals, providing rich embed formatting and professional notification delivery.
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from infrastructure.monitoring.alerts import AlertChannel, Alert, AlertSeverity
from infrastructure.external_services.discord_service import (
    get_discord_service,
    DiscordChannelType,
    UserTier,
)

logger = logging.getLogger(__name__)


class EnhancedDiscordAlertChannel(AlertChannel):
    """
    Enhanced Discord alert channel that integrates with the Discord notification service.

    This channel routes alerts to appropriate Discord channels based on severity
    and provides rich formatting for both system alerts and trading signals.
    """

    def __init__(self, default_user_tier: UserTier = UserTier.ADMIN):
        self.discord_service = get_discord_service()
        self.default_user_tier = default_user_tier
        self.enabled = self._check_configuration()

    def _check_configuration(self) -> bool:
        """Check if Discord integration is properly configured."""
        try:
            # Check if at least one Discord webhook is configured
            has_webhook = any(
                os.getenv(f"DISCORD_WEBHOOK_{channel_type.value.upper()}")
                for channel_type in DiscordChannelType
            )

            if not has_webhook:
                logger.warning(
                    "No Discord webhooks configured. Discord alerts will be disabled."
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check Discord configuration: {str(e)}")
            return False

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert to Discord with appropriate routing based on severity.

        Args:
            alert: The alert to send

        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.debug("Discord alert channel is disabled")
            return False

        try:
            # Use the Discord service to send the alert
            success = await self.discord_service.send_system_alert(alert)

            if success:
                logger.info(f"Successfully sent alert to Discord: {alert.alert_id}")
            else:
                logger.warning(f"Failed to send alert to Discord: {alert.alert_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending alert to Discord: {str(e)}")
            return False

    def is_available(self) -> bool:
        """Check if the Discord channel is available."""
        return self.enabled

    async def send_signal_alert(
        self,
        signal,  # Signal entity
        alert_type: str = "signal_generated",
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a trading signal as a Discord notification.

        This method bridges the alert system with trading signal notifications,
        allowing signals to be sent through the alert infrastructure.

        Args:
            signal: The trading signal to send
            alert_type: Type of alert (signal_generated, signal_updated, etc.)
            additional_context: Additional context information

        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.debug("Discord alert channel is disabled")
            return False

        try:
            # Determine user tier based on signal confidence or other criteria
            user_tier = self._determine_user_tier_for_signal(signal)

            # Use the Discord service to send the signal notification
            success = await self.discord_service.send_signal_notification(
                signal=signal,
                user_tier=user_tier,
                additional_context=additional_context,
            )

            if success:
                logger.info(
                    f"Successfully sent signal alert to Discord: {signal.signal_id}"
                )
            else:
                logger.warning(
                    f"Failed to send signal alert to Discord: {signal.signal_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error sending signal alert to Discord: {str(e)}")
            return False

    async def send_market_analysis_alert(
        self,
        title: str,
        analysis: str,
        trend_data: Optional[Dict[str, Any]] = None,
        regime_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send market analysis as a Discord notification.

        Args:
            title: Analysis title
            analysis: Analysis content
            trend_data: Trend information
            regime_data: Market regime data

        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.debug("Discord alert channel is disabled")
            return False

        try:
            success = await self.discord_service.send_market_analysis(
                title=title,
                analysis=analysis,
                trend_data=trend_data,
                regime_data=regime_data,
            )

            if success:
                logger.info(f"Successfully sent market analysis to Discord: {title}")

            return success

        except Exception as e:
            logger.error(f"Error sending market analysis to Discord: {str(e)}")
            return False

    async def send_system_status_alert(
        self,
        status: str,
        message: str,
        status_type: str = "info",
        uptime: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send system status update as a Discord notification.

        Args:
            status: Status indicator
            message: Status message
            status_type: Type of status
            uptime: System uptime
            performance_metrics: Performance data

        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.debug("Discord alert channel is disabled")
            return False

        try:
            success = await self.discord_service.send_system_status(
                status=status,
                message=message,
                status_type=status_type,
                uptime=uptime,
                performance_metrics=performance_metrics,
            )

            if success:
                logger.info(f"Successfully sent system status to Discord: {status}")

            return success

        except Exception as e:
            logger.error(f"Error sending system status to Discord: {str(e)}")
            return False

    def _determine_user_tier_for_signal(self, signal) -> UserTier:
        """
        Determine the appropriate user tier for a signal based on its properties.

        This can be enhanced with more sophisticated logic based on:
        - Signal confidence score
        - Market conditions
        - User subscription levels
        - Time of day
        - etc.

        Args:
            signal: The trading signal

        Returns:
            UserTier: The determined user tier
        """
        # Basic logic: high confidence signals go to premium channels
        if hasattr(signal, "confidence_score") and signal.confidence_score:
            if signal.confidence_score >= 0.8:
                return UserTier.PREMIUM

        # Default to free tier
        return UserTier.FREE


# Helper functions for integration with existing alert system


async def send_signal_to_discord(
    signal,
    alert_type: str = "signal_generated",
    additional_context: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Convenience function to send a signal to Discord through the alert system.

    Args:
        signal: The trading signal to send
        alert_type: Type of alert
        additional_context: Additional context

    Returns:
        bool: Success status
    """
    discord_channel = EnhancedDiscordAlertChannel()
    return await discord_channel.send_signal_alert(
        signal=signal, alert_type=alert_type, additional_context=additional_context
    )


async def send_market_analysis_to_discord(
    title: str,
    analysis: str,
    trend_data: Optional[Dict[str, Any]] = None,
    regime_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Convenience function to send market analysis to Discord.

    Args:
        title: Analysis title
        analysis: Analysis content
        trend_data: Trend data
        regime_data: Regime data

    Returns:
        bool: Success status
    """
    discord_channel = EnhancedDiscordAlertChannel()
    return await discord_channel.send_market_analysis_alert(
        title=title, analysis=analysis, trend_data=trend_data, regime_data=regime_data
    )


async def send_system_status_to_discord(
    status: str,
    message: str,
    status_type: str = "info",
    uptime: Optional[str] = None,
    performance_metrics: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Convenience function to send system status to Discord.

    Args:
        status: Status indicator
        message: Status message
        status_type: Type of status
        uptime: System uptime
        performance_metrics: Performance metrics

    Returns:
        bool: Success status
    """
    discord_channel = EnhancedDiscordAlertChannel()
    return await discord_channel.send_system_status_alert(
        status=status,
        message=message,
        status_type=status_type,
        uptime=uptime,
        performance_metrics=performance_metrics,
    )


# Integration function to add Discord channel to the existing alert manager
def add_discord_channel_to_alert_manager(alert_manager) -> bool:
    """
    Add the enhanced Discord channel to an existing alert manager.

    Args:
        alert_manager: The alert manager instance

    Returns:
        bool: Success status
    """
    try:
        discord_channel = EnhancedDiscordAlertChannel()
        alert_manager.add_channel("discord_enhanced", discord_channel)

        # Add routing rules for Discord
        alert_manager.add_alert_rule(
            {
                "severity": [AlertSeverity.CRITICAL],
                "channels": ["logs", "email", "discord_enhanced"],
                "immediate": True,
            }
        )

        alert_manager.add_alert_rule(
            {
                "severity": [AlertSeverity.HIGH],
                "channels": ["logs", "discord_enhanced"],
                "immediate": True,
            }
        )

        logger.info("Enhanced Discord alert channel added to alert manager")
        return True

    except Exception as e:
        logger.error(f"Failed to add Discord channel to alert manager: {str(e)}")
        return False
