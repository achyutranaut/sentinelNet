"""WebSocket Connection Manager for Streaming Alerts (SentinelNet Tier 5/6 Integration).

Manages active WebSocket dashboard connections, handles client disconnects gracefully,
and broadcasts scored threat alerts with attached SHAP explanations without crashing
or blocking the scoring pipeline.
"""

import asyncio
import logging
from typing import Any, Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

from src.api.schemas import AlertStreamItem

logger = logging.getLogger(__name__)


class AlertStreamManager:
    """Thread-safe and async connection manager for live alert streaming."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts WebSocket connection and registers client in subscriber pool."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        # Send initial confirmation message
        try:
            await websocket.send_json({
                "event": "SUBSCRIBED",
                "message": "Connected to SentinelNet Tier 5 live alert and TreeSHAP stream.",
                "active_subscribers": len(self.active_connections)
            })
        except (WebSocketDisconnect, RuntimeError):
            await self.disconnect(websocket)
        except Exception as e:
            logger.error("Failed to send initial subscription message to WebSocket client: %s", e, exc_info=True)
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Safely removes disconnected client from subscriber pool."""
        async with self._lock:
            self.active_connections.discard(websocket)

    async def broadcast_alert(self, alert: AlertStreamItem) -> int:
        """Broadcasts an alert to all active clients.

        Gracefully purges dead/disconnected connections without interrupting
        the scoring pipeline or failing for remaining clients.
        Returns the count of successful deliveries.
        """
        async with self._lock:
            clients = list(self.active_connections)

        if not clients:
            return 0

        payload = alert.model_dump()
        dead_clients: List[WebSocket] = []
        delivered = 0

        for ws in clients:
            try:
                await ws.send_json(payload)
                delivered += 1
            except (WebSocketDisconnect, RuntimeError):
                # Normal client disconnection or socket closure
                dead_clients.append(ws)
            except Exception as e:
                # Unexpected error (e.g. serialization or internal fault)
                logger.error("Unexpected error delivering alert to WebSocket client: %s", e, exc_info=True)
                dead_clients.append(ws)

        if dead_clients:
            async with self._lock:
                for ws in dead_clients:
                    self.active_connections.discard(ws)

        return delivered

    def subscriber_count(self) -> int:
        """Returns the current number of active WebSocket subscribers."""
        return len(self.active_connections)
