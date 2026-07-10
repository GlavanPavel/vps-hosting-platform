from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class ImageCreate(BaseModel):
    name: str = Field(..., max_length=40)
    source_url: str = Field(
        ..., max_length=500, pattern=r"^https?://",
        description="URL to a disk image Glance can fetch (web-download)",
    )
    disk_format: Literal["qcow2", "raw", "vmdk", "vdi", "iso"] = "qcow2"


class ImageVisibility(BaseModel):
    is_public: bool


class SnapshotCreate(BaseModel):
    name: str = Field(..., max_length=40)


class ImageResponse(BaseModel):
    id: int
    name: str
    source_type: str
    source_url: str | None
    source_instance_id: int | None
    disk_format: str
    openstack_image_id: str | None
    status: str
    size_bytes: int | None
    min_disk_gb: int | None
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}
