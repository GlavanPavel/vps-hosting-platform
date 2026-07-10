from fastapi import APIRouter, Depends
from routers.deps import UowDep, CurrentUserDep, require_permission
from schemas.volume import VolumeCreate, VolumeResponse, VolumeAttach
import services

volume_router = APIRouter(prefix="/volumes", tags=["volumes"])


@volume_router.get("/", response_model=list[VolumeResponse])
async def list_volumes(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.list_volumes(uow=uow, organization_id=user.organization_id)


@volume_router.post("/", response_model=VolumeResponse, status_code=201)
async def create_volume(data: VolumeCreate, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.create_volume(uow=uow, data=data, organization_id=user.organization_id)


@volume_router.post("/{volume_id}/attach", status_code=200)
async def attach_volume(volume_id: int, data: VolumeAttach, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.attach_volume(
        uow=uow, volume_id=volume_id, instance_id=data.instance_id,
        organization_id=user.organization_id,
    )


@volume_router.post("/{volume_id}/detach", status_code=200)
async def detach_volume(volume_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.detach_volume(
        uow=uow, volume_id=volume_id, organization_id=user.organization_id
    )


@volume_router.delete(
    "/{volume_id}", status_code=200,
    dependencies=[Depends(require_permission("volume:delete"))],
)
async def delete_volume(volume_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.delete_volume(
        uow=uow, volume_id=volume_id, organization_id=user.organization_id
    )
