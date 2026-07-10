from fastapi import APIRouter

from routers.deps import UowDep, CurrentUserDep
from schemas.quota import QuotaResponse
import services

quota_router = APIRouter(prefix="/quota", tags=["quota"])


@quota_router.get("/", response_model=QuotaResponse)
async def get_quota(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.get_quota(uow=uow, organization_id=user.organization_id)
