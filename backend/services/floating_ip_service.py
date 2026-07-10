from fastapi import HTTPException

from core.unit_of_work import UnitOfWork
from services.quota_service import enforce_quota
from schemas.network import FloatingIPResponse
from domain.events import (
    FloatingIPAllocationRequested,
    FloatingIPAssociationRequested,
    FloatingIPDisassociationRequested,
    FloatingIPReleaseRequested,
)
from domain.dispatcher import dispatch


async def list_floating_ips(uow: UnitOfWork, organization_id: int) -> list[FloatingIPResponse]:
    fips = await uow.floating_ips.get_by_org(organization_id)
    instances = await uow.instances.get_by_org(organization_id)
    names = {i.id: i.name for i in instances}
    return [
        FloatingIPResponse(
            id=f.id,
            ip_address=f.ip_address,
            openstack_floatingip_id=f.openstack_floatingip_id,
            external_network_name=f.external_network_name,
            status=f.status,
            instance_id=f.instance_id,
            instance_name=names.get(f.instance_id) if f.instance_id else None,
            created_at=f.created_at,
        )
        for f in fips
    ]


async def allocate_floating_ip(uow: UnitOfWork, organization_id: int) -> dict:
    await enforce_quota(uow, organization_id, add_floating_ips=1)
    dispatch(FloatingIPAllocationRequested(organization_id=organization_id))
    return {"message": "Floating IP allocation requested"}


async def associate_floating_ip(
    uow: UnitOfWork, floating_ip_id: int, instance_id: int, organization_id: int
) -> dict:
    fip = await uow.floating_ips.get_by_id_and_org(floating_ip_id, organization_id)
    if not fip:
        raise HTTPException(status_code=404, detail="Floating IP not found")
    if fip.instance_id is not None:
        raise HTTPException(status_code=409, detail="Floating IP is already attached to an instance")

    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")

    # one public IP per instance, mirroring the auto-allocation on create
    existing = await uow.floating_ips.get_by_instance(instance_id)
    if existing:
        raise HTTPException(status_code=409, detail="Instance already has a floating IP")

    fip.status = "associating"
    fip.instance_id = instance_id
    await uow.commit()

    dispatch(FloatingIPAssociationRequested(
        floating_ip_id=fip.id,
        openstack_floatingip_id=fip.openstack_floatingip_id,
        instance_openstack_id=instance.openstack_id,
    ))
    return {"message": "Association requested"}


async def disassociate_floating_ip(
    uow: UnitOfWork, floating_ip_id: int, organization_id: int
) -> dict:
    fip = await uow.floating_ips.get_by_id_and_org(floating_ip_id, organization_id)
    if not fip:
        raise HTTPException(status_code=404, detail="Floating IP not found")
    if fip.instance_id is None:
        raise HTTPException(status_code=409, detail="Floating IP is not attached to any instance")

    fip.status = "disassociating"
    await uow.commit()

    dispatch(FloatingIPDisassociationRequested(
        floating_ip_id=fip.id,
        openstack_floatingip_id=fip.openstack_floatingip_id,
    ))
    return {"message": "Disassociation requested"}


async def release_floating_ip(
    uow: UnitOfWork, floating_ip_id: int, organization_id: int
) -> dict:
    fip = await uow.floating_ips.get_by_id_and_org(floating_ip_id, organization_id)
    if not fip:
        raise HTTPException(status_code=404, detail="Floating IP not found")

    fip.status = "releasing"
    await uow.commit()

    dispatch(FloatingIPReleaseRequested(
        floating_ip_id=fip.id,
        openstack_floatingip_id=fip.openstack_floatingip_id,
    ))
    return {"message": "Release requested"}
