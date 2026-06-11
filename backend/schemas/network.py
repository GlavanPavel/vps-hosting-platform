from datetime import datetime
from pydantic import BaseModel, Field


class SubnetCreate(BaseModel):
    name: str = Field(..., max_length=100)
    cidr: str = Field(..., description="CIDR block, e.g. 10.0.1.0/24")


class SubnetResponse(BaseModel):
    id: int
    name: str
    cidr: str
    openstack_subnet_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NetworkCreate(BaseModel):
    name: str = Field(..., max_length=100)
    # initial subnets can be provided at creation time
    subnets: list[SubnetCreate] = Field(default_factory=list)


class NetworkResponse(BaseModel):
    id: int
    name: str
    openstack_network_id: str | None
    subnets: list[SubnetResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class FloatingIPResponse(BaseModel):
    id: int
    ip_address: str
    openstack_floatingip_id: str
    external_network_name: str
    status: str
    instance_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
