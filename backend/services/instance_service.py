from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from models.instance import Instance
from schemas.instance import InstanceRequest, InstanceResponse
from domain.events import InstanceProvisioningStarted, InstanceDeletionRequested
from domain.dispatcher import dispatch


async def create_instance(uow: UnitOfWork, data: InstanceRequest, user_id: int) -> InstanceResponse:
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

    instance = Instance(
        organization_id=user.organization_id,
        user_id=user_id,
        name=data.name,
        flavor_name=data.flavor_name,
        image_name=data.image_name,
        keypair_id=keypair.id,
        subnet_id=subnet.id,
        status="BUILD",
    )
    instance.security_groups = security_groups

    await uow.instances.add(instance)
    await uow.commit()
    await uow.refresh(instance)

    dispatch(InstanceProvisioningStarted(
        instance_id=instance.id,
        name=instance.name,
        image_name=instance.image_name,
        flavor_name=instance.flavor_name,
        keypair_openstack_name=keypair.openstack_name,
        subnet_openstack_id=subnet.openstack_subnet_id,
        security_group_openstack_ids=[sg.openstack_id for sg in security_groups],
    ))

    return InstanceResponse.model_validate(instance)


async def delete_instance(uow: UnitOfWork, instance_id: int, organization_id: int) -> dict:
    instance = await uow.instances.get_by_id_and_org(instance_id, organization_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    if instance.openstack_id:
        instance.status = "DELETING"
        await uow.commit()

        dispatch(InstanceDeletionRequested(
            instance_id=instance.id,
            openstack_id=instance.openstack_id,
        ))
        return {"message": "Deletion request registered"}

    # instance never made it to OpenStack — safe to hard-delete
    await uow.instances.delete(instance)
    await uow.commit()
    return {"message": "Incomplete instance removed from database"}


async def get_instances(uow: UnitOfWork, organization_id: int) -> list[InstanceResponse]:
    instances = await uow.instances.get_by_org(organization_id)
    return [InstanceResponse.model_validate(i) for i in instances]
