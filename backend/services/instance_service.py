import openstack
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Instance
from schemas import InstanceRequest
from core.config import config

def _provision_vm_in_openstack(name_instance: str, name_image: str, name_flavor: str):
    print("Connecting to openstack...")
    conn = openstack.connect(
        auth_url=config.OS_AUTH_URL,
        project_name=config.OS_PROJECT_NAME,
        username=config.OS_USERNAME,
        password=config.OS_PASSWORD,
        user_domain_name=config.OS_USER_DOMAIN_NAME,
        project_domain_name=config.OS_PROJECT_DOMAIN_NAME
    )

    name_network = "demo-net"
    name_key = "mykey"
    sec_group = "default"

    image = conn.compute.find_image(name_image)
    flavor = conn.compute.find_flavor(name_flavor)
    network = conn.network.find_network(name_network)
    keypair = conn.compute.find_keypair(name_key)

    if not all([image, flavor, network, keypair]):
        raise HTTPException(status_code=404, detail="Error: resource not found")

    server = conn.compute.create_server(
        name=name_instance,
        image_id=image.id,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
        key_name=keypair.name,
        security_groups=[{"name": sec_group}]
    )

    print("Waiting for the instance to become active...")
    server = conn.compute.wait_for_server(server)

    return server


def _delete_vm_in_openstack(openstack_id: str):
    print("connecting to openstack...")
    conn = openstack.connect(
        auth_url=config.OS_AUTH_URL,
        project_name=config.OS_PROJECT_NAME,
        username=config.OS_USERNAME,
        password=config.OS_PASSWORD,
        user_domain_name=config.OS_USER_DOMAIN_NAME,
        project_domain_name=config.OS_PROJECT_DOMAIN_NAME
    )

    server = conn.compute.find_server(openstack_id)
    if server:
        conn.compute.delete_server(server)
        conn.compute.wait_for_delete(server)
    else:
        print("instance not found in openstack")


async def create_instance(db: AsyncSession, instance_data: InstanceRequest):
    server_os = await run_in_threadpool(
        _provision_vm_in_openstack,
        name_instance=instance_data.name,
        name_image=instance_data.image_name,
        name_flavor=instance_data.flavor_name
    )

    print(f"Salvez instanța {server_os.name} în baza de date...")

    new_instance = Instance(
        name=server_os.name,
        openstack_id=server_os.id,
        status=server_os.status,
        flavor_name=instance_data.flavor_name,
        image_name=instance_data.image_name
    )

    db.add(new_instance)
    await db.commit()
    await db.refresh(new_instance)

    return {
        "db_id": new_instance.id,
        "server_name": new_instance.name,
        "openstack_id": new_instance.openstack_id,
        "status": new_instance.status
    }


async def delete_instance(db: AsyncSession, instance_id: int):
    instance_db = await db.get(Instance, instance_id)

    if not instance_db:
        raise HTTPException(status_code=404, detail="instance id not found in database")

    if instance_db.openstack_id:
        await run_in_threadpool(_delete_vm_in_openstack, instance_db.openstack_id)

    await db.delete(instance_db)
    await db.commit()

    return {"message": "success"}


async def get_all_instances(db: AsyncSession):
    query = select(Instance)
    rezultat = await db.execute(query)
    instante = rezultat.scalars().all()

    return instante