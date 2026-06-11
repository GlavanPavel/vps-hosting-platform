from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    organization_name: str = Field(..., max_length=100)


class UserResponse(BaseModel):
    id: int
    email: str
    organization_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationResponse(BaseModel):
    id: int
    name: str
    openstack_project_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
