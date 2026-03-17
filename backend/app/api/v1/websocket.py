"""
WebSocket endpoints for real-time optimization progress updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for optimization tasks."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task: {task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """Remove a WebSocket connection."""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task: {task_id}")

    async def broadcast(self, task_id: str, message: dict) -> None:
        """Broadcast a message to all connections for a task."""
        if task_id not in self.active_connections:
            return

        dead_connections: Set[WebSocket] = set()
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        self.active_connections[task_id] -= dead_connections

    async def send_progress(
        self,
        task_id: str,
        progress: float,
        current_step: str
    ) -> None:
        """Send a progress update."""
        await self.broadcast(task_id, {
            "type": "progress",
            "progress": progress,
            "current_step": current_step
        })

    async def send_step_complete(
        self,
        task_id: str,
        step: str,
        result: str
    ) -> None:
        """Send a step completion notification."""
        await self.broadcast(task_id, {
            "type": "step_complete",
            "step": step,
            "result": result
        })

    async def send_completed(
        self,
        task_id: str,
        result: dict
    ) -> None:
        """Send a task completion notification."""
        await self.broadcast(task_id, {
            "type": "completed",
            "result": result
        })

    async def send_error(
        self,
        task_id: str,
        error: str
    ) -> None:
        """Send an error notification."""
        await self.broadcast(task_id, {
            "type": "error",
            "error": error
        })


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task progress updates.

    Message types sent to client:
    - connected: Connection established
    - subscribed: Subscription confirmed
    - progress: Progress update with percentage and current step
    - step_complete: A step has completed
    - completed: Task finished with final result
    - error: An error occurred

    Message types received from client:
    - ping: Keep-alive ping
    - subscribe: Subscribe to task updates
    """
    await manager.connect(websocket, task_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "WebSocket connection established"
        })

        while True:
            # Wait for client messages (ping/pong or subscription updates)
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type", "unknown")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "subscribe":
                    # Client subscribing to task updates
                    await websocket.send_json({
                        "type": "subscribed",
                        "task_id": task_id
                    })
                else:
                    logger.debug(f"Received unknown message type: {msg_type}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, task_id)


def get_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
