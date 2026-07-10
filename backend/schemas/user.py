from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, computed_field
from core.permissions import permissions_for


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    organization_name: str = Field(..., max_length=100)


class MemberCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Literal["owner", "member"] = "member"


class MemberUpdate(BaseModel):
    role: Literal["owner", "member"] | None = None
    is_active: bool | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    organization_id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def permissions(self) -> list[str]:
        return sorted(permissions_for(self.role))


class OrganizationResponse(BaseModel):
    id: int
    name: str
    openstack_project_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
