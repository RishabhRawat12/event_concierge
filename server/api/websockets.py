import asyncio
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from infrastructure.redis import cache

logger = logging.getLogger(__name__)
router = APIRouter()

class TacticalStreamManager:
    """Manages real-time situational awareness via Redis PubSub."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Situational link established. Active streams: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info(f"Situational link released. Active streams: {len(self.active_connections)}")

    async def broadcast_redis_updates(self, channel: str = "venue_updates") -> None:
        """Subscribes to Redis PubSub and pushes raw payloads to all active WebSockets."""
        logger.info(f"Subscribing to tactical channel: {channel}")
        ps = await cache.subscribe(channel)
        if not ps:
            logger.error("Redis PubSub subscription failed. Real-time stream unavailable.")
            return

        try:
            async for message in ps.listen():
                if message["type"] == "message":
                    payload = message["data"]
                    # Push to all active links
                    if self.active_connections:
                        await asyncio.gather(*[
                            ws.send_text(payload) for ws in self.active_connections
                        ], return_exceptions=True)
        except Exception as e:
            logger.error(f"WebSocket broadcast anomaly: {e}")
        finally:
            await ps.unsubscribe(channel)

stream_manager = TacticalStreamManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Entry point for attendee/staff real-time synchronization."""
    await stream_manager.connect(websocket)
    try:
        while True:
            # Keep-alive loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception:
        stream_manager.disconnect(websocket)
