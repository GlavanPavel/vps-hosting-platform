from fastapi import APIRouter, Depends
from routers.deps import UowDep, CurrentUserModelDep, require_permission
from schemas.user import MemberCreate, MemberUpdate, UserResponse
import services

org_router = APIRouter(prefix="/org", tags=["org"])


@org_router.get("/members", response_model=list[UserResponse])
async def list_members(uow: UowDep, user: CurrentUserModelDep):
    return await services.list_members(uow=uow, organization_id=user.organization_id)


@org_router.post(
    "/members", response_model=UserResponse, status_code=201,
    dependencies=[Depends(require_permission("org:manage"))],
)
async def create_member(data: MemberCreate, uow: UowDep, user: CurrentUserModelDep):
    return await services.create_member(uow=uow, data=data, organization_id=user.organization_id)


@org_router.patch(
    "/members/{member_id}", response_model=UserResponse,
    dependencies=[Depends(require_permission("org:manage"))],
)
async def update_member(member_id: int, data: MemberUpdate, uow: UowDep, user: CurrentUserModelDep):
    return await services.update_member(
        uow=uow, member_id=member_id, data=data,
        organization_id=user.organization_id, actor_id=user.id,
    )
