"""
WebSocket Connection Manager
----------------------------
Maintains a registry of active WebSocket connections keyed by migration_id.
Each migration_id acts as its own isolated "room".
"""

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, migration_id: Any, websocket: WebSocket) -> None:
        """Accept and register a WebSocket into the migration room."""
        await websocket.accept()
        room = str(migration_id)
        if room not in self._rooms:
            self._rooms[room] = []
        self._rooms[room].append(websocket)

    def disconnect(self, migration_id: Any, websocket: WebSocket) -> None:
        """Remove a WebSocket from the migration room."""
        room = str(migration_id)
        if room in self._rooms:
            (
                self._rooms[room].discard(websocket)
                if hasattr(self._rooms[room], "discard")
                else None
            )
            try:
                self._rooms[room].remove(websocket)
            except ValueError:
                pass
            if not self._rooms[room]:
                del self._rooms[room]

    async def send_to_room(self, migration_id: Any, message: dict[str, Any]) -> None:
        """Broadcast a JSON message to all clients in a migration room."""
        room = str(migration_id)
        dead = []
        for ws in self._rooms.get(room, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(migration_id, ws)

    async def send_log(
        self, migration_id: Any, step: str, log: str, exit_code: int | None = None
    ) -> None:
        """Send a structured log line to all clients in a room."""
        await self.send_to_room(
            migration_id,
            {
                "type": "log",
                "step": step,
                "log": log,
                "exit_code": exit_code,
            },
        )

    async def send_step_status(
        self, migration_id: Any, step: str, status: str, meta: dict | None = None
    ) -> None:
        """Notify all clients in a room of a step status change."""
        await self.send_to_room(
            migration_id,
            {
                "type": "step_status",
                "step": step,
                "status": status,
                "meta": meta or {},
            },
        )

    async def send_error(self, migration_id: Any, step: str, error: str) -> None:
        """Send an error event to all clients in a room."""
        await self.send_to_room(
            migration_id,
            {"type": "error", "step": step, "error": error},
        )


manager = ConnectionManager()
