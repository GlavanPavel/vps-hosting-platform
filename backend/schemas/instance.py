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
    # optional custom root disk (GB) — boots from a volume instead of the flavor disk
    root_disk_gb: int | None = Field(default=None, ge=1, le=1024)
    # optional extra data disk (GB) to create + attach after the VM is ACTIVE
    data_volume_size_gb: int | None = Field(default=None, ge=1, le=1024)
    # optional existing volumes (DB ids) to attach after the VM is ACTIVE
    attach_volume_ids: list[int] = Field(default_factory=list)
    # optional cloud-init startup script run on first boot (base64-encoded by Celery
    # before reaching nova; raw stays under nova's 64 KB user_data ceiling)
    user_data: str | None = Field(default=None, max_length=49152)
    # how many identical instances to launch in one request (EC2-style)
    count: int = Field(default=1, ge=1, le=10)
    # allocate + associate a public (floating) IP once the server is ACTIVE
    assign_floating_ip: bool = Field(default=True)


class InstanceResponse(BaseModel):
    id: int
    name: str
    status: str
    flavor_name: str
    image_name: str
    private_ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}



class KeypairBrief(BaseModel):
    id: int
    name: str


class SubnetBrief(BaseModel):
    id: int
    name: str
    cidr: str
    network_name: str


class SecurityGroupBrief(BaseModel):
    id: int
    name: str


class FloatingIPBrief(BaseModel):
    ip_address: str
    status: str


class VolumeBrief(BaseModel):
    id: int
    name: str
    size_gb: int
    status: str
    device: str | None


class InstanceDetailResponse(BaseModel):
    id: int
    name: str
    status: str
    flavor_name: str
    image_name: str
    # flavor-derived specs (from core/flavors.py) so the detail page can show them
    vcpus: int
    ram_mb: int
    disk_gb: int
    private_ip_address: str | None
    # OpenStack server UUID — needed by the frontend to query telemetry
    openstack_id: str | None
    created_at: datetime
    keypair: KeypairBrief | None
    subnet: SubnetBrief | None
    security_groups: list[SecurityGroupBrief]
    floating_ip: FloatingIPBrief | None
    volumes: list[VolumeBrief]
