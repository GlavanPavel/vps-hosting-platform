from core.unit_of_work import UnitOfWork
from core.flavors import flavor_spec
from schemas.usage import UsageResponse, InstanceUsage, VolumeUsage


def _r(x: float) -> float:
    return round(x, 2)


async def get_usage(uow: UnitOfWork, organization_id: int) -> UsageResponse:
    instances = await uow.instances.get_by_org(organization_id)
    volumes = await uow.volumes.get_by_org(organization_id)

    instance_lines = [
        InstanceUsage(
            id=inst.id, name=inst.name, flavor_name=inst.flavor_name,
            status=inst.status, hours=_r(inst.running_seconds / 3600),
        )
        for inst in instances
    ]
    volume_lines = [
        VolumeUsage(id=vol.id, name=vol.name, size_gb=vol.size_gb) for vol in volumes
    ]

    # footprint — sum the flavor-allocated vCPU/RAM of ACTIVE instances (reserved
    # capacity, not measured consumption); volumes always hold their storage
    active = [i for i in instances if i.status == "ACTIVE"]
    vcpus = sum(flavor_spec(i.flavor_name)["vcpu"] for i in active)
    ram_mb = sum(flavor_spec(i.flavor_name)["ram_mb"] for i in active)
    storage_gb = sum(v.size_gb for v in volumes)

    return UsageResponse(
        instances=instance_lines,
        volumes=volume_lines,
        running_instances=len(active),
        vcpus_allocated=vcpus,
        ram_gb_allocated=_r(ram_mb / 1024),
        storage_gb=storage_gb,
    )
