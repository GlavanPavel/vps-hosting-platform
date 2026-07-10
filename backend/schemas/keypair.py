from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class KeypairCreate(BaseModel):
    name: str = Field(..., max_length=100)
    public_key: str = Field(..., description="OpenSSH public key string")


class KeypairGenerate(BaseModel):
    name: str = Field(..., max_length=100)
    key_type: Literal["ed25519", "rsa"] = Field(
        default="ed25519", description="Algorithm for the generated keypair"
    )


class KeypairResponse(BaseModel):
    id: int
    name: str
    fingerprint: str
    openstack_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KeypairGenerateResponse(KeypairResponse):
    private_key: str
