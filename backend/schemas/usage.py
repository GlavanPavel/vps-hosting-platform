from pydantic import BaseModel


class InstanceUsage(BaseModel):
    id: int
    name: str
    flavor_name: str
    status: str
    hours: float


class VolumeUsage(BaseModel):
    id: int
    name: str
    size_gb: int


class UsageResponse(BaseModel):
    instances: list[InstanceUsage]
    volumes: list[VolumeUsage]
    # footprint of currently-running resources — these are amounts *allocated* by each
    # flavor, not measured in-guest consumption (the hypervisor doesn't expose live RAM)
    running_instances: int
    vcpus_allocated: int
    ram_gb_allocated: float
    storage_gb: int
