from fastapi import APIRouter
from routers.deps import UowDep, CurrentUserDep
from schemas.usage import UsageResponse
import services

usage_router = APIRouter(prefix="/usage", tags=["usage"])


@usage_router.get("/", response_model=UsageResponse)
async def get_usage(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.get_usage(uow=uow, organization_id=user.organization_id)
