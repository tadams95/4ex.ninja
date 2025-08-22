"""
Notification Service
Handles Discord notifications for trading signals and system events.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from models.signal_models import TradingSignal, NotificationPayload
from config.settings import get_settings


class NotificationService:
    """Service for sending Discord notifications."""

    def __init__(self):
        self.settings = get_settings()
        self.webhook_url = self.settings.discord_webhook_url
        self.logger = logging.getLogger(__name__)

    async def send_signal_notification(self, signal: TradingSignal) -> bool:
        """
        Send trading signal notification to Discord.

        Args:
            signal: TradingSignal to notify about

        Returns:
            True if notification sent successfully
        """
        if not self.webhook_url:
            self.logger.warning("Discord webhook URL not configured")
            return False

        try:
            embed = self._create_signal_embed(signal)
            payload = NotificationPayload(
                content=f"🚨 **{signal.signal_type}** Signal Generated", embeds=[embed]
            )

            success = await self._send_discord_webhook(payload)

            if success:
                self.logger.info(f"Signal notification sent for {signal.pair}")
            else:
                self.logger.error(
                    f"Failed to send signal notification for {signal.pair}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Error sending signal notification: {str(e)}")
            return False

    async def send_performance_update(self, metrics: Dict[str, Any]) -> bool:
        """Send performance update notification."""
        if not self.webhook_url:
            return False

        try:
            embed = self._create_performance_embed(metrics)
            payload = NotificationPayload(
                content="📊 **Performance Update**", embeds=[embed]
            )

            return await self._send_discord_webhook(payload)

        except Exception as e:
            self.logger.error(f"Error sending performance update: {str(e)}")
            return False

    async def send_system_notification(
        self, message: str, level: str = "info", title: str = "System Notification"
    ) -> bool:
        """Send general system notification."""
        if not self.webhook_url:
            return False

        try:
            color = self._get_color_for_level(level)

            embed = {
                "title": title,
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "4ex.ninja Trading System"},
            }

            payload = NotificationPayload(content=f"🔔 **{title}**", embeds=[embed])

            return await self._send_discord_webhook(payload)

        except Exception as e:
            self.logger.error(f"Error sending system notification: {str(e)}")
            return False

    async def send_batch_signals(self, signals: List[TradingSignal]) -> bool:
        """Send multiple signals in a batch notification."""
        if not self.webhook_url or not signals:
            return False

        try:
            # Group signals by type
            buy_signals = [s for s in signals if s.signal_type == "BUY"]
            sell_signals = [s for s in signals if s.signal_type == "SELL"]

            embeds = []

            if buy_signals:
                embeds.append(self._create_batch_signal_embed(buy_signals, "BUY"))

            if sell_signals:
                embeds.append(self._create_batch_signal_embed(sell_signals, "SELL"))

            if embeds:
                payload = NotificationPayload(
                    content=f"🚨 **Batch Signal Update** - {len(signals)} signals",
                    embeds=embeds,
                )

                return await self._send_discord_webhook(payload)

            return True

        except Exception as e:
            self.logger.error(f"Error sending batch signals: {str(e)}")
            return False

    def _create_signal_embed(self, signal: TradingSignal) -> Dict[str, Any]:
        """Create Discord embed for a trading signal."""
        color = (
            0x00FF00 if signal.signal_type == "BUY" else 0xFF0000
        )  # Green for BUY, Red for SELL

        fields = [
            {"name": "Pair", "value": f"{signal.pair}", "inline": True},
            {"name": "Timeframe", "value": signal.timeframe, "inline": True},
            {"name": "Price", "value": f"{signal.price:.5f}", "inline": True},
            {"name": "Fast MA (50)", "value": f"{signal.fast_ma:.5f}", "inline": True},
            {"name": "Slow MA (200)", "value": f"{signal.slow_ma:.5f}", "inline": True},
        ]

        if signal.confidence:
            fields.append(
                {
                    "name": "Confidence",
                    "value": f"{signal.confidence:.1%}",
                    "inline": True,
                }
            )

        embed = {
            "title": f"{signal.signal_type} Signal",
            "color": color,
            "fields": fields,
            "timestamp": signal.timestamp.isoformat(),
            "footer": {"text": f"Strategy: {signal.strategy_type}"},
        }

        return embed

    def _create_performance_embed(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create Discord embed for performance metrics."""
        return {
            "title": "Performance Metrics",
            "color": 0x0099FF,
            "fields": [
                {
                    "name": "Total Return",
                    "value": f"{metrics.get('total_return', 0):.2f}%",
                    "inline": True,
                },
                {
                    "name": "Win Rate",
                    "value": f"{metrics.get('win_rate', 0):.1%}",
                    "inline": True,
                },
                {
                    "name": "Total Trades",
                    "value": str(metrics.get("total_trades", 0)),
                    "inline": True,
                },
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "4ex.ninja Performance Tracker"},
        }

    def _create_batch_signal_embed(
        self, signals: List[TradingSignal], signal_type: str
    ) -> Dict[str, Any]:
        """Create embed for batch signals of the same type."""
        color = 0x00FF00 if signal_type == "BUY" else 0xFF0000

        pairs_text = "\n".join(
            [f"• {signal.pair} @ {signal.price:.5f}" for signal in signals]
        )

        return {
            "title": f"{signal_type} Signals ({len(signals)})",
            "description": pairs_text,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Conservative Moderate Daily Strategy"},
        }

    def _get_color_for_level(self, level: str) -> int:
        """Get Discord embed color based on notification level."""
        colors = {
            "info": 0x0099FF,  # Blue
            "success": 0x00FF00,  # Green
            "warning": 0xFFAA00,  # Orange
            "error": 0xFF0000,  # Red
            "critical": 0x990000,  # Dark Red
        }
        return colors.get(level.lower(), 0x0099FF)

    async def _send_discord_webhook(self, payload: NotificationPayload) -> bool:
        """Send payload to Discord webhook."""
        try:
            import ssl
            # Create SSL context for Discord API
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(
                    self.webhook_url, json=payload.dict()
                ) as response:
                    if response.status == 204:
                        return True
                    else:
                        self.logger.error(
                            f"Discord webhook failed with status {response.status}"
                        )
                        return False

        except asyncio.TimeoutError:
            self.logger.error("Discord webhook timeout")
            return False
        except Exception as e:
            self.logger.error(f"Discord webhook error: {str(e)}")
            return False

    async def test_notification(self) -> bool:
        """Send a test notification to verify webhook configuration."""
        return await self.send_system_notification(
            "Test notification from 4ex.ninja backend", "info", "System Test"
        )
