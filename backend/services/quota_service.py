from fastapi import HTTPException

from core.unit_of_work import UnitOfWork
from core.quotas import DEFAULT_QUOTA, QUOTA_FIELDS
from core.flavors import flavor_spec
from models.quota import Quota
from schemas.quota import QuotaLimits, QuotaUsage, QuotaResponse, QuotaUpdate


async def _effective_limits(uow: UnitOfWork, organization_id: int) -> tuple[dict, bool]:
    row = await uow.quotas.get_by_org(organization_id)
    if row:
        return ({f: getattr(row, f) for f in QUOTA_FIELDS}, False)
    return (dict(DEFAULT_QUOTA), True)


async def _usage(uow: UnitOfWork, organization_id: int) -> dict:
    instances = await uow.instances.get_by_org(organization_id)
    volumes = await uow.volumes.get_by_org(organization_id)
    fips = await uow.floating_ips.get_by_org(organization_id)
    ram_mb = sum(flavor_spec(i.flavor_name)["ram_mb"] for i in instances)
    return {
        "instances": len(instances),
        "vcpus": sum(flavor_spec(i.flavor_name)["vcpu"] for i in instances),
        "ram_mb": ram_mb,
        "volumes": len(volumes),
        "storage_gb": sum(v.size_gb for v in volumes),
        "floating_ips": len(fips),
    }


async def get_quota(uow: UnitOfWork, organization_id: int) -> QuotaResponse:
    limits, is_default = await _effective_limits(uow, organization_id)
    usage = await _usage(uow, organization_id)
    return QuotaResponse(
        limits=QuotaLimits(**limits),
        usage=QuotaUsage(
            instances=usage["instances"],
            vcpus=usage["vcpus"],
            ram_gb=round(usage["ram_mb"] / 1024, 2),
            volumes=usage["volumes"],
            storage_gb=usage["storage_gb"],
            floating_ips=usage["floating_ips"],
        ),
        is_default=is_default,
    )


async def set_quota(uow: UnitOfWork, organization_id: int, data: QuotaUpdate) -> QuotaResponse:
    org = await uow.organizations.get_by_id(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    row = await uow.quotas.get_by_org(organization_id)
    if not row:
        row = Quota(organization_id=organization_id)
        await uow.quotas.add(row)
    for field in QUOTA_FIELDS:
        setattr(row, field, getattr(data, field))
    await uow.commit()
    return await get_quota(uow, organization_id)


async def enforce_quota(
    uow: UnitOfWork,
    organization_id: int,
    *,
    add_instances: int = 0,
    add_vcpus: int = 0,
    add_ram_mb: int = 0,
    add_volumes: int = 0,
    add_storage_gb: int = 0,
    add_floating_ips: int = 0,
) -> None:
    limits, _ = await _effective_limits(uow, organization_id)
    usage = await _usage(uow, organization_id)

    errors: list[str] = []
    if add_instances and usage["instances"] + add_instances > limits["max_instances"]:
        errors.append(f"instances ({usage['instances']}+{add_instances} > {limits['max_instances']})")
    if add_vcpus and usage["vcpus"] + add_vcpus > limits["max_vcpus"]:
        errors.append(f"vCPUs ({usage['vcpus']}+{add_vcpus} > {limits['max_vcpus']})")
    if add_ram_mb and usage["ram_mb"] + add_ram_mb > limits["max_ram_gb"] * 1024:
        used_gb = round(usage["ram_mb"] / 1024, 1)
        add_gb = round(add_ram_mb / 1024, 1)
        errors.append(f"RAM ({used_gb}+{add_gb} > {limits['max_ram_gb']} GB)")
    if add_volumes and usage["volumes"] + add_volumes > limits["max_volumes"]:
        errors.append(f"volumes ({usage['volumes']}+{add_volumes} > {limits['max_volumes']})")
    if add_storage_gb and usage["storage_gb"] + add_storage_gb > limits["max_storage_gb"]:
        errors.append(
            f"storage ({usage['storage_gb']}+{add_storage_gb} > {limits['max_storage_gb']} GB)"
        )
    if add_floating_ips and usage["floating_ips"] + add_floating_ips > limits["max_floating_ips"]:
        errors.append(
            f"floating IPs ({usage['floating_ips']}+{add_floating_ips} > {limits['max_floating_ips']})"
        )

    if errors:
        raise HTTPException(status_code=409, detail="Quota exceeded — " + "; ".join(errors))
