from uuid import UUID

from core.dependency import get_db
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from service import migration as migration_svc
from sqlalchemy.orm import Session
from websocket.manager import manager

ws_router = APIRouter(tags=["Migration WebSocket"])


@ws_router.websocket("/ws/migrations/{migration_id}")
async def migration_ws(
    migration_id: str, websocket: WebSocket, db: Session = Depends(get_db)
):
    await manager.connect(migration_id, websocket)
    try:
        # Optionally send current DB state on connect so UI can restore progress
        try:
            current = migration_svc.get_migration(db, UUID(migration_id))
            await websocket.send_json(
                {"type": "init", "migration": current.model_dump(mode="json")}
            )
        except (ValueError, NameError) as e:
            await websocket.send_json(
                {"type": "error", "error": f"Initialization failed: {str(e)}"}
            )
            return

        # Keep connection alive — pipeline pushes, client may send pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(migration_id, websocket)
    except Exception as e:
        await websocket.send_json(
            {"type": "error", "error": f"Internal server error: {str(e)}"}
        )
        manager.disconnect(migration_id, websocket)
