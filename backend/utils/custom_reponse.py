from typing import Any, Optional

from fastapi.responses import JSONResponse
from utils.json_utils import json_serializer


def custom_response(
    success: bool = False,
    message: str = "Something went wrong",
    data: Optional[Any] = None,
    status: int = 400,
) -> JSONResponse:
    """
    Standardized API response handler using custom json_serializer

    Args:
        success: Boolean indicating if request was successful
        message: Human-readable message
        data: Response data (can be dict, list, or any JSON-serializable object)
        status: HTTP status code

    Returns:
        JSONResponse with standardized format
    """
    response = {
        "success": success,
        "message": message,
        "data": json_serializer(data),
    }
    return JSONResponse(content=response, status_code=status)
