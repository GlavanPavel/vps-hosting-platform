from collections import defaultdict

from fastapi import HTTPException

from core.unit_of_work import UnitOfWork
from core.flavors import flavor_spec
from models.cloud_stats import CloudStats
from models.user import User
from domain.events import (
    InstanceStopRequested,
    KeypairDeletionRequested,
    OrganizationDeletionRequested,
)
from domain.dispatcher import dispatch
from schemas.admin import (
    AdminOverview,
    CloudCapacity,
    PlatformTotals,
    OrgUsageRow,
    AdminUserRow,
)


def _r(x: float) -> float:
    return round(x, 2)


def _vcpus(instances) -> int:
    return sum(flavor_spec(i.flavor_name)["vcpu"] for i in instances)


def _ram_gb(instances) -> float:
    return _r(sum(flavor_spec(i.flavor_name)["ram_mb"] for i in instances) / 1024)


def _capacity(stats: CloudStats | None) -> CloudCapacity | None:
    if not stats:
        return None
    return CloudCapacity(
        hypervisor_count=stats.hypervisor_count,
        vcpus_total=stats.vcpus_total,
        vcpus_used=stats.vcpus_used,
        ram_gb_total=_r((stats.ram_mb_total or 0) / 1024),
        ram_gb_used=_r((stats.ram_mb_used or 0) / 1024),
        disk_gb_total=stats.disk_gb_total,
        disk_gb_used=stats.disk_gb_used,
        running_vms=stats.running_vms,
        storage_gb_total=stats.storage_gb_total,
        storage_gb_used=stats.storage_gb_used,
        updated_at=stats.updated_at,
    )


async def get_overview(uow: UnitOfWork) -> AdminOverview:
    instances = await uow.instances.get_all()
    volumes = await uow.volumes.get_all()
    users = await uow.users.get_all()
    orgs = await uow.organizations.get_all()
    stats = await uow.cloud_stats.get_latest()

    active = [i for i in instances if i.status == "ACTIVE"]
    totals = PlatformTotals(
        organizations=len(orgs),
        users=len(users),
        instances=len(instances),
        running_instances=len(active),
        volumes=len(volumes),
        vcpus_allocated=_vcpus(active),
        ram_gb_allocated=_ram_gb(active),
        storage_gb=sum(v.size_gb for v in volumes),
    )
    return AdminOverview(capacity=_capacity(stats), totals=totals)


async def list_organizations(uow: UnitOfWork) -> list[OrgUsageRow]:
    orgs = await uow.organizations.get_all()
    instances = await uow.instances.get_all()
    volumes = await uow.volumes.get_all()
    users = await uow.users.get_all()

    inst_by_org: dict[int, list] = defaultdict(list)
    for i in instances:
        inst_by_org[i.organization_id].append(i)
    vol_by_org: dict[int, list] = defaultdict(list)
    for v in volumes:
        vol_by_org[v.organization_id].append(v)
    users_by_org: dict[int, int] = defaultdict(int)
    active_users_by_org: dict[int, int] = defaultdict(int)
    for u in users:
        users_by_org[u.organization_id] += 1
        if u.is_active:
            active_users_by_org[u.organization_id] += 1

    rows = []
    for o in orgs:
        insts = inst_by_org.get(o.id, [])
        active = [i for i in insts if i.status == "ACTIVE"]
        total_users = users_by_org.get(o.id, 0)
        rows.append(OrgUsageRow(
            id=o.id,
            name=o.name,
            users=total_users,
            instances=len(insts),
            running_instances=len(active),
            vcpus_allocated=_vcpus(active),
            ram_gb_allocated=_ram_gb(active),
            storage_gb=sum(v.size_gb for v in vol_by_org.get(o.id, [])),
            suspended=total_users > 0 and active_users_by_org.get(o.id, 0) == 0,
            created_at=o.created_at,
        ))
    return rows


