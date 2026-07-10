from fastapi import APIRouter, Depends

from routers.deps import UowDep, require_admin, AdminUserDep
from schemas.admin import AdminOverview, OrgUsageRow, AdminUserRow, AdminUserUpdate
from schemas.quota import QuotaResponse, QuotaUpdate
from tasks.monitoring_tasks import collect_cloud_stats
import services

admin_router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@admin_router.get("/overview", response_model=AdminOverview)
async def overview(uow: UowDep):
    return await services.get_admin_overview(uow=uow)


@admin_router.post("/cloud-stats/refresh", status_code=202)
async def refresh_cloud_stats():
    collect_cloud_stats.delay()
    return {"message": "Cluster stats refresh requested"}


@admin_router.get("/organizations", response_model=list[OrgUsageRow])
async def organizations(uow: UowDep):
    return await services.list_all_organizations(uow=uow)


@admin_router.get("/users", response_model=list[AdminUserRow])
async def users(uow: UowDep):
    return await services.list_all_users(uow=uow)


@admin_router.patch("/users/{user_id}")
async def set_user_active(user_id: int, data: AdminUserUpdate, uow: UowDep, admin: AdminUserDep):
    return await services.admin_set_user_active(
        uow=uow, user_id=user_id, is_active=data.is_active, actor=admin
    )


@admin_router.delete("/users/{user_id}")
async def delete_user(user_id: int, uow: UowDep, admin: AdminUserDep):
    return await services.admin_delete_user(uow=uow, user_id=user_id, actor=admin)


@admin_router.post("/organizations/{organization_id}/active")
async def set_org_active(organization_id: int, data: AdminUserUpdate, uow: UowDep, admin: AdminUserDep):
    return await services.admin_set_org_active(
        uow=uow, organization_id=organization_id, is_active=data.is_active, actor=admin
    )


@admin_router.delete("/organizations/{organization_id}", status_code=202)
async def delete_organization(organization_id: int, uow: UowDep, admin: AdminUserDep):
    return await services.admin_delete_organization(
        uow=uow, organization_id=organization_id, actor=admin
    )


@admin_router.get("/organizations/{organization_id}/quota", response_model=QuotaResponse)
async def get_org_quota(organization_id: int, uow: UowDep):
    return await services.get_quota(uow=uow, organization_id=organization_id)


@admin_router.put("/organizations/{organization_id}/quota", response_model=QuotaResponse)
async def set_org_quota(organization_id: int, data: QuotaUpdate, uow: UowDep):
    return await services.set_quota(uow=uow, organization_id=organization_id, data=data)
