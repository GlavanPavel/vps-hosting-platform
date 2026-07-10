from datetime import datetime, timezone
from pydantic import BaseModel, field_serializer


class InstanceEventResponse(BaseModel):
    id: int
    severity: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def _serialize_created_at(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
