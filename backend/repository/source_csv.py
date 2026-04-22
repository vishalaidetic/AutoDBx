from typing import Optional
from uuid import UUID

from model.source_csv import SourceCSV
from sqlalchemy.orm import Session


class SourceCSVRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, source_csv: SourceCSV) -> SourceCSV:
        self.db.add(source_csv)
        self.db.commit()
        self.db.refresh(source_csv)
        return source_csv

    def get_by_id(self, source_csv_id: UUID) -> Optional[SourceCSV]:
        return self.db.query(SourceCSV).filter(SourceCSV.id == source_csv_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[SourceCSV]:
        return self.db.query(SourceCSV).offset(skip).limit(limit).all()

    def update(self, source_csv: SourceCSV, updates: dict) -> SourceCSV:
        for field, value in updates.items():
            if hasattr(source_csv, field):
                setattr(source_csv, field, value)
        self.db.commit()
        self.db.refresh(source_csv)
        return source_csv

    def delete(self, source_csv: SourceCSV) -> None:
        self.db.delete(source_csv)
        self.db.commit()
