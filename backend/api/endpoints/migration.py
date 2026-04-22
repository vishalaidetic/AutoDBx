import os
from uuid import UUID

from core.dependency import get_db
from fastapi import APIRouter, BackgroundTasks, Depends
from model.migration import MigrationStatus
from schema.migration import MigrationCreate, MigrationUpdate
from service import migration as migration_svc
from service.pipeline import AUTO_DBX_ROOT, get_project_working_dir, run_step
from sqlalchemy.orm import Session
from utils.custom_reponse import custom_response
from utils.file_utils import list_subdirectories

router = APIRouter(prefix="/migrations", tags=["Migration"])
ws_router = APIRouter(tags=["Migration WebSocket"])


@router.post("/", status_code=201)
def create_migration(payload: MigrationCreate, db: Session = Depends(get_db)):
    """
    Step 1 — Create a Migration entity when the user moves from Preview → Execution.
    Returns the migration_id used to open the WebSocket connection.
    """
    try:
        data = migration_svc.create_migration(db, payload)
        return custom_response(
            success=True,
            message="Migration created successfully",
            data=data,
            status=201,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/")
def list_migrations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        data = migration_svc.list_migrations(db, skip=skip, limit=limit)
        return custom_response(
            success=True,
            message="Migrations fetched successfully",
            data=data,
            status=200,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/folders")
async def get_autodbx_folders():
    """
    Fetches the list of subdirectories within the AutoDBx folder.
    """
    autodbx_path = AUTO_DBX_ROOT

    if not os.path.isdir(autodbx_path):
        return custom_response(
            success=False,
            message=f"AutoDBx directory not found at {autodbx_path}",
            status=404,
        )
    try:
        folders = list_subdirectories(autodbx_path)
        return custom_response(
            success=True,
            message="Folders fetched successfully",
            data={"folders": folders},
            status=200,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/{migration_id}")
def get_migration(migration_id: UUID, db: Session = Depends(get_db)):
    try:
        data = migration_svc.get_migration(db, migration_id)
        return custom_response(
            success=True,
            message="Migration fetched successfully",
            data=data,
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.patch("/{migration_id}")
def update_migration(
    migration_id: UUID, payload: MigrationUpdate, db: Session = Depends(get_db)
):
    try:
        data = migration_svc.update_migration(db, migration_id, payload)
        return custom_response(
            success=True,
            message="Migration updated successfully",
            data=data,
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.delete("/{migration_id}", status_code=204)
def delete_migration(migration_id: UUID, db: Session = Depends(get_db)):
    try:
        migration_svc.delete_migration(db, migration_id)
        return custom_response(
            success=True,
            message="Migration deleted successfully",
            status=204,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.post("/{migration_id}/run/{step_key}")
def run_migration(
    migration_id: UUID,
    step_key: str,
    project_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Step 3 — Trigger a specific pipeline step in the background.
    Output streams in real-time over the WebSocket room for this migration_id.
    """
    try:
        migration = migration_svc.get_migration(db, migration_id)
        project_dir = get_project_working_dir(project_name)

        background_tasks.add_task(
            run_step,
            migration_id,
            step_key,
            project_dir,
        )

        return custom_response(
            success=True,
            message=f"Pipeline step '{step_key}' triggered successfully",
            data=migration,
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)
