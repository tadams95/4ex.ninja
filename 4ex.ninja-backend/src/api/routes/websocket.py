"""
WebSocket API Routes for 4ex.ninja

This module provides WebSocket endpoints for real-time signal notifications.
Integrates with existing AsyncNotificationService infrastructure.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from infrastructure.services.websocket_notification_bridge import (
    get_websocket_bridge,
    WebSocketNotificationBridge,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    # Authentication parameters (optional)
    walletAddress: Optional[str] = Query(None),
    sessionToken: Optional[str] = Query(None),
    anonymousId: Optional[str] = Query(None),
    bridge: WebSocketNotificationBridge = Depends(get_websocket_bridge),
):
    """
    WebSocket endpoint for real-time signal notifications.

    Supports three authentication methods:
    1. Wallet-based (future token gating): ?walletAddress=0x...
    2. Session-based (current system): ?sessionToken=jwt_token
    3. Anonymous (public access): ?anonymousId=uuid or auto-generated

    Example connections:
    - ws://localhost:8000/ws/notifications?sessionToken=your_jwt_token
    - ws://localhost:8000/ws/notifications?walletAddress=0x1234...
    - ws://localhost:8000/ws/notifications (anonymous)
    """
    connection_id = None

    try:
        # Prepare authentication data
        auth_data = {}
        if walletAddress:
            auth_data["walletAddress"] = walletAddress
        elif sessionToken:
            auth_data["sessionToken"] = sessionToken
            # In a real implementation, you'd validate the JWT and extract userId
            # For now, we'll use a placeholder
            auth_data["userId"] = "session_user"
        else:
            auth_data["anonymousId"] = anonymousId

        # Connect to WebSocket bridge
        connection_id = await bridge.connect_websocket(websocket, auth_data)
        logger.info(f"✅ WebSocket client connected: {connection_id}")

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (heartbeat, subscriptions, etc.)
                message = await websocket.receive_text()
                await handle_client_message(websocket, connection_id, message, bridge)

            except WebSocketDisconnect:
                logger.info(f"✅ WebSocket client disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"❌ Error handling WebSocket message: {e}")
                # Continue trying to handle messages

    except WebSocketDisconnect:
        logger.info(f"✅ WebSocket client disconnected during setup: {connection_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Cleanup connection
        if connection_id:
            await bridge.disconnect_websocket(connection_id)


async def handle_client_message(
    websocket: WebSocket,
    connection_id: str,
    message: str,
    bridge: WebSocketNotificationBridge,
):
    """Handle incoming messages from WebSocket clients."""
    try:
        data = json.loads(message)
        message_type = data.get("type", "unknown")

        if message_type == "heartbeat":
            # Respond to heartbeat
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "heartbeat_ack",
                        "timestamp": bridge.connections[
                            connection_id
                        ].last_activity.isoformat(),
                    }
                )
            )

        elif message_type == "subscribe":
            # Handle subscription requests (future implementation)
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "subscription_ack",
                        "data": {"message": "Subscriptions not yet implemented"},
                    }
                )
            )

        elif message_type == "get_stats":
            # Return connection statistics
            stats = await bridge.get_connection_stats()
            await websocket.send_text(json.dumps({"type": "stats", "data": stats}))

        else:
            logger.warning(f"Unknown message type: {message_type}")

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received from {connection_id}: {message}")
    except Exception as e:
        logger.error(f"Error handling message from {connection_id}: {e}")


@router.get("/stats")
async def get_websocket_stats(
    bridge: WebSocketNotificationBridge = Depends(get_websocket_bridge),
):
    """Get WebSocket connection statistics."""
    return await bridge.get_connection_stats()


# Health check endpoint for WebSocket service
@router.get("/health")
async def websocket_health(
    bridge: WebSocketNotificationBridge = Depends(get_websocket_bridge),
):
    """WebSocket service health check."""
    stats = await bridge.get_connection_stats()
    return {
        "status": "healthy",
        "service": "websocket-notifications",
        "connections": stats["total_connections"],
        "timestamp": stats,
    }
