"""
WebSocket Notification Bridge for 4ex.ninja

This service extends the existing AsyncNotificationService to provide
real-time WebSocket notifications alongside Discord delivery.

Builds on:
- Existing AsyncNotificationService (already optimized to <500ms)
- Redis cache infrastructure for connection state management
- Current signal generation pipeline
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from core.entities.signal import Signal
from infrastructure.services.async_notification_service import (
    AsyncNotificationService,
    NotificationPriority,
)
from infrastructure.monitoring.alerts import Alert

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """WebSocket authentication types."""

    ANONYMOUS = "anonymous"
    SESSION = "session"
    WALLET = "wallet"


class AccessTier(Enum):
    """Access tiers for token-gated features."""

    FREE = "free"
    PREMIUM = "premium"
    HOLDER = "holder"
    WHALE = "whale"


@dataclass
class NotificationTarget:
    """Notification target for WebSocket delivery."""

    type: AuthType
    identifier: str
    access_tier: AccessTier
    token_balance: Optional[int] = None


@dataclass
class WebSocketConnection:
    """WebSocket connection metadata."""

    connection_id: str
    websocket: WebSocket
    target: NotificationTarget
    subscriptions: Set[str]
    connected_at: datetime
    last_activity: datetime


class WebSocketNotificationBridge:
    """
    Bridge between existing AsyncNotificationService and WebSocket connections.

    This service enables dual notification delivery:
    1. Discord notifications (existing, working)
    2. WebSocket notifications (new)
    """

    def __init__(self, async_notification_service: AsyncNotificationService):
        self.discord_service = async_notification_service
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids

        # Use existing Redis cache for connection state if available
        self.redis_client = None
        try:
            from infrastructure.cache.redis_cache_service import RedisCacheService

            self.redis_cache = RedisCacheService()
            logger.info("✅ WebSocket bridge will use Redis for connection state")
        except Exception as e:
            logger.warning(f"❌ Redis not available for WebSocket state: {e}")
            self.redis_cache = None

    async def connect_websocket(
        self, websocket: WebSocket, auth_data: Dict[str, Any]
    ) -> str:
        """
        Connect a new WebSocket client with authentication.

        Args:
            websocket: FastAPI WebSocket connection
            auth_data: Authentication data (wallet, session, or anonymous)

        Returns:
            str: Connection ID
        """
        await websocket.accept()

        connection_id = str(uuid.uuid4())
        target = await self._authenticate_connection(auth_data)

        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            target=target,
            subscriptions=set(),
            connected_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
        )

        self.connections[connection_id] = connection

        # Track user connections
        if target.identifier not in self.user_connections:
            self.user_connections[target.identifier] = set()
        self.user_connections[target.identifier].add(connection_id)

        # Store connection state in Redis if available
        if self.redis_cache:
            try:
                await self._store_connection_state(connection)
            except Exception as e:
                logger.warning(f"Failed to store connection state in Redis: {e}")

        logger.info(f"✅ WebSocket connected: {connection_id} ({target.type.value})")

        # Send welcome message with available channels
        await self._send_welcome_message(connection)

        return connection_id

    async def disconnect_websocket(self, connection_id: str):
        """Disconnect and cleanup WebSocket connection."""
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # Remove from user connections
            if connection.target.identifier in self.user_connections:
                self.user_connections[connection.target.identifier].discard(
                    connection_id
                )
                if not self.user_connections[connection.target.identifier]:
                    del self.user_connections[connection.target.identifier]

            # Cleanup Redis state
            if self.redis_cache:
                try:
                    await self._remove_connection_state(connection_id)
                except Exception as e:
                    logger.warning(f"Failed to remove connection state from Redis: {e}")

            del self.connections[connection_id]
            logger.info(f"✅ WebSocket disconnected: {connection_id}")

    async def broadcast_signal(
        self,
        signal: Signal,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ):
        """
        Broadcast signal to both Discord and WebSocket connections.

        This maintains the existing Discord notification functionality
        while adding WebSocket delivery.
        """
        # 1. Send to Discord using existing AsyncNotificationService (already working)
        try:
            await self.discord_service.queue_notification(
                signal_data=signal, priority=priority  # Pass Signal object directly
            )
            logger.debug(f"✅ Signal queued for Discord: {signal.signal_id}")
        except Exception as e:
            logger.error(f"❌ Failed to queue Discord notification: {e}")

        # 2. Send to WebSocket connections (new functionality)
        await self._broadcast_to_websockets(signal)

    async def _broadcast_to_websockets(self, signal: Signal):
        """Broadcast signal to connected WebSocket clients."""
        if not self.connections:
            logger.debug("No WebSocket connections to broadcast to")
            return

        # Get available channels for signal
        available_channels = self._get_signal_channels(signal)

        # Prepare WebSocket message
        message = {
            "type": "signal",
            "data": {
                "signal_id": signal.signal_id,
                "pair": signal.pair,
                "signal_type": signal.signal_type.value if signal.signal_type else None,
                "entry_price": (
                    float(signal.entry_price) if signal.entry_price else None
                ),
                "confidence_score": (
                    float(signal.confidence_score) if signal.confidence_score else None
                ),
                "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
                "channel": available_channels[0] if available_channels else "public",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Send to appropriate connections
        disconnected_connections = []
        sent_count = 0

        for connection_id, connection in self.connections.items():
            try:
                # Check if user has access to any of the signal's channels
                user_channels = self._get_user_channels(connection.target)
                if any(channel in user_channels for channel in available_channels):
                    await connection.websocket.send_text(json.dumps(message))
                    connection.last_activity = datetime.now(timezone.utc)
                    sent_count += 1
                    logger.debug(f"✅ Signal sent to WebSocket: {connection_id}")

            except WebSocketDisconnect:
                disconnected_connections.append(connection_id)
            except Exception as e:
                logger.error(f"❌ Failed to send to WebSocket {connection_id}: {e}")
                disconnected_connections.append(connection_id)

        # Cleanup disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect_websocket(connection_id)

        logger.info(f"✅ Signal broadcast to {sent_count} WebSocket connections")

    async def _authenticate_connection(
        self, auth_data: Dict[str, Any]
    ) -> NotificationTarget:
        """
        Authenticate WebSocket connection with progressive enhancement.

        Support three authentication types:
        1. Wallet (future-ready for token gating)
        2. Session (current NextAuth.js)
        3. Anonymous (public access)
        """
        # Wallet authentication (placeholder for future token integration)
        if auth_data.get("walletAddress"):
            return NotificationTarget(
                type=AuthType.WALLET,
                identifier=auth_data["walletAddress"],
                access_tier=AccessTier.FREE,  # Will be token-balance based later
                token_balance=0,
            )

        # Session authentication (current system)
        elif auth_data.get("sessionToken"):
            # For now, treat session users as premium
            # This will integrate with existing NextAuth.js
            return NotificationTarget(
                type=AuthType.SESSION,
                identifier=auth_data.get("userId", "session_user"),
                access_tier=AccessTier.PREMIUM,
            )

        # Anonymous access (public signals only)
        else:
            anonymous_id = auth_data.get("anonymousId", str(uuid.uuid4()))
            return NotificationTarget(
                type=AuthType.ANONYMOUS,
                identifier=anonymous_id,
                access_tier=AccessTier.FREE,
            )

    def _get_signal_channels(self, signal: Signal) -> List[str]:
        """
        Determine which channels a signal should be broadcast to.

        This will expand with token-gated features.
        """
        channels = ["public"]  # All signals go to public channel

        # Add premium channels based on signal quality
        if hasattr(signal, "confidence_score") and signal.confidence_score:
            if signal.confidence_score > 0.8:
                channels.append("premium")
            if signal.confidence_score > 0.9:
                channels.append("whale")

        return channels

    def _get_user_channels(self, target: NotificationTarget) -> List[str]:
        """Get available channels for a user based on their access tier."""
        channels = ["public"]  # Everyone gets public

        if target.access_tier in [
            AccessTier.PREMIUM,
            AccessTier.HOLDER,
            AccessTier.WHALE,
        ]:
            channels.append("premium")

        if target.access_tier == AccessTier.WHALE:
            channels.append("whale")

        return channels

    async def _send_welcome_message(self, connection: WebSocketConnection):
        """Send welcome message with available channels."""
        available_channels = self._get_user_channels(connection.target)

        welcome_msg = {
            "type": "welcome",
            "data": {
                "connection_id": connection.connection_id,
                "auth_type": connection.target.type.value,
                "access_tier": connection.target.access_tier.value,
                "available_channels": available_channels,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            await connection.websocket.send_text(json.dumps(welcome_msg))
            logger.debug(f"✅ Welcome message sent to {connection.connection_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send welcome message: {e}")

    async def _store_connection_state(self, connection: WebSocketConnection):
        """Store connection state in Redis for scalability."""
        if not self.redis_cache:
            return

        # Use a simple string-based storage since we don't have set_with_expiry
        state_data = {
            "target_type": connection.target.type.value,
            "target_identifier": connection.target.identifier,
            "access_tier": connection.target.access_tier.value,
            "connected_at": connection.connected_at.isoformat(),
            "subscriptions": list(connection.subscriptions),
        }

        # Store for 1 hour (3600 seconds)
        key = f"websocket_connection_{connection.connection_id}"
        try:
            # Use Redis client directly if available
            if (
                hasattr(self.redis_cache, "redis_client")
                and self.redis_cache.redis_client
            ):
                await self.redis_cache.redis_client.setex(
                    key, 3600, json.dumps(state_data)
                )
        except Exception as e:
            logger.warning(f"Failed to store connection state: {e}")

    async def _remove_connection_state(self, connection_id: str):
        """Remove connection state from Redis."""
        if not self.redis_cache:
            return

        key = f"websocket_connection_{connection_id}"
        try:
            if (
                hasattr(self.redis_cache, "redis_client")
                and self.redis_cache.redis_client
            ):
                await self.redis_cache.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Failed to remove connection state: {e}")

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics for monitoring."""
        stats = {
            "total_connections": len(self.connections),
            "connections_by_type": {},
            "connections_by_tier": {},
            "active_users": len(self.user_connections),
        }

        for connection in self.connections.values():
            # Count by auth type
            auth_type = connection.target.type.value
            stats["connections_by_type"][auth_type] = (
                stats["connections_by_type"].get(auth_type, 0) + 1
            )

            # Count by access tier
            access_tier = connection.target.access_tier.value
            stats["connections_by_tier"][access_tier] = (
                stats["connections_by_tier"].get(access_tier, 0) + 1
            )

        return stats


# Global instance to be used by FastAPI routes
_websocket_bridge: Optional[WebSocketNotificationBridge] = None


def get_websocket_bridge() -> WebSocketNotificationBridge:
    """Get the global WebSocket bridge instance."""
    global _websocket_bridge
    if _websocket_bridge is None:
        # Initialize with existing AsyncNotificationService
        from infrastructure.services.async_notification_service import (
            AsyncNotificationService,
        )

        async_service = AsyncNotificationService()
        _websocket_bridge = WebSocketNotificationBridge(async_service)
    return _websocket_bridge


async def initialize_websocket_bridge():
    """Initialize the WebSocket bridge service."""
    get_websocket_bridge()
    logger.info("✅ WebSocket notification bridge initialized")
