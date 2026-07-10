from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from core.flavors import flavor_spec
from services.quota_service import enforce_quota
from services.instance_event_service import record_event
from models.instance import Instance
from models.image import Image
from schemas.instance import (
    InstanceRequest,
    InstanceResponse,
    InstanceDetailResponse,
    KeypairBrief,
    SubnetBrief,
    SecurityGroupBrief,
    FloatingIPBrief,
    VolumeBrief,
)
from schemas.image import ImageResponse
from domain.events import (
    InstanceProvisioningStarted,
    InstanceDeletionRequested,
    InstanceStopRequested,
    InstanceStartRequested,
    InstanceRebootRequested,
    InstanceSnapshotRequested,
)
from domain.dispatcher import dispatch


async def create_instance(uow: UnitOfWork, data: InstanceRequest, user_id: int) -> list[InstanceResponse]:
    user = await uow.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    keypair = await uow.keypairs.get_by_id_and_user(data.keypair_id, user_id)
    if not keypair:
        raise HTTPException(status_code=404, detail="Keypair not found or does not belong to this user")
    if not keypair.openstack_name:
        raise HTTPException(status_code=422, detail="Keypair has not been uploaded to OpenStack yet")

    subnet = await uow.subnets.get_by_id_and_org(data.subnet_id, user.organization_id)
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found or does not belong to this organization")
    if not subnet.openstack_subnet_id:
        raise HTTPException(status_code=422, detail="Subnet has not been provisioned in OpenStack yet")

    security_groups = await uow.security_groups.get_by_ids_and_org(
        data.security_group_ids, user.organization_id
    )
    if len(security_groups) != len(data.security_group_ids):
        raise HTTPException(status_code=404, detail="One or more security groups not found or unauthorized")

    missing_os_id = [sg.name for sg in security_groups if not sg.openstack_id]
    if missing_os_id:
        raise HTTPException(
            status_code=422,
            detail=f"Security groups not yet provisioned in OpenStack: {missing_os_id}",
        )

    count = data.count or 1

    # an existing volume attaches to exactly one server, so it can't be shared
    # across a multi-instance launch
    if count > 1 and data.attach_volume_ids:
        raise HTTPException(
            status_code=422,
            detail="Attaching existing volumes is only supported when launching a single instance",
        )

    # validate any existing volumes the user wants attached (must be available)
    if data.attach_volume_ids:
        volumes = await uow.volumes.get_by_ids_and_org(data.attach_volume_ids, user.organization_id)
        if len(volumes) != len(set(data.attach_volume_ids)):
            raise HTTPException(status_code=404, detail="One or more volumes not found or unauthorized")
        unavailable = [v.name for v in volumes if v.status != "available" or v.instance_id is not None]
        if unavailable:
            raise HTTPException(
                status_code=409, detail=f"Volumes not available to attach: {unavailable}"
            )

    # enforce the org's quota before creating anything
    spec = flavor_spec(data.flavor_name)
    await enforce_quota(
        uow, user.organization_id,
        add_instances=count,
        add_vcpus=spec["vcpu"] * count,
        add_ram_mb=spec["ram_mb"] * count,
        add_floating_ips=count if data.assign_floating_ip else 0,
    )

    # build all the DB rows first, commit once, then fan out provisioning events
    instances: list[Instance] = []
    for i in range(count):
        # suffix names only when launching a batch, so a single launch keeps its exact name
        inst_name = data.name if count == 1 else f"{data.name}-{i + 1}"
        instance = Instance(
            organization_id=user.organization_id,
            user_id=user_id,
            name=inst_name,
            flavor_name=data.flavor_name,
            image_name=data.image_name,
            keypair_id=keypair.id,
            subnet_id=subnet.id,
            status="BUILD",
        )
        instance.security_groups = security_groups
        await uow.instances.add(instance)
        instances.append(instance)

    await uow.commit()

    for instance in instances:
        await uow.refresh(instance)
        dispatch(InstanceProvisioningStarted(
            instance_id=instance.id,
            name=instance.name,
            image_name=instance.image_name,
            flavor_name=instance.flavor_name,
            keypair_openstack_name=keypair.openstack_name,
            subnet_openstack_id=subnet.openstack_subnet_id,
            security_group_openstack_ids=[sg.openstack_id for sg in security_groups],
            root_disk_gb=data.root_disk_gb or 0,
            data_volume_size_gb=data.data_volume_size_gb or 0,
            attach_volume_ids=data.attach_volume_ids,
            user_data=data.user_data or "",
            assign_floating_ip=data.assign_floating_ip,
        ))
        await record_event(
            uow, instance.id, "info",
            f"Instance created ({data.flavor_name}) — provisioning started",
        )

    return [InstanceResponse.model_validate(i) for i in instances]


