from datetime import datetime
from pydantic import BaseModel, Field


class KeypairCreate(BaseModel):
    name: str = Field(..., max_length=100)
    public_key: str = Field(..., description="OpenSSH public key string")


class KeypairResponse(BaseModel):
    id: int
    name: str
    fingerprint: str
    openstack_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
