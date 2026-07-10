from datetime import datetime
from pydantic import BaseModel, Field


class VolumeCreate(BaseModel):
    name: str = Field(..., max_length=100)
    size_gb: int = Field(..., ge=1, le=1024, description="Size in gigabytes")


class VolumeAttach(BaseModel):
    instance_id: int = Field(..., description="ID of an ACTIVE instance in the same org")


class VolumeResponse(BaseModel):
    id: int
    name: str
    size_gb: int
    status: str
    openstack_volume_id: str | None
    instance_id: int | None
    device: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