async def delete_instance(uow: UnitOfWork, instance_id: int, organization_id: int) -> dict:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if instance.openstack_id:
        instance.status = "DELETING"
        await uow.commit()
        # the instance's event rows cascade-delete with it once Celery removes the row
        await record_event(uow, instance.id, "info", "Deletion requested")

        dispatch(InstanceDeletionRequested(
            instance_id=instance.id,
            openstack_id=instance.openstack_id,
        ))
        return {"message": "Deletion request registered"}

    # instance never made it to OpenStack — safe to hard-delete
    await uow.instances.delete(instance)
    await uow.commit()
    return {"message": "Incomplete instance removed from database"}


async def stop_instance(uow: UnitOfWork, instance_id: int, organization_id: int) -> dict:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")
    if instance.status != "ACTIVE":
        raise HTTPException(
            status_code=409, detail=f"Only an ACTIVE instance can be stopped (current: {instance.status})"
        )

    instance.status = "STOPPING"
    await uow.commit()
    dispatch(InstanceStopRequested(instance_id=instance.id, openstack_id=instance.openstack_id))
    await record_event(uow, instance.id, "info", "Stop requested")
    return {"message": "Stop requested"}


async def start_instance(uow: UnitOfWork, instance_id: int, organization_id: int) -> dict:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")
    if instance.status != "SHUTOFF":
        raise HTTPException(
            status_code=409, detail=f"Only a stopped instance can be started (current: {instance.status})"
        )

    instance.status = "STARTING"
    await uow.commit()
    dispatch(InstanceStartRequested(instance_id=instance.id, openstack_id=instance.openstack_id))
    await record_event(uow, instance.id, "info", "Start requested")
    return {"message": "Start requested"}


async def reboot_instance(uow: UnitOfWork, instance_id: int, organization_id: int) -> dict:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")
    if instance.status != "ACTIVE":
        raise HTTPException(
            status_code=409, detail=f"Only an ACTIVE instance can be restarted (current: {instance.status})"
        )

    instance.status = "REBOOT"
    await uow.commit()
    dispatch(InstanceRebootRequested(instance_id=instance.id, openstack_id=instance.openstack_id))
    await record_event(uow, instance.id, "info", "Restart requested")
    return {"message": "Restart requested"}


async def snapshot_instance(
    uow: UnitOfWork, instance_id: int, name: str, organization_id: int
) -> ImageResponse:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not instance.openstack_id:
        raise HTTPException(status_code=409, detail="Instance is not provisioned in OpenStack yet")
    if instance.status not in ("ACTIVE", "SHUTOFF"):
        raise HTTPException(
            status_code=409,
            detail=f"Can only snapshot an ACTIVE or SHUTOFF instance (current: {instance.status})",
        )

    # a snapshot is just a Glance image with a different origin — reuses the images pipeline
    image = Image(
        organization_id=organization_id,
        name=name,
        source_type="snapshot",
        source_instance_id=instance.id,
        status="snapshotting",
    )
    await uow.images.add(image)
    await uow.commit()
    await uow.refresh(image)

    dispatch(InstanceSnapshotRequested(
        image_id=image.id,
        instance_openstack_id=instance.openstack_id,
        name=image.name,
    ))
    await record_event(uow, instance.id, "info", f"Snapshot requested: {name}")
    return ImageResponse.model_validate(image)


async def get_instances(uow: UnitOfWork, organization_id: int) -> list[InstanceResponse]:
    instances = await uow.instances.get_by_org(organization_id)
    return [InstanceResponse.model_validate(i) for i in instances]


async def get_instance(
    uow: UnitOfWork, instance_id: int, organization_id: int
) -> InstanceDetailResponse:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    spec = flavor_spec(instance.flavor_name)
    return InstanceDetailResponse(
        id=instance.id,
        name=instance.name,
        status=instance.status,
        flavor_name=instance.flavor_name,
        image_name=instance.image_name,
        vcpus=spec["vcpu"],
        ram_mb=spec["ram_mb"],
        disk_gb=spec["disk_gb"],
        private_ip_address=instance.private_ip_address,
        openstack_id=instance.openstack_id,
        created_at=instance.created_at,
        keypair=KeypairBrief(id=instance.keypair.id, name=instance.keypair.name)
        if instance.keypair else None,
        subnet=SubnetBrief(
            id=instance.subnet.id,
            name=instance.subnet.name,
            cidr=instance.subnet.cidr,
            network_name=instance.subnet.network.name,
        ) if instance.subnet else None,
        security_groups=[
            SecurityGroupBrief(id=sg.id, name=sg.name) for sg in instance.security_groups
        ],
        floating_ip=FloatingIPBrief(
            ip_address=instance.floating_ip.ip_address,
            status=instance.floating_ip.status,
        ) if instance.floating_ip else None,
        volumes=[
            VolumeBrief(
                id=v.id, name=v.name, size_gb=v.size_gb, status=v.status, device=v.device
            ) for v in instance.volumes
        ],
    )
