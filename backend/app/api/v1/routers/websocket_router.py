"""WebSocket router for real-time updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set, Optional
import json
import asyncio

from app.services.auth_service import AuthService

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> set of channel names
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.subscriptions[websocket] = set()
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        self.subscriptions.pop(websocket, None)
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a connection to a channel"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe a connection from a channel"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections for a user"""
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except:
                    pass  # Connection may be closed
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast a message to all subscribers of a channel"""
        for ws, channels in self.subscriptions.items():
            if channel in channels:
                try:
                    await ws.send_json(message)
                except:
                    pass  # Connection may be closed
    
    def get_subscriber_count(self, channel: str) -> int:
        """Get the number of subscribers to a channel"""
        count = 0
        for channels in self.subscriptions.values():
            if channel in channels:
                count += 1
        return count


# Global connection manager instance
manager = ConnectionManager()


def verify_ws_token(token: str) -> Optional[str]:
    """Verify WebSocket authentication token and return user_id"""
    try:
        payload = AuthService.verify_token(token)
        if payload:
            return payload.sub
    except:
        pass
    return None


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with: ws://host/ws/connect?token=<jwt_token>
    
    Message protocol:
    - Subscribe: {"action": "subscribe", "channel": "quotes:AAPL"}
    - Unsubscribe: {"action": "unsubscribe", "channel": "quotes:AAPL"}
    
    Channel patterns:
    - quotes:{symbol} - Stock quote updates
    - portfolio:{user_id} - Portfolio value changes
    - notifications:{user_id} - User notifications
    - alerts:{rule_id} - Alert triggers
    - sync:{account_id} - Account sync status
    """
    # Verify authentication
    user_id = verify_ws_token(token) if token else None
    
    if not user_id:
        await websocket.close(code=4001)  # Unauthorized
        return
    
    # Accept connection
    await manager.connect(websocket, user_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "WebSocket connection established"
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            channel = data.get("channel")
            
            if action == "subscribe" and channel:
                # Validate channel access (e.g., user can only subscribe to their own portfolio)
                if channel.startswith("portfolio:") or channel.startswith("notifications:"):
                    channel_user_id = channel.split(":")[1]
                    if channel_user_id != user_id:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not authorized to subscribe to this channel"
                        })
                        continue
                
                await manager.subscribe(websocket, channel)
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": channel
                })
                
            elif action == "unsubscribe" and channel:
                await manager.unsubscribe(websocket, channel)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "channel": channel
                })
                
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# Helper functions to be used by other services
async def notify_user(user_id: str, notification: dict):
    """Send a notification to a specific user via WebSocket"""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": notification
    })


async def broadcast_quote(symbol: str, quote_data: dict):
    """Broadcast a quote update to all subscribers"""
    await manager.broadcast_to_channel(f"quotes:{symbol}", {
        "type": "quote",
        "symbol": symbol,
        "data": quote_data
    })


async def broadcast_portfolio_update(user_id: str, portfolio_data: dict):
    """Broadcast portfolio update to user"""
    await manager.broadcast_to_channel(f"portfolio:{user_id}", {
        "type": "portfolio_update",
        "data": portfolio_data
    })


async def broadcast_sync_status(account_id: str, status: dict):
    """Broadcast account sync status"""
    await manager.broadcast_to_channel(f"sync:{account_id}", {
        "type": "sync_status",
        "account_id": account_id,
        "data": status
    })
