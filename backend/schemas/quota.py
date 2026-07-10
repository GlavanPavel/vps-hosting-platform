from pydantic import BaseModel, Field


class QuotaLimits(BaseModel):
    max_instances: int
    max_vcpus: int
    max_ram_gb: int
    max_volumes: int
    max_storage_gb: int
    max_floating_ips: int


class QuotaUsage(BaseModel):
    instances: int
    vcpus: int
    ram_gb: float
    volumes: int
    storage_gb: int
    floating_ips: int


class QuotaResponse(BaseModel):
    limits: QuotaLimits
    usage: QuotaUsage
    # True when the org has no override row and is using the system defaults
    is_default: bool


class QuotaUpdate(BaseModel):
    max_instances: int = Field(..., ge=0)
    max_vcpus: int = Field(..., ge=0)
    max_ram_gb: int = Field(..., ge=0)
    max_volumes: int = Field(..., ge=0)
    max_storage_gb: int = Field(..., ge=0)
    max_floating_ips: int = Field(..., ge=0)
