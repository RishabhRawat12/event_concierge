"""
Real-time situational awareness via WebSocket orchestration.
Enables low-latency tactical broadcasting to all connected staff nodes.
"""
import asyncio
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections for tactical broadcasting."""

    def __init__(self) -> None:
        self._active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts and registers a new tactical connection."""
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.debug(f"Tactical node connected. Active channel count: {len(self._active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes a tactical node from the active registry."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
            logger.debug(f"Tactical node released. Remaining channels: {len(self._active_connections)}")

    async def broadcast(self, message: str) -> None:
        """
        Broadcats a tactical protocol to all connected nodes concurrently.
        Uses concurrent execution to prevent head-of-line blocking by slow nodes.
        """
        if not self._active_connections:
            return

        async def _safe_send(conn: WebSocket) -> None:
            try:
                await conn.send_text(message)
            except Exception:
                self.disconnect(conn)

        # Batch execution of tactical updates
        await asyncio.gather(*[_safe_send(c) for c in list(self._active_connections)])

ws_manager = ConnectionManager()

