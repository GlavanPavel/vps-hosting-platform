from fastapi import APIRouter, Depends, status

from routers.deps import UowDep, CurrentUserDep, require_permission
from schemas.network import FloatingIPResponse, FloatingIPAssociate
import services

floating_ip_router = APIRouter(prefix="/floating-ips", tags=["floating-ips"])


@floating_ip_router.get("/", response_model=list[FloatingIPResponse])
async def list_floating_ips(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.list_floating_ips(uow=uow, organization_id=user.organization_id)


@floating_ip_router.post(
    "/", status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission("floating_ip:manage"))],
)
async def allocate_floating_ip(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.allocate_floating_ip(uow=uow, organization_id=user.organization_id)


@floating_ip_router.post(
    "/{floating_ip_id}/associate", status_code=200,
    dependencies=[Depends(require_permission("floating_ip:manage"))],
)
async def associate_floating_ip(
    floating_ip_id: int, data: FloatingIPAssociate, uow: UowDep, user_id: CurrentUserDep
):
    user = await uow.users.get_by_id(user_id)
    return await services.associate_floating_ip(
        uow=uow, floating_ip_id=floating_ip_id, instance_id=data.instance_id,
        organization_id=user.organization_id,
    )


@floating_ip_router.post(
    "/{floating_ip_id}/disassociate", status_code=200,
    dependencies=[Depends(require_permission("floating_ip:manage"))],
)
async def disassociate_floating_ip(floating_ip_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.disassociate_floating_ip(
        uow=uow, floating_ip_id=floating_ip_id, organization_id=user.organization_id,
    )


@floating_ip_router.delete(
    "/{floating_ip_id}", status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission("floating_ip:release"))],
)
async def release_floating_ip(floating_ip_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.release_floating_ip(
        uow=uow, floating_ip_id=floating_ip_id, organization_id=user.organization_id,
    )
