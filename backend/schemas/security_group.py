from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class SecurityGroupRuleCreate(BaseModel):
    direction: Literal["ingress", "egress"]
    protocol: Literal["tcp", "udp", "icmp"] | None = None
    port_range_min: int | None = Field(None, ge=1, le=65535)
    port_range_max: int | None = Field(None, ge=1, le=65535)
    remote_ip_prefix: str | None = Field(None, description="CIDR notation, e.g. 0.0.0.0/0")


class SecurityGroupRuleResponse(BaseModel):
    id: int
    direction: str
    protocol: str | None
    port_range_min: int | None
    port_range_max: int | None
    remote_ip_prefix: str | None

    model_config = {"from_attributes": True}


class SecurityGroupCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    rules: list[SecurityGroupRuleCreate] = Field(default_factory=list)


class SecurityGroupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    openstack_id: str | None
    rules: list[SecurityGroupRuleResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
