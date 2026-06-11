from fastapi import APIRouter
from routers.deps import UowDep, CurrentUserDep
from schemas.instance import InstanceRequest, InstanceResponse
import services

instance_router = APIRouter(prefix="/instances", tags=["instances"])


@instance_router.get("/", response_model=list[InstanceResponse])
async def list_instances(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.get_instances(uow=uow, organization_id=user.organization_id)


@instance_router.post("/", response_model=InstanceResponse, status_code=201)
async def create_instance(data: InstanceRequest, uow: UowDep, user_id: CurrentUserDep):
    return await services.create_instance(uow=uow, data=data, user_id=user_id)


@instance_router.delete("/{instance_id}", status_code=200)
async def delete_instance(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.delete_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )
