from fastapi import APIRouter
from routers.deps import UowDep, CurrentUserDep
from schemas.security_group import SecurityGroupCreate, SecurityGroupResponse
import services

security_group_router = APIRouter(prefix="/security-groups", tags=["security-groups"])


@security_group_router.get("/", response_model=list[SecurityGroupResponse])
async def list_security_groups(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.list_security_groups(uow=uow, organization_id=user.organization_id)


@security_group_router.post("/", response_model=SecurityGroupResponse, status_code=201)
async def create_security_group(data: SecurityGroupCreate, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.create_security_group(
        uow=uow, data=data, organization_id=user.organization_id
    )


@security_group_router.delete("/{sg_id}", status_code=200)
async def delete_security_group(sg_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.delete_security_group(
        uow=uow, sg_id=sg_id, organization_id=user.organization_id
    )
