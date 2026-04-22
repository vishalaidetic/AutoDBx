from fastapi import APIRouter, File, HTTPException, UploadFile
from utils.aws_file_handler import AWSFileHandler
from utils.custom_reponse import custom_response

router = APIRouter(prefix="/aws", tags=["AWS S3"])


@router.post("/upload")
async def upload_s3_file(file: UploadFile = File(...)):
    """Uploads a file to S3."""
    handler = AWSFileHandler()
    try:
        content = await file.read()
        s3_key = f"uploads/{file.filename}"
        uploaded_key = handler.upload_file(content, s3_key)
        return custom_response(
            success=True,
            message="File uploaded successfully",
            data={"s3_key": uploaded_key},
            status=201,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/data/{s3_key:path}")
async def get_s3_file_data(s3_key: str):
    """Downloads a file from S3 and returns its content as JSON."""
    handler = AWSFileHandler()
    try:
        data = handler.download_and_read_file(s3_key)
        return custom_response(
            success=True,
            message="Data fetched successfully",
            data=data,
            status=200,
        )
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)
