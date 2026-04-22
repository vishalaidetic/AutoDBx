from typing import Optional
from uuid import UUID, uuid4

from model.source_csv import SourceCSV
from repository.source_csv import SourceCSVRepository
from schema.source_csv import SourceCSVCreate, SourceCSVResponse, SourceCSVUpdate
from sqlalchemy.orm import Session


def _get_or_raise(repo: SourceCSVRepository, source_csv_id: UUID) -> SourceCSV:
    source_csv = repo.get_by_id(source_csv_id)
    if not source_csv:
        raise ValueError(f"SourceCSV '{source_csv_id}' not found.")
    return source_csv


def create_source_csv(db: Session, payload: SourceCSVCreate) -> SourceCSVResponse:
    source_csv = SourceCSV(id=uuid4(), **payload.model_dump())
    created = SourceCSVRepository(db).create(source_csv)
    return SourceCSVResponse.from_attributes(created)


def get_source_csv(db: Session, source_csv_id: UUID) -> SourceCSVResponse:
    repo = SourceCSVRepository(db)
    source_csv = _get_or_raise(repo, source_csv_id)
    return SourceCSVResponse.from_attributes(source_csv)


def list_source_csvs(
    db: Session, skip: int = 0, limit: int = 100
) -> list[SourceCSVResponse]:
    items = SourceCSVRepository(db).get_all(skip=skip, limit=limit)
    return [SourceCSVResponse.from_attributes(item) for item in items]


def update_source_csv(
    db: Session, source_csv_id: UUID, payload: SourceCSVUpdate
) -> SourceCSVResponse:
    repo = SourceCSVRepository(db)
    source_csv = _get_or_raise(repo, source_csv_id)
    updates = payload.model_dump(exclude_none=True)
    updated = repo.update(source_csv, updates)
    return SourceCSVResponse.from_attributes(updated)


def delete_source_csv(db: Session, source_csv_id: UUID) -> None:
    repo = SourceCSVRepository(db)
    source_csv = _get_or_raise(repo, source_csv_id)
    repo.delete(source_csv)
