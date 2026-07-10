from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from routers.deps import UowDep, CurrentUserDep, require_permission
from schemas.instance import InstanceRequest, InstanceResponse, InstanceDetailResponse
from schemas.instance_event import InstanceEventResponse
from schemas.image import SnapshotCreate, ImageResponse
from tasks.instance_tasks import (
    get_console_url as get_console_url_task,
    get_console_output as get_console_output_task,
)
import services

instance_router = APIRouter(prefix="/instances", tags=["instances"])


@instance_router.get("/", response_model=list[InstanceResponse])
async def list_instances(uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.get_instances(uow=uow, organization_id=user.organization_id)


@instance_router.get("/{instance_id}", response_model=InstanceDetailResponse)
async def get_instance(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.get_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )


@instance_router.get("/{instance_id}/console")
async def get_instance_console(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    detail = await services.get_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )
    if not detail.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")
    if detail.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Console is only available while the instance is ACTIVE")

    try:
        result = await run_in_threadpool(
            lambda: get_console_url_task.delay(detail.openstack_id).get(timeout=20)
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not open console: {exc}")

    return {"console_url": result["url"]}


@instance_router.get("/{instance_id}/logs")
async def get_instance_logs(
    instance_id: int, uow: UowDep, user_id: CurrentUserDep, lines: int = 200
):
    user = await uow.users.get_by_id(user_id)
    detail = await services.get_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )
    if not detail.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")

    lines = max(1, min(lines, 1000))
    try:
        result = await run_in_threadpool(
            lambda: get_console_output_task.delay(detail.openstack_id, lines).get(timeout=20)
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch logs: {exc}")

    return {"output": result.get("output", "")}


@instance_router.get("/{instance_id}/events", response_model=list[InstanceEventResponse])
async def get_instance_events(
    instance_id: int, uow: UowDep, user_id: CurrentUserDep, limit: int = 100
):
    user = await uow.users.get_by_id(user_id)
    instance = await uow.instances.get_by_id_and_org(instance_id, user.organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return await services.list_events(uow=uow, instance_id=instance_id, limit=limit)


@instance_router.post("/", response_model=list[InstanceResponse], status_code=201)
async def create_instance(data: InstanceRequest, uow: UowDep, user_id: CurrentUserDep):
    return await services.create_instance(uow=uow, data=data, user_id=user_id)


@instance_router.post("/{instance_id}/stop", status_code=200)
async def stop_instance(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.stop_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )


@instance_router.post("/{instance_id}/start", status_code=200)
async def start_instance(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.start_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )


@instance_router.post("/{instance_id}/reboot", status_code=200)
async def reboot_instance(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.reboot_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )


@instance_router.post(
    "/{instance_id}/snapshot", response_model=ImageResponse, status_code=201,
    dependencies=[Depends(require_permission("instance:snapshot"))],
)
async def snapshot_instance(
    instance_id: int, data: SnapshotCreate, uow: UowDep, user_id: CurrentUserDep
):
    user = await uow.users.get_by_id(user_id)
    return await services.snapshot_instance(
        uow=uow, instance_id=instance_id, name=data.name,
        organization_id=user.organization_id,
    )


@instance_router.delete(
    "/{instance_id}", status_code=200,
    dependencies=[Depends(require_permission("instance:delete"))],
)
async def delete_instance(instance_id: int, uow: UowDep, user_id: CurrentUserDep):
    user = await uow.users.get_by_id(user_id)
    return await services.delete_instance(
        uow=uow, instance_id=instance_id, organization_id=user.organization_id
    )
