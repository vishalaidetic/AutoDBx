from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from model.migration import MigrationStatus
from pydantic import BaseModel, ConfigDict


class MigrationBase(BaseModel):
    description: Optional[str] = None
    source_csv_id: Optional[UUID] = None


class MigrationCreate(MigrationBase):
    """Payload to create a new migration record."""

    pass


class MigrationStepUpdate(BaseModel):
    """Payload to update a single pipeline step."""

    status: MigrationStatus
    meta_data: Optional[dict[str, Any]] = None


class MigrationUpdate(BaseModel):
    """Generic partial update — all fields optional."""

    description: Optional[str] = None
    status: Optional[MigrationStatus] = None
    source_csv_id: Optional[UUID] = None


class ValidateBundleStep(BaseModel):
    status: Optional[MigrationStatus] = None
    meta_data: Optional[dict[str, Any]] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None


class DeployBundleStep(BaseModel):
    status: Optional[MigrationStatus] = None
    meta_data: Optional[dict[str, Any]] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None


class ConfigTableStep(BaseModel):
    status: Optional[MigrationStatus] = None
    meta_data: Optional[dict[str, Any]] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None


class MigrationJobStep(BaseModel):
    status: Optional[MigrationStatus] = None
    meta_data: Optional[dict[str, Any]] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None


class MigrationResponse(BaseModel):
    """Full migration record returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: Optional[str] = None
    status: MigrationStatus
    source_csv_id: Optional[UUID] = None

    validate_bundle: ValidateBundleStep
    deploy_bundle: DeployBundleStep
    config_table: ConfigTableStep
    migration_job: MigrationJobStep

    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "MigrationResponse":
        return cls(
            id=obj.id,
            description=obj.description,
            status=obj.status,
            source_csv_id=obj.source_csv_id,
            validate_bundle=ValidateBundleStep(
                status=obj.validate_bundle_status,
                meta_data=obj.validate_bundle_meta_data,
                start_time=obj.validate_start_time,
                completion_time=obj.validate_completion_time,
            ),
            deploy_bundle=DeployBundleStep(
                status=obj.deploy_bundle_status,
                meta_data=obj.deploy_bundle_meta_data,
                start_time=obj.deploy_start_time,
                completion_time=obj.deploy_completion_time,
            ),
            config_table=ConfigTableStep(
                status=obj.config_table_status,
                meta_data=obj.config_table_meta_data,
                start_time=obj.config_table_start_time,
                completion_time=obj.config_table_completion_time,
            ),
            migration_job=MigrationJobStep(
                status=obj.migration_job_status,
                meta_data=obj.migration_job_meta_data,
                start_time=obj.migration_job_start_time,
                completion_time=obj.migration_job_completion_time,
            ),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class MigrationListResponse(BaseModel):
    """Paginated list of migrations."""

    total: int
    items: list[MigrationResponse]
