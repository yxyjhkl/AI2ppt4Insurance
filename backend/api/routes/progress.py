"""WebSocket endpoint for real-time progress updates."""
from __future__ import annotations
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import asyncio

router = APIRouter()

# Store active connections
active_connections: dict[str, WebSocket] = {}


@router.websocket("/ws/progress/{task_id}")
async def progress_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for receiving progress updates."""
    await websocket.accept()
    active_connections[task_id] = websocket
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_text('{"type": "ping"}')
    except WebSocketDisconnect:
        del active_connections[task_id]
    except Exception:
        if task_id in active_connections:
            del active_connections[task_id]


async def send_progress(task_id: str, progress: dict):
    """Send progress update to connected client."""
    if task_id in active_connections:
        try:
            import json
            await active_connections[task_id].send_text(json.dumps({
                "type": "progress",
                **progress
            }))
        except Exception:
            # Remove dead connection
            del active_connections[task_id]
