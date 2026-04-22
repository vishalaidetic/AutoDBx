from datetime import datetime
from enum import Enum
from uuid import uuid4

from core.database import Base
from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class MigrationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Migration(Base):
    __tablename__ = "migration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(MigrationStatus), default=MigrationStatus.PENDING, nullable=False
    )

    validate_bundle_status = Column(SAEnum(MigrationStatus), nullable=True)
    validate_bundle_meta_data = Column(JSON, nullable=True)
    validate_start_time = Column(DateTime, nullable=True)
    validate_completion_time = Column(DateTime, nullable=True)

    deploy_bundle_status = Column(SAEnum(MigrationStatus), nullable=True)
    deploy_bundle_meta_data = Column(JSON, nullable=True)
    deploy_start_time = Column(DateTime, nullable=True)
    deploy_completion_time = Column(DateTime, nullable=True)

    config_table_status = Column(SAEnum(MigrationStatus), nullable=True)
    config_table_meta_data = Column(JSON, nullable=True)
    config_table_start_time = Column(DateTime, nullable=True)
    config_table_completion_time = Column(DateTime, nullable=True)

    migration_job_status = Column(SAEnum(MigrationStatus), nullable=True)
    migration_job_meta_data = Column(JSON, nullable=True)
    migration_job_start_time = Column(DateTime, nullable=True)
    migration_job_completion_time = Column(DateTime, nullable=True)

    source_csv_id = Column(
        UUID(as_uuid=True), ForeignKey("source_csv.id"), nullable=True
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    source_csv = relationship("SourceCSV", back_populates="migrations")
