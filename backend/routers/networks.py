from fastapi import APIRouter, Depends
from routers.deps import UowDep, CurrentUserDep, require_permission
from schemas.network import NetworkCreate, NetworkResponse, FloatingIPResponse
import services

network_router = APIRouter(prefix="/networks", tags=["networks"])


@network_router.get("/", response_model=list[NetworkResponse])
async def list_networks(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.list_networks(uow=uow, organization_id=user.organization_id)


@network_router.post("/", response_model=NetworkResponse, status_code=201)
async def create_network(data: NetworkCreate, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.create_network(
        uow=uow, data=data, organization_id=user.organization_id
    )


@network_router.delete(
    "/{network_id}", status_code=200,
    dependencies=[Depends(require_permission("network:delete"))],
)
async def delete_network(network_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.delete_network(
        uow=uow, network_id=network_id, organization_id=user.organization_id
    )


@network_router.get("/floating-ips", response_model=list[FloatingIPResponse])
async def list_floating_ips(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    fips = await uow.floating_ips.get_by_org(user.organization_id)
    from schemas.network import FloatingIPResponse
    return [FloatingIPResponse.model_validate(f) for f in fips]
