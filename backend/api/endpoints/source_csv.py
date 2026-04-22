from uuid import UUID

from core.dependency import get_db
from fastapi import APIRouter, Depends
from schema.source_csv import SourceCSVCreate, SourceCSVUpdate
from service import source_csv as source_csv_svc
from sqlalchemy.orm import Session
from utils.custom_reponse import custom_response

router = APIRouter(prefix="/source-csv", tags=["Source CSV"])


@router.post("/", status_code=201)
def create_source_csv(payload: SourceCSVCreate, db: Session = Depends(get_db)):
    try:
        data = source_csv_svc.create_source_csv(db, payload)
        return custom_response(
            success=True,
            message="Source CSV record created successfully",
            data=data,
            status=201,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/")
def list_source_csvs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        data = source_csv_svc.list_source_csvs(db, skip=skip, limit=limit)
        return custom_response(
            success=True,
            message="Source CSV records fetched successfully",
            data=data,
            status=200,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/{source_csv_id}")
def get_source_csv(source_csv_id: UUID, db: Session = Depends(get_db)):
    try:
        data = source_csv_svc.get_source_csv(db, source_csv_id)
        return custom_response(
            success=True,
            message="Source CSV record fetched successfully",
            data=data,
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.patch("/{source_csv_id}")
def update_source_csv(
    source_csv_id: UUID, payload: SourceCSVUpdate, db: Session = Depends(get_db)
):
    try:
        data = source_csv_svc.update_source_csv(db, source_csv_id, payload)
        return custom_response(
            success=True,
            message="Source CSV record updated successfully",
            data=data,
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.delete("/{source_csv_id}", status_code=204)
def delete_source_csv(source_csv_id: UUID, db: Session = Depends(get_db)):
    try:
        source_csv_svc.delete_source_csv(db, source_csv_id)
        return custom_response(
            success=True,
            message="Source CSV record deleted successfully",
            status=204,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=404)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)
