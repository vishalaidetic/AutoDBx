from datetime import datetime
from typing import Optional
from uuid import UUID

from model.migration import Migration, MigrationStatus
from sqlalchemy.orm import Session


class MigrationRepository:
    def __init__(self, db: Session):
        self.db = db

    """
    Migration Repository
    --------------------
    Data access layer for the Migration model.
    All DB operations are synchronous (SQLAlchemy Core).
    The caller is responsible for providing an active Session via FastAPI's Depends(get_db).
    """

    def create(self, migration: Migration) -> Migration:
        """Persist a new Migration record."""
        self.db.add(migration)
        self.db.commit()
        self.db.refresh(migration)
        return migration

    def get_by_id(self, migration_id: UUID) -> Optional[Migration]:
        """Fetch a single Migration by its primary key."""
        return self.db.query(Migration).filter(Migration.id == migration_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Migration]:
        """Fetch a paginated list of all migrations."""
        return self.db.query(Migration).offset(skip).limit(limit).all()

    def get_by_status(self, status: MigrationStatus) -> list[Migration]:
        """Fetch all migrations with a given status."""
        return self.db.query(Migration).filter(Migration.status == status).all()

    def get_by_source_csv(self, source_csv_id: UUID) -> list[Migration]:
        """Fetch all migrations linked to a specific SourceCSV."""
        return (
            self.db.query(Migration)
            .filter(Migration.source_csv_id == source_csv_id)
            .all()
        )

    def update(self, migration: Migration, updates: dict) -> Migration:
        """Apply a dict of field updates to an existing Migration."""
        for field, value in updates.items():
            if hasattr(migration, field):
                setattr(migration, field, value)
        migration.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(migration)
        return migration

    def delete(self, migration: Migration) -> None:
        """Hard-delete a Migration record."""
        self.db.delete(migration)
        self.db.commit()