async def list_users(uow: UnitOfWork) -> list[AdminUserRow]:
    users = await uow.users.get_all()
    orgs = {o.id: o.name for o in await uow.organizations.get_all()}
    instances = await uow.instances.get_all()

    inst_by_user: dict[int, list] = defaultdict(list)
    for i in instances:
        inst_by_user[i.user_id].append(i)

    rows = []
    for u in users:
        insts = inst_by_user.get(u.id, [])
        active = [i for i in insts if i.status == "ACTIVE"]
        rows.append(AdminUserRow(
            id=u.id,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            organization_id=u.organization_id,
            organization_name=orgs.get(u.organization_id, "—"),
            instances=len(insts),
            vcpus_allocated=_vcpus(active),
            ram_gb_allocated=_ram_gb(active),
            created_at=u.created_at,
        ))
    return rows


async def _stop_instances(uow: UnitOfWork, instances) -> int:
    to_stop = [(i.id, i.openstack_id) for i in instances if i.status == "ACTIVE" and i.openstack_id]
    for i in instances:
        if i.status == "ACTIVE" and i.openstack_id:
            i.status = "STOPPING"
    await uow.commit()
    for instance_id, openstack_id in to_stop:
        dispatch(InstanceStopRequested(instance_id=instance_id, openstack_id=openstack_id))
    return len(to_stop)


async def set_user_active(uow: UnitOfWork, user_id: int, is_active: bool, actor: User) -> dict:
    user = await uow.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == actor.id and not is_active:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account")

    user.is_active = is_active
    stopped = 0
    if not is_active:
        # stop the instances this user created so they stop consuming/metering
        org_instances = await uow.instances.get_by_org(user.organization_id)
        stopped = await _stop_instances(uow, [i for i in org_instances if i.user_id == user_id])
    else:
        await uow.commit()
    return {
        "message": f"User {'activated' if is_active else 'deactivated'}",
        "instances_stopped": stopped,
    }


async def delete_user(uow: UnitOfWork, user_id: int, actor: User) -> dict:
    user = await uow.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == actor.id:
        raise HTTPException(status_code=409, detail="You cannot delete your own account")

    org_id = user.organization_id
    others = [u for u in await uow.users.get_by_org(org_id) if u.id != user_id]
    # reassign this user's instances to keep them under the org (prefer an owner)
    target = next((u for u in others if u.role == "owner"), None) or (others[0] if others else None)
    org_instances = await uow.instances.get_by_org(org_id)
    user_instances = [i for i in org_instances if i.user_id == user_id]
    if user_instances and not target:
        raise HTTPException(
            status_code=409,
            detail="User is the only member and owns instances — delete the organization instead.",
        )
    for inst in user_instances:
        inst.user_id = target.id

    # their keypairs are personal — remove from OpenStack + DB
    keypairs = await uow.keypairs.get_by_user(user_id)
    openstack_names = [kp.openstack_name for kp in keypairs if kp.openstack_name]
    for kp in keypairs:
        await uow.keypairs.delete(kp)

    await uow.users.delete(user)
    await uow.commit()
    for name in openstack_names:
        dispatch(KeypairDeletionRequested(openstack_name=name))
    return {"message": "User deleted", "instances_reassigned": len(user_instances)}


async def set_org_active(uow: UnitOfWork, organization_id: int, is_active: bool, actor: User) -> dict:
    org = await uow.organizations.get_by_id(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if actor.organization_id == organization_id and not is_active:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own organization")

    for u in await uow.users.get_by_org(organization_id):
        u.is_active = is_active

    stopped = 0
    if not is_active:
        stopped = await _stop_instances(uow, await uow.instances.get_by_org(organization_id))
    else:
        await uow.commit()
    return {
        "message": f"Organization {'activated' if is_active else 'suspended'}",
        "instances_stopped": stopped,
    }


async def delete_organization(uow: UnitOfWork, organization_id: int, actor: User) -> dict:
    org = await uow.organizations.get_by_id(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if actor.organization_id == organization_id:
        raise HTTPException(status_code=409, detail="You cannot delete your own organization")

    # lock the org out immediately, then let Celery tear down OpenStack + the DB rows
    for u in await uow.users.get_by_org(organization_id):
        u.is_active = False
    await uow.commit()
    dispatch(OrganizationDeletionRequested(organization_id=organization_id))
    return {"message": "Organization teardown started"}
