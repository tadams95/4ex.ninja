"""
Discord Service for 4ex.ninja

This module provides Discord integration services with support for different
channel types, user tiers, and comprehensive notification delivery.
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import aiohttp
from dataclasses import dataclass

from core.entities.signal import Signal
from infrastructure.monitoring.alerts import Alert, AlertSeverity

logger = logging.getLogger(__name__)


class UserTier(Enum):
    """User tier levels for Discord access control."""

    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


class DiscordChannelType(Enum):
    """Discord channel types for routing."""

    SIGNALS_FREE = "signals_free"
    SIGNALS_PREMIUM = "signals_premium"
    ALERTS_CRITICAL = "alerts_critical"
    ALERTS_GENERAL = "alerts_general"
    MARKET_ANALYSIS = "market_analysis"
    SYSTEM_STATUS = "system_status"
    GENERAL = "general"


@dataclass
class DiscordMessage:
    """Discord message data structure."""

    content: str
    embeds: List[Dict[str, Any]]
    channel_type: DiscordChannelType
    priority: str = "normal"


class DiscordService:
    """
    Discord service for sending notifications with webhook support.

    This service provides basic webhook functionality for Discord notifications
    with proper error handling and rate limiting awareness.
    """

    def __init__(self):
        self.webhooks = self._load_webhook_configuration()
        self.session: Optional[aiohttp.ClientSession] = None

    def _load_webhook_configuration(self) -> Dict[DiscordChannelType, str]:
        """Load Discord webhook URLs from environment variables."""
        webhooks = {}

        webhook_mapping = {
            DiscordChannelType.SIGNALS_FREE: "DISCORD_WEBHOOK_SIGNALS_FREE",
            DiscordChannelType.SIGNALS_PREMIUM: "DISCORD_WEBHOOK_SIGNALS_PREMIUM",
            DiscordChannelType.ALERTS_CRITICAL: "DISCORD_WEBHOOK_ALERTS_CRITICAL",
            DiscordChannelType.ALERTS_GENERAL: "DISCORD_WEBHOOK_ALERTS_GENERAL",
            DiscordChannelType.MARKET_ANALYSIS: "DISCORD_WEBHOOK_MARKET_ANALYSIS",
            DiscordChannelType.SYSTEM_STATUS: "DISCORD_WEBHOOK_SYSTEM_STATUS",
            DiscordChannelType.GENERAL: "DISCORD_WEBHOOK_COMMUNITY",
        }

        for channel_type, env_var in webhook_mapping.items():
            webhook_url = os.getenv(env_var)
            if webhook_url:
                webhooks[channel_type] = webhook_url
            else:
                logger.debug(f"No webhook configured for {channel_type.value}")

        # Fallback to general webhook if available
        general_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        if general_webhook and not webhooks:
            logger.info("Using general Discord webhook as fallback")
            for channel_type in DiscordChannelType:
                webhooks[channel_type] = general_webhook

        return webhooks

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session

    async def send_webhook_message(
        self, channel_type: DiscordChannelType, message: DiscordMessage
    ) -> bool:
        """
        Send a message to Discord via webhook.

        Args:
            channel_type: Target Discord channel type
            message: Message to send

        Returns:
            bool: Success status
        """
        webhook_url = self.webhooks.get(channel_type)
        if not webhook_url:
            logger.warning(f"No webhook configured for {channel_type.value}")
            return False

        try:
            session = await self._get_session()

            payload = {"content": message.content, "embeds": message.embeds}

            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.debug(f"Successfully sent message to {channel_type.value}")
                    return True
                else:
                    logger.warning(
                        f"Discord webhook returned status {response.status} for {channel_type.value}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.error(f"Timeout sending message to Discord {channel_type.value}")
            return False
        except Exception as e:
            logger.error(
                f"Error sending Discord message to {channel_type.value}: {str(e)}"
            )
            return False

    async def send_signal_notification(
        self,
        signal: Signal,
        user_tier: UserTier = UserTier.FREE,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a trading signal notification to appropriate Discord channel.

        Args:
            signal: Trading signal to send
            user_tier: User tier for channel routing
            additional_context: Additional context information

        Returns:
            bool: Success status
        """
        try:
            # Determine target channel based on user tier and signal confidence
            channel_type = self._get_signal_channel(signal, user_tier)

            # Create Discord embed for signal
            embed = self._create_signal_embed(signal, additional_context)

            message = DiscordMessage(
                content=f"🚨 New {signal.signal_type.value} signal: {signal.pair}",
                embeds=[embed],
                channel_type=channel_type,
                priority=(
                    "high"
                    if signal.confidence_score and signal.confidence_score > 0.8
                    else "normal"
                ),
            )

            return await self.send_webhook_message(channel_type, message)

        except Exception as e:
            logger.error(f"Error sending signal notification: {str(e)}")
            return False

    async def send_system_alert(self, alert: Alert) -> bool:
        """
        Send a system alert to Discord.

        Args:
            alert: System alert to send

        Returns:
            bool: Success status
        """
        try:
            # Route based on alert severity
            channel_type = (
                DiscordChannelType.ALERTS_CRITICAL
                if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]
                else DiscordChannelType.ALERTS_GENERAL
            )

            embed = self._create_alert_embed(alert)

            message = DiscordMessage(
                content=f"🚨 {alert.severity.value.upper()} Alert",
                embeds=[embed],
                channel_type=channel_type,
                priority=(
                    "urgent" if alert.severity == AlertSeverity.CRITICAL else "high"
                ),
            )

            return await self.send_webhook_message(channel_type, message)

        except Exception as e:
            logger.error(f"Error sending system alert: {str(e)}")
            return False

    async def send_market_analysis(
        self,
        title: str,
        analysis: str,
        trend_data: Optional[Dict[str, Any]] = None,
        regime_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send market analysis to Discord.

        Args:
            title: Analysis title
            analysis: Analysis content
            trend_data: Trend data
            regime_data: Market regime data

        Returns:
            bool: Success status
        """
        try:
            embed = {
                "title": title,
                "description": analysis[:2000],  # Discord embed description limit
                "color": 0x0099FF,  # Blue color
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": [],
            }

            if trend_data:
                embed["fields"].append(
                    {
                        "name": "Trend Analysis",
                        "value": str(trend_data)[:1000],
                        "inline": False,
                    }
                )

            if regime_data:
                embed["fields"].append(
                    {
                        "name": "Market Regime",
                        "value": str(regime_data)[:1000],
                        "inline": False,
                    }
                )

            message = DiscordMessage(
                content="📊 Market Analysis Update",
                embeds=[embed],
                channel_type=DiscordChannelType.MARKET_ANALYSIS,
                priority="normal",
            )

            return await self.send_webhook_message(
                DiscordChannelType.MARKET_ANALYSIS, message
            )

        except Exception as e:
            logger.error(f"Error sending market analysis: {str(e)}")
            return False

    def _get_signal_channel(
        self, signal: Signal, user_tier: UserTier
    ) -> DiscordChannelType:
        """Determine appropriate Discord channel for signal based on user tier."""
        if (
            user_tier == UserTier.PREMIUM
            and signal.confidence_score
            and signal.confidence_score >= 0.8
        ):
            return DiscordChannelType.SIGNALS_PREMIUM
        return DiscordChannelType.SIGNALS_FREE

    def _create_signal_embed(
        self, signal: Signal, additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create Discord embed for trading signal."""
        color = 0x00FF00 if signal.signal_type.value == "BUY" else 0xFF0000

        embed = {
            "title": f"{signal.signal_type.value} Signal - {signal.pair}",
            "color": color,
            "timestamp": signal.timestamp.isoformat(),
            "fields": [
                {
                    "name": "Entry Price",
                    "value": str(signal.entry_price),
                    "inline": True,
                },
                {"name": "Timeframe", "value": signal.timeframe, "inline": True},
                {
                    "name": "Strategy",
                    "value": signal.strategy_name or "Unknown",
                    "inline": True,
                },
            ],
        }

        if signal.confidence_score:
            embed["fields"].append(
                {
                    "name": "Confidence",
                    "value": f"{signal.confidence_score:.1%}",
                    "inline": True,
                }
            )

        if signal.stop_loss:
            embed["fields"].append(
                {"name": "Stop Loss", "value": str(signal.stop_loss), "inline": True}
            )

        if signal.take_profit:
            embed["fields"].append(
                {
                    "name": "Take Profit",
                    "value": str(signal.take_profit),
                    "inline": True,
                }
            )

        if additional_context:
            for key, value in additional_context.items():
                if len(embed["fields"]) < 25:  # Discord limit
                    embed["fields"].append(
                        {
                            "name": key.replace("_", " ").title(),
                            "value": str(value)[:1000],  # Field value limit
                            "inline": True,
                        }
                    )

        return embed

    def _create_alert_embed(self, alert: Alert) -> Dict[str, Any]:
        """Create Discord embed for system alert."""
        severity_colors = {
            AlertSeverity.CRITICAL: 0xFF0000,  # Red
            AlertSeverity.HIGH: 0xFF8C00,  # Orange
            AlertSeverity.MEDIUM: 0xFFFF00,  # Yellow
            AlertSeverity.LOW: 0x00FFFF,  # Cyan
            AlertSeverity.INFO: 0x0080FF,  # Blue
        }

        embed = {
            "title": f"{alert.severity.value.upper()} Alert",
            "description": alert.message[:2000],
            "color": severity_colors.get(alert.severity, 0x808080),
            "timestamp": alert.timestamp.isoformat(),
            "fields": [
                {"name": "Alert ID", "value": alert.alert_id, "inline": True},
                {"name": "Source", "value": alert.source, "inline": True},
            ],
        }

        if alert.context:
            for key, value in alert.context.items():
                if len(embed["fields"]) < 25:
                    embed["fields"].append(
                        {
                            "name": key.replace("_", " ").title(),
                            "value": str(value)[:1000],
                            "inline": True,
                        }
                    )

        return embed

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()


# Global service instance
_discord_service: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """Get or create the global Discord service instance."""
    global _discord_service
    if _discord_service is None:
        _discord_service = DiscordService()
    return _discord_service


async def cleanup_discord_service():
    """Cleanup the global Discord service."""
    global _discord_service
    if _discord_service:
        await _discord_service.close()
        _discord_service = None
