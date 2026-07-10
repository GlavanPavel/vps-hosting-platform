from datetime import datetime
from pydantic import BaseModel


class CloudCapacity(BaseModel):
    hypervisor_count: int
    vcpus_total: int
    vcpus_used: int
    ram_gb_total: float
    ram_gb_used: float
    disk_gb_total: int
    disk_gb_used: int
    running_vms: int
    storage_gb_total: int | None
    storage_gb_used: int | None
    updated_at: datetime


class PlatformTotals(BaseModel):
    organizations: int
    users: int
    instances: int
    running_instances: int
    volumes: int
    vcpus_allocated: int
    ram_gb_allocated: float
    storage_gb: int


class AdminOverview(BaseModel):
    # null until the collector task has run at least once
    capacity: CloudCapacity | None
    totals: PlatformTotals


class OrgUsageRow(BaseModel):
    id: int
    name: str
    users: int
    instances: int
    running_instances: int
    vcpus_allocated: int
    ram_gb_allocated: float
    storage_gb: int
    # suspended = has users but none of them are active (admin deactivated the org)
    suspended: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    is_active: bool


class AdminUserRow(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    organization_id: int
    organization_name: str
    instances: int
    vcpus_allocated: int
    ram_gb_allocated: float
    created_at: datetime
