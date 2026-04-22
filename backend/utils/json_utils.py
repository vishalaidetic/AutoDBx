import json
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder that handles:
    - UUIDs
    - Datetimes/Dates
    - Enums
    - Pydantic Models
    """

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


def json_serializer(data):
    """
    Serializes data to a JSON-compatible dictionary using CustomJSONEncoder
    """
    return json.loads(json.dumps(data, cls=CustomJSONEncoder))
