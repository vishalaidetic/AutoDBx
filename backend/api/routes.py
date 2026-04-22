from api.endpoints.aws import router as aws_router
from api.endpoints.databricks import router as databricks_router
from api.endpoints.migration import router as migration_router
from api.endpoints.source_csv import router as source_csv_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(migration_router)
router.include_router(source_csv_router)
router.include_router(databricks_router)
router.include_router(aws_router)
