from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from model.migration import Migration, MigrationStatus
from repository.migration import MigrationRepository
from schema.migration import (
    MigrationCreate,
    MigrationListResponse,
    MigrationResponse,
    MigrationStepUpdate,
    MigrationUpdate,
)
from sqlalchemy.orm import Session


def _derive_overall_status(step_status: MigrationStatus) -> MigrationStatus:
    """
    Map an individual step status to the overall migration status.
      FAILED  → overall FAILED
      RUNNING → overall RUNNING
      SUCCESS → overall RUNNING  (caller marks final SUCCESS explicitly)
      PENDING → overall PENDING
    """
    mapping = {
        MigrationStatus.FAILED: MigrationStatus.FAILED,
        MigrationStatus.RUNNING: MigrationStatus.RUNNING,
        MigrationStatus.SUCCESS: MigrationStatus.RUNNING,
        MigrationStatus.PENDING: MigrationStatus.PENDING,
    }
    return mapping.get(step_status, MigrationStatus.RUNNING)


def _get_or_raise(repo: MigrationRepository, migration_id: UUID) -> Migration:
    """Fetch a migration by ID or raise ValueError."""
    migration = repo.get_by_id(migration_id)
    if not migration:
        raise ValueError(f"Migration '{migration_id}' not found.")
    return migration


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_migration(db: Session, payload: MigrationCreate) -> MigrationResponse:
    """Create a new Migration record with PENDING status."""
    migration = Migration(
        id=uuid4(),
        description=payload.description,
        status=MigrationStatus.PENDING,
        source_csv_id=payload.source_csv_id,
    )
    created = MigrationRepository(db).create(migration)
    return MigrationResponse.from_orm(created)


def get_migration(db: Session, migration_id: UUID) -> MigrationResponse:
    """Retrieve a migration by ID, raises ValueError if not found."""
    migration = _get_or_raise(MigrationRepository(db), migration_id)
    return MigrationResponse.from_orm(migration)


def list_migrations(
    db: Session, skip: int = 0, limit: int = 100
) -> MigrationListResponse:
    """Return a paginated list of all migrations."""
    items = MigrationRepository(db).get_all(skip=skip, limit=limit)
    return MigrationListResponse(
        total=len(items),
        items=[MigrationResponse.from_orm(m) for m in items],
    )


def list_by_status(db: Session, status: MigrationStatus) -> MigrationListResponse:
    """Return all migrations with the given status."""
    items = MigrationRepository(db).get_by_status(status)
    return MigrationListResponse(
        total=len(items),
        items=[MigrationResponse.from_orm(m) for m in items],
    )


def list_by_source_csv(db: Session, source_csv_id: UUID) -> MigrationListResponse:
    """Return all migrations linked to a specific SourceCSV."""
    items = MigrationRepository(db).get_by_source_csv(source_csv_id)
    return MigrationListResponse(
        total=len(items),
        items=[MigrationResponse.from_orm(m) for m in items],
    )


def update_validate_step(
    db: Session, migration_id: UUID, payload: MigrationStepUpdate
) -> MigrationResponse:
    """Update the validate-bundle step result for a migration."""
    repo = MigrationRepository(db)
    migration = _get_or_raise(repo, migration_id)
    now = datetime.utcnow()
    updates = {
        "validate_bundle_status": payload.status,
        "validate_bundle_meta_data": payload.meta_data,
        "status": _derive_overall_status(payload.status),
    }
    if payload.status == MigrationStatus.RUNNING:
        updates["validate_start_time"] = now
    else:
        updates["validate_completion_time"] = now
    return MigrationResponse.from_orm(repo.update(migration, updates))


def update_deploy_step(
    db: Session, migration_id: UUID, payload: MigrationStepUpdate
) -> MigrationResponse:
    """Update the deploy-bundle step result for a migration."""
    repo = MigrationRepository(db)
    migration = _get_or_raise(repo, migration_id)
    now = datetime.utcnow()
    updates = {
        "deploy_bundle_status": payload.status,
        "deploy_bundle_meta_data": payload.meta_data,
        "status": _derive_overall_status(payload.status),
    }
    if payload.status == MigrationStatus.RUNNING:
        updates["deploy_start_time"] = now
    else:
        updates["deploy_completion_time"] = now
    return MigrationResponse.from_orm(repo.update(migration, updates))


def update_config_table_step(
    db: Session, migration_id: UUID, payload: MigrationStepUpdate
) -> MigrationResponse:
    """Update the config-table-creation step result for a migration."""
    repo = MigrationRepository(db)
    migration = _get_or_raise(repo, migration_id)
    now = datetime.utcnow()
    updates = {
        "config_table_status": payload.status,
        "config_table_meta_data": payload.meta_data,
        "status": _derive_overall_status(payload.status),
    }
    if payload.status == MigrationStatus.RUNNING:
        updates["config_table_start_time"] = now
    else:
        updates["config_table_completion_time"] = now
    return MigrationResponse.from_orm(repo.update(migration, updates))


def update_migration_job_step(
    db: Session, migration_id: UUID, payload: MigrationStepUpdate
) -> MigrationResponse:
    """Update the migration-job step result for a migration."""
    repo = MigrationRepository(db)
    migration = _get_or_raise(repo, migration_id)
    now = datetime.utcnow()
    updates = {
        "migration_job_status": payload.status,
        "migration_job_meta_data": payload.meta_data,
        "status": _derive_overall_status(payload.status),
    }
    if payload.status == MigrationStatus.RUNNING:
        updates["migration_job_start_time"] = now
    else:
        updates["migration_job_completion_time"] = now
    return MigrationResponse.from_orm(repo.update(migration, updates))


def update_migration(
    db: Session, migration_id: UUID, payload: MigrationUpdate
) -> MigrationResponse:
    """Apply partial field-level updates to a migration."""
    repo = MigrationRepository(db)
    migration = _get_or_raise(repo, migration_id)
    updates = payload.model_dump(exclude_none=True)
    updated = repo.update(migration, updates)
    return MigrationResponse.from_orm(updated)


def delete_migration(db: Session, migration_id: UUID) -> None:
    """Hard-delete a migration by ID."""
    repo = MigrationRepository(db)
    migration = _get_or_raise(repo, migration_id)
    repo.delete(migration)
