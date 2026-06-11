from datetime import datetime
from pydantic import BaseModel, Field


class InstanceRequest(BaseModel):
    name: str = Field(..., max_length=100)
    flavor_name: str = Field(..., max_length=50)
    image_name: str = Field(..., max_length=50)
    keypair_id: int = Field(..., description="ID of a keypair owned by the requesting user")
    subnet_id: int = Field(..., description="ID of a subnet belonging to the user's organization")
    security_group_ids: list[int] = Field(
        ..., min_length=1, description="One or more security group IDs from the user's organization"
    )


class InstanceResponse(BaseModel):
    id: int
    name: str
    status: str
    flavor_name: str
    image_name: str
    private_ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
