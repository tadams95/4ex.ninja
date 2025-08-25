"""
Enhanced Discord Integration Service
Advanced Discord webhook management with tier-based routing and rich signal formatting.

Features:
- Multi-tier webhook routing (Free, Premium, Whale, Alpha)
- Enhanced signal embeds with Phase 1 strategy details
- Rate limiting and error handling
- Signal delivery tracking
- Performance monitoring integration
"""

import asyncio
import aiohttp
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

from models.signal_models import TradingSignal, NotificationPayload
from config.settings import get_settings


class UserTier(Enum):
    """User tier levels for Discord routing."""
    FREE = "free"
    PREMIUM = "premium"
    WHALE = "whale"
    ALPHA = "alpha"


class SignalPriority(Enum):
    """Signal priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnhancedDiscordService:
    """Enhanced Discord service with multi-tier support and rich formatting."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Webhook configurations for different tiers
        self.webhook_configs = {
            UserTier.FREE: {
                "url": os.getenv("DISCORD_WEBHOOK_SIGNALS_FREE"),
                "name": "Free Signals",
                "color": 0x3498DB,  # Blue
                "rate_limit": 5  # signals per hour
            },
            UserTier.PREMIUM: {
                "url": os.getenv("DISCORD_WEBHOOK_SIGNALS_PREMIUM"),
                "name": "Premium Signals",
                "color": 0xF39C12,  # Orange
                "rate_limit": 20  # signals per hour
            },
            UserTier.WHALE: {
                "url": os.getenv("DISCORD_WEBHOOK_WHALE_SIGNALS"),
                "name": "Whale Signals",
                "color": 0x9B59B6,  # Purple
                "rate_limit": 50  # signals per hour
            },
            UserTier.ALPHA: {
                "url": os.getenv("DISCORD_WEBHOOK_ALPHA_SIGNALS"),
                "name": "Alpha Signals",
                "color": 0xE74C3C,  # Red
                "rate_limit": 100  # signals per hour
            }
        }
        
        # Additional webhook types
        self.system_webhooks = {
            "critical": os.getenv("DISCORD_WEBHOOK_ALERTS_CRITICAL"),
            "general": os.getenv("DISCORD_WEBHOOK_ALERTS_GENERAL"),
            "market_analysis": os.getenv("DISCORD_WEBHOOK_MARKET_ANALYSIS"),
            "system_status": os.getenv("DISCORD_WEBHOOK_SYSTEM_STATUS"),
            "community": os.getenv("DISCORD_WEBHOOK_COMMUNITY")
        }
        
        # Branding configuration
        self.branding = {
            "avatar_url": os.getenv("DISCORD_AVATAR_URL", "https://4ex.ninja/logo.png"),
            "footer_icon_url": os.getenv("DISCORD_FOOTER_ICON_URL", "https://4ex.ninja/favicon.ico"),
            "brand_color": int(os.getenv("DISCORD_BRAND_COLOR", "0x1DB954"), 16)
        }
        
        # Rate limiting tracking
        self.rate_limits = {}
        
        # Delivery tracking
        self.delivery_stats = {
            "total_sent": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "by_tier": {tier.value: {"sent": 0, "success": 0, "failed": 0} for tier in UserTier}
        }

    async def send_enhanced_signal(
        self, 
        signal_data: Dict[str, Any], 
        user_tier: UserTier = UserTier.FREE,
        priority: SignalPriority = SignalPriority.MEDIUM
    ) -> bool:
        """
        Send enhanced trading signal to appropriate Discord channel.
        
        Args:
            signal_data: Enhanced signal data from strategy
            user_tier: User subscription tier
            priority: Signal priority level
            
        Returns:
            True if signal sent successfully
        """
        try:
            webhook_config = self.webhook_configs.get(user_tier)
            if not webhook_config or not webhook_config["url"]:
                self.logger.warning(f"No webhook configured for tier: {user_tier.value}")
                return False
            
            # Check rate limits
            if not self._check_rate_limit(user_tier):
                self.logger.warning(f"Rate limit exceeded for tier: {user_tier.value}")
                return False
            
            # Create enhanced embed
            embed = self._create_enhanced_signal_embed(signal_data, user_tier, priority)
            
            # Create payload
            payload = {
                "content": self._get_signal_content_message(signal_data, priority),
                "embeds": [embed],
                "username": f"4ex.ninja {webhook_config['name']}",
                "avatar_url": self.branding["avatar_url"]
            }
            
            # Send to Discord
            success = await self._send_webhook(webhook_config["url"], payload)
            
            # Update delivery stats
            self._update_delivery_stats(user_tier, success)
            
            if success:
                self.logger.info(f"Enhanced signal sent to {user_tier.value} tier: {signal_data.get('pair')}")
            else:
                self.logger.error(f"Failed to send signal to {user_tier.value} tier: {signal_data.get('pair')}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending enhanced signal: {str(e)}")
            self._update_delivery_stats(user_tier, False)
            return False

    def _create_enhanced_signal_embed(
        self, 
        signal_data: Dict[str, Any], 
        user_tier: UserTier,
        priority: SignalPriority
    ) -> Dict[str, Any]:
        """Create rich Discord embed for enhanced signal."""
        
        # Handle both V2 format and legacy format
        trade_rec = signal_data.get("trade_recommendation", {})
        signal_direction = (
            signal_data.get("direction") or  # V2 format
            trade_rec.get("signal_direction") or  # Legacy format
            signal_data.get("signal", "UNKNOWN")  # Fallback
        )
        
        # Convert BUY/SELL to LONG/SHORT for consistency
        if signal_direction == "BUY":
            signal_direction = "LONG"
        elif signal_direction == "SELL":
            signal_direction = "SHORT"
            
        confidence = trade_rec.get("confidence", signal_data.get("confidence", 0.0))
        
        # Determine embed color based on signal direction and priority
        if signal_direction == "LONG":
            base_color = 0x00FF00  # Green
        elif signal_direction == "SHORT":
            base_color = 0xFF0000  # Red
        else:
            base_color = self.webhook_configs[user_tier]["color"]
        
        # Adjust color intensity based on priority
        if priority == SignalPriority.CRITICAL:
            color = base_color
        elif priority == SignalPriority.HIGH:
            color = base_color
        else:
            color = self.webhook_configs[user_tier]["color"]
        
        # Build embed fields
        fields = []
        
        # Basic signal information
        fields.extend([
            {
                "name": "💱 Pair",
                "value": f"**{signal_data.get('pair', 'UNKNOWN')}**",
                "inline": True
            },
            {
                "name": "📊 Direction",
                "value": f"**{signal_direction}** {self._get_direction_emoji(signal_direction)}",
                "inline": True
            },
            {
                "name": "💹 Price",
                "value": f"**{signal_data.get('entry_price', signal_data.get('current_price', 0)):.5f}**",
                "inline": True
            }
        ])
        
        # Enhanced strategy details
        if confidence > 0:
            fields.append({
                "name": "🎯 Confidence",
                "value": f"**{confidence:.1%}**",
                "inline": True
            })
        
        # Phase 1 enhancement details
        phase1_data = signal_data.get("phase1_enhancements", {})
        session_analysis = signal_data.get("session_analysis", {})
        
        # Session information (for JPY pairs)
        if "JPY" in signal_data.get("pair", ""):
            session_quality = session_analysis.get("session_quality_multiplier", 1.0)
            is_optimal = session_analysis.get("is_optimal_session", False)
            fields.append({
                "name": "🕐 Session Quality",
                "value": f"**{session_quality:.1f}x** {'✅ Optimal' if is_optimal else '⚠️ Sub-optimal'}",
                "inline": True
            })
        
        # Confluence scoring
        confluence_score = signal_data.get("confluence_score", 0.0)
        if confluence_score > 0:
            confluence_emoji = "🟢" if confluence_score >= 1.0 else "🟡" if confluence_score >= 0.5 else "🔴"
            fields.append({
                "name": "🎯 Confluence Score",
                "value": f"**{confluence_score:.2f}** {confluence_emoji}",
                "inline": True
            })
        
        # Signal strength
        signal_strength = signal_data.get("signal_strength", "unknown")
        strength_emoji = {
            "confluence": "🟢🟢🟢",
            "very_strong": "🟢🟢",
            "strong": "🟢",
            "moderate": "🟡",
            "weak": "🔴"
        }.get(signal_strength, "❓")
        
        fields.append({
            "name": "💪 Signal Strength",
            "value": f"**{signal_strength.replace('_', ' ').title()}** {strength_emoji}",
            "inline": True
        })
        
        # Position sizing (if available)
        position_sizing = signal_data.get("position_sizing")
        if position_sizing and user_tier in [UserTier.PREMIUM, UserTier.WHALE, UserTier.ALPHA]:
            risk_percent = position_sizing.get("risk_percent", 0)
            position_size = position_sizing.get("position_size", 0)
            fields.extend([
                {
                    "name": "📈 Risk %",
                    "value": f"**{risk_percent:.1f}%**",
                    "inline": True
                },
                {
                    "name": "💰 Position Size",
                    "value": f"**{position_size:,.0f}** units",
                    "inline": True
                }
            ])
        
        # Strategy information
        strategy_field_value = "Enhanced Daily Strategy (Phase 1)"
        if phase1_data:
            enhancements = []
            if phase1_data.get("session_filter_active"):
                enhancements.append("📅 Session Filter")
            if phase1_data.get("confluence_detected"):
                enhancements.append("🎯 Confluence")
            if phase1_data.get("dynamic_sizing_applied"):
                enhancements.append("⚖️ Dynamic Sizing")
            
            if enhancements:
                strategy_field_value += f"\n{' • '.join(enhancements)}"
        
        fields.append({
            "name": "🤖 Strategy",
            "value": strategy_field_value,
            "inline": False
        })
        
        # Create embed
        embed = {
            "title": f"{self._get_direction_emoji(signal_direction)} {signal_direction} Signal - {signal_data.get('pair')}",
            "description": self._get_signal_description(signal_data, user_tier),
            "color": color,
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"4ex.ninja • {user_tier.value.title()} Tier • {priority.value.title()} Priority",
                "icon_url": self.branding["footer_icon_url"]
            },
            "thumbnail": {
                "url": self.branding["avatar_url"]
            }
        }
        
        return embed

    def _get_signal_description(self, signal_data: Dict[str, Any], user_tier: UserTier) -> str:
        """Get appropriate signal description based on user tier."""
        
        base_desc = f"Enhanced Daily Strategy signal for {signal_data.get('pair')}"
        
        if user_tier == UserTier.FREE:
            return f"{base_desc} - Join premium for detailed analysis!"
        
        trade_rec = signal_data.get("trade_recommendation", {})
        filters_passed = trade_rec.get("filters_passed", [])
        
        if filters_passed:
            return f"{base_desc}\n\n**Passed Filters:** {', '.join(filters_passed[:3])}"
        
        return base_desc

    def _get_signal_content_message(self, signal_data: Dict[str, Any], priority: SignalPriority) -> str:
        """Get content message for signal notification."""
        
        priority_emoji = {
            SignalPriority.CRITICAL: "🚨🚨🚨",
            SignalPriority.HIGH: "🚨🚨",
            SignalPriority.MEDIUM: "🚨",
            SignalPriority.LOW: "📢"
        }
        
        emoji = priority_emoji.get(priority, "📢")
        direction = (
            signal_data.get("direction") or  # V2 format
            signal_data.get("trade_recommendation", {}).get("signal_direction") or  # Legacy format
            signal_data.get("signal", "SIGNAL")  # Fallback
        )
        
        # Convert BUY/SELL to LONG/SHORT
        if direction == "BUY":
            direction = "LONG"
        elif direction == "SELL":
            direction = "SHORT"
        pair = signal_data.get("pair", "UNKNOWN")
        
        return f"{emoji} **{direction} {pair}** - Enhanced Daily Strategy Signal"

    def _get_direction_emoji(self, direction: str) -> str:
        """Get emoji for signal direction."""
        return {
            "LONG": "📈",
            "SHORT": "📉",
            "BUY": "🟢",
            "SELL": "🔴"
        }.get(direction, "📊")

    async def send_batch_enhanced_signals(
        self, 
        signals_data: List[Dict[str, Any]], 
        user_tier: UserTier = UserTier.FREE
    ) -> bool:
        """Send multiple signals as a batch notification."""
        
        if not signals_data:
            return False
        
        try:
            webhook_config = self.webhook_configs.get(user_tier)
            if not webhook_config or not webhook_config["url"]:
                return False
            
            # Group signals by direction - handle both V2 and legacy formats
            long_signals = []
            short_signals = []
            
            for s in signals_data:
                direction = (
                    s.get("direction") or 
                    s.get("trade_recommendation", {}).get("signal_direction") or 
                    s.get("signal", "")
                )
                if direction in ["LONG", "BUY"]:
                    long_signals.append(s)
                elif direction in ["SHORT", "SELL"]:
                    short_signals.append(s)
            
            embeds = []
            
            if long_signals:
                embeds.append(self._create_batch_embed(long_signals, "LONG", user_tier))
            
            if short_signals:
                embeds.append(self._create_batch_embed(short_signals, "SHORT", user_tier))
            
            if embeds:
                payload = {
                    "content": f"🚨 **Batch Signal Update** - {len(signals_data)} Enhanced Signals",
                    "embeds": embeds,
                    "username": f"4ex.ninja {webhook_config['name']}",
                    "avatar_url": self.branding["avatar_url"]
                }
                
                success = await self._send_webhook(webhook_config["url"], payload)
                self._update_delivery_stats(user_tier, success)
                return success
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending batch signals: {str(e)}")
            return False

    def _create_batch_embed(
        self, 
        signals: List[Dict[str, Any]], 
        direction: str, 
        user_tier: UserTier
    ) -> Dict[str, Any]:
        """Create embed for batch signals."""
        
        color = 0x00FF00 if direction == "LONG" else 0xFF0000
        
        # Create pairs list with confidence scores
        pairs_text = []
        for signal in signals[:10]:  # Limit to 10 signals to avoid Discord limits
            pair = signal.get("pair", "UNKNOWN")
            confidence = signal.get("trade_recommendation", {}).get("confidence", 0.0)
            price = signal.get("current_price", 0)
            confluence = signal.get("confluence_score", 0.0)
            
            confidence_emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
            confluence_emoji = "⭐" if confluence >= 1.0 else ""
            
            pairs_text.append(f"• **{pair}** @ {price:.5f} {confidence_emoji} {confluence_emoji}")
        
        if len(signals) > 10:
            pairs_text.append(f"... and {len(signals) - 10} more signals")
        
        description = "\n".join(pairs_text)
        
        # Add summary statistics
        avg_confidence = sum(s.get("trade_recommendation", {}).get("confidence", 0) for s in signals) / len(signals)
        jpy_pairs = sum(1 for s in signals if "JPY" in s.get("pair", ""))
        
        summary_fields = [
            {
                "name": "📊 Summary",
                "value": f"**{len(signals)}** {direction} signals\n**{avg_confidence:.1%}** avg confidence\n**{jpy_pairs}** JPY pairs",
                "inline": True
            }
        ]
        
        if user_tier in [UserTier.PREMIUM, UserTier.WHALE, UserTier.ALPHA]:
            high_confluence = sum(1 for s in signals if s.get("confluence_score", 0) >= 1.0)
            session_optimal = sum(1 for s in signals if s.get("session_analysis", {}).get("is_optimal_session", False))
            
            summary_fields.append({
                "name": "🎯 Quality Metrics",
                "value": f"**{high_confluence}** high confluence\n**{session_optimal}** optimal session",
                "inline": True
            })
        
        return {
            "title": f"📈 {direction} Signals ({len(signals)})" if direction == "LONG" else f"📉 {direction} Signals ({len(signals)})",
            "description": description,
            "color": color,
            "fields": summary_fields,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Enhanced Daily Strategy • {user_tier.value.title()} Tier",
                "icon_url": self.branding["footer_icon_url"]
            }
        }

    async def send_performance_update(
        self, 
        metrics: Dict[str, Any], 
        user_tier: UserTier = UserTier.FREE
    ) -> bool:
        """Send performance metrics update."""
        
        try:
            webhook_config = self.webhook_configs.get(user_tier)
            if not webhook_config or not webhook_config["url"]:
                return False
            
            embed = {
                "title": "📊 Performance Update - Enhanced Daily Strategy",
                "color": self.branding["brand_color"],
                "fields": [
                    {
                        "name": "📈 Total Return",
                        "value": f"**{metrics.get('total_return', 0):.2f}%**",
                        "inline": True
                    },
                    {
                        "name": "🎯 Win Rate",
                        "value": f"**{metrics.get('win_rate', 0):.1%}**",
                        "inline": True
                    },
                    {
                        "name": "📊 Total Trades",
                        "value": f"**{metrics.get('total_trades', 0)}**",
                        "inline": True
                    },
                    {
                        "name": "💰 Avg Trade Return",
                        "value": f"**{metrics.get('avg_trade_return', 0):.1f}%**",
                        "inline": True
                    },
                    {
                        "name": "📉 Max Drawdown",
                        "value": f"**{metrics.get('max_drawdown', 0):.1f}%**",
                        "inline": True
                    },
                    {
                        "name": "⚡ Sharpe Ratio",
                        "value": f"**{metrics.get('sharpe_ratio', 0):.2f}**",
                        "inline": True
                    }
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "4ex.ninja Performance Tracker",
                    "icon_url": self.branding["footer_icon_url"]
                }
            }
            
            payload = {
                "content": "📊 **Enhanced Daily Strategy Performance Update**",
                "embeds": [embed],
                "username": f"4ex.ninja {webhook_config['name']}",
                "avatar_url": self.branding["avatar_url"]
            }
            
            return await self._send_webhook(webhook_config["url"], payload)
            
        except Exception as e:
            self.logger.error(f"Error sending performance update: {str(e)}")
            return False

    async def send_system_notification(
        self, 
        message: str, 
        level: str = "info", 
        webhook_type: str = "general"
    ) -> bool:
        """Send system notification to appropriate webhook."""
        
        webhook_url = self.system_webhooks.get(webhook_type)
        if not webhook_url:
            return False
        
        color_map = {
            "info": 0x0099FF,
            "success": 0x00FF00,
            "warning": 0xFFAA00,
            "error": 0xFF0000,
            "critical": 0x990000
        }
        
        embed = {
            "title": f"🔔 System {level.title()}",
            "description": message,
            "color": color_map.get(level, 0x0099FF),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "4ex.ninja System Monitor",
                "icon_url": self.branding["footer_icon_url"]
            }
        }
        
        payload = {
            "content": f"🔔 **System {level.title()}**",
            "embeds": [embed],
            "username": "4ex.ninja System",
            "avatar_url": self.branding["avatar_url"]
        }
        
        return await self._send_webhook(webhook_url, payload)

    def _check_rate_limit(self, user_tier: UserTier) -> bool:
        """Check if user tier is within rate limits."""
        # Simplified rate limiting - in production, implement proper time-based limits
        config = self.webhook_configs.get(user_tier, {})
        limit = config.get("rate_limit", 10)
        
        current_hour = datetime.now().hour
        tier_key = f"{user_tier.value}_{current_hour}"
        
        if tier_key not in self.rate_limits:
            self.rate_limits[tier_key] = 0
        
        if self.rate_limits[tier_key] >= limit:
            return False
        
        self.rate_limits[tier_key] += 1
        return True

    def _update_delivery_stats(self, user_tier: UserTier, success: bool):
        """Update delivery statistics."""
        self.delivery_stats["total_sent"] += 1
        self.delivery_stats["by_tier"][user_tier.value]["sent"] += 1
        
        if success:
            self.delivery_stats["successful_deliveries"] += 1
            self.delivery_stats["by_tier"][user_tier.value]["success"] += 1
        else:
            self.delivery_stats["failed_deliveries"] += 1
            self.delivery_stats["by_tier"][user_tier.value]["failed"] += 1

    async def _send_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """Send payload to Discord webhook with error handling."""
        try:
            import ssl
            # Create SSL context for Discord API
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 204:
                        return True
                    else:
                        self.logger.error(f"Discord webhook failed with status {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("Discord webhook timeout")
            return False
        except Exception as e:
            self.logger.error(f"Discord webhook error: {str(e)}")
            return False

    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics."""
        total = self.delivery_stats["total_sent"]
        success_rate = (self.delivery_stats["successful_deliveries"] / total * 100) if total > 0 else 0
        
        return {
            "total_sent": total,
            "successful_deliveries": self.delivery_stats["successful_deliveries"],
            "failed_deliveries": self.delivery_stats["failed_deliveries"],
            "success_rate": round(success_rate, 2),
            "by_tier": self.delivery_stats["by_tier"]
        }

    async def test_all_webhooks(self) -> Dict[str, bool]:
        """Test all configured webhooks."""
        results = {}
        
        # Test tier webhooks
        for tier, config in self.webhook_configs.items():
            if config["url"]:
                test_payload = {
                    "content": f"🧪 Test notification for {tier.value} tier",
                    "embeds": [{
                        "title": f"{config['name']} Test",
                        "description": "Testing webhook connectivity",
                        "color": config["color"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }],
                    "username": f"4ex.ninja {config['name']}",
                    "avatar_url": self.branding["avatar_url"]
                }
                
                results[f"tier_{tier.value}"] = await self._send_webhook(config["url"], test_payload)
            else:
                results[f"tier_{tier.value}"] = False
        
        # Test system webhooks
        for webhook_type, webhook_url in self.system_webhooks.items():
            if webhook_url:
                success = await self.send_system_notification(
                    f"Test notification for {webhook_type} webhook",
                    "info",
                    webhook_type
                )
                results[f"system_{webhook_type}"] = success
            else:
                results[f"system_{webhook_type}"] = False
        
        return results


# Global enhanced Discord service instance
enhanced_discord_service = EnhancedDiscordService()


def get_enhanced_discord_service() -> EnhancedDiscordService:
    """Get the enhanced Discord service instance."""
    return enhanced_discord_service
