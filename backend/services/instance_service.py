import openstack
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Instance
from schemas.instance import InstanceRequest
from core.config import config

# --- NOU: Importăm task-ul Celery creat anterior ---
from tasks.vm_tasks import create_vm_background


def _delete_vm_in_openstack(openstack_id: str):
    """ Această funcție rămâne aici deocamdată.
    O vom putea muta în Celery mai târziu. """
    print("Connecting to openstack...")
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
        print("Instance not found in openstack")


async def create_instance(db: AsyncSession, instance_data: InstanceRequest):
    new_instance = Instance(
        name=instance_data.name,
        flavor_name=instance_data.flavor_name,
        image_name=instance_data.image_name
    )

    db.add(new_instance)
    await db.commit()
    await db.refresh(new_instance)

    print(f"Instanța '{new_instance.name}' (ID DB: {new_instance.id}) a fost salvată ca BUILD. Trimit la RabbitMQ...")

    # sending task to celery
    create_vm_background.delay(
        instance_id=new_instance.id,
        name_instance=instance_data.name,
        name_image=instance_data.image_name,
        name_flavor=instance_data.flavor_name
    )

    return {
        "db_id": new_instance.id,
        "server_name": new_instance.name,
        "status": new_instance.status,
        "message": "Creating server"
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