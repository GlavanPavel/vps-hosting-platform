from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from services.quota_service import enforce_quota
from models.volume import Volume
from schemas.volume import VolumeCreate, VolumeResponse
from domain.events import (
    VolumeCreationRequested,
    VolumeDeletionRequested,
    VolumeAttachRequested,
    VolumeDetachRequested,
)
from domain.dispatcher import dispatch


async def create_volume(
    uow: UnitOfWork, data: VolumeCreate, organization_id: int
) -> VolumeResponse:
    await enforce_quota(uow, organization_id, add_volumes=1, add_storage_gb=data.size_gb)
    volume = Volume(
        organization_id=organization_id,
        name=data.name,
        size_gb=data.size_gb,
        status="creating",
    )
    await uow.volumes.add(volume)
    await uow.commit()
    await uow.refresh(volume)

    dispatch(VolumeCreationRequested(
        volume_id=volume.id,
        name=volume.name,
        size_gb=volume.size_gb,
    ))
    return VolumeResponse.model_validate(volume)


async def list_volumes(uow: UnitOfWork, organization_id: int) -> list[VolumeResponse]:
    volumes = await uow.volumes.get_by_org(organization_id)
    return [VolumeResponse.model_validate(v) for v in volumes]


async def delete_volume(uow: UnitOfWork, volume_id: int, organization_id: int) -> dict:
    volume = await uow.volumes.get_by_id_and_org(volume_id, organization_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    if volume.instance_id is not None:
        raise HTTPException(status_code=409, detail="Detach the volume before deleting it")

    openstack_volume_id = volume.openstack_volume_id
    if openstack_volume_id:
        volume.status = "deleting"
        await uow.commit()
        dispatch(VolumeDeletionRequested(
            volume_id=volume.id, openstack_volume_id=openstack_volume_id
        ))
        return {"message": "Volume deletion requested"}

    # never provisioned in Cinder — safe to hard-delete
    await uow.volumes.delete(volume)
    await uow.commit()
    return {"message": "Incomplete volume removed"}


async def attach_volume(
    uow: UnitOfWork, volume_id: int, instance_id: int, organization_id: int
) -> dict:
    volume = await uow.volumes.get_by_id_and_org(volume_id, organization_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    if not volume.openstack_volume_id:
        raise HTTPException(status_code=409, detail="Volume is not provisioned yet")
    if volume.instance_id is not None:
        raise HTTPException(status_code=409, detail="Volume is already attached")
    if volume.status != "available":
        raise HTTPException(
            status_code=409, detail=f"Volume is not available (status: {volume.status})"
        )

    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned yet")
    if instance.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Instance must be ACTIVE to attach a volume")

    # optimistically reserve the volume for this instance
    volume.status = "attaching"
    volume.instance_id = instance.id
    await uow.commit()

    dispatch(VolumeAttachRequested(
        volume_id=volume.id,
        openstack_volume_id=volume.openstack_volume_id,
        instance_openstack_id=instance.openstack_id,
    ))
    return {"message": "Attach requested"}


async def detach_volume(uow: UnitOfWork, volume_id: int, organization_id: int) -> dict:
    volume = await uow.volumes.get_by_id_and_org(volume_id, organization_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    if volume.instance_id is None:
        raise HTTPException(status_code=409, detail="Volume is not attached")

    instance = await uow.instances.get_by_id(volume.instance_id)
    instance_openstack_id = instance.openstack_id if instance else ""

    volume.status = "detaching"
    await uow.commit()

    dispatch(VolumeDetachRequested(
        volume_id=volume.id,
        openstack_volume_id=volume.openstack_volume_id or "",
        instance_openstack_id=instance_openstack_id or "",
    ))
    return {"message": "Detach requested"}
