import openstack
from core.celery_app import celery_app
from core.config import config
from models.instance import Instance

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# celery e sincron
sync_db_url = config.DATABASE_URL.replace("+aiomysql", "+pymysql")
engine = create_engine(sync_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, max_retries=3)
def create_vm_background(self, instance_id: int, name_instance: str, name_image: str, name_flavor: str):
    print(f"[Task {self.request.id}] {name_instance}")

    try:
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
            raise Exception("Openstack resource not found")

        server = conn.compute.create_server(
            name=name_instance,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=[{"uuid": network.id}],
            key_name=keypair.name,
            security_groups=[{"name": sec_group}]
        )

        print(f"[Task {self.request.id}] Building the server")
        server = conn.compute.wait_for_server(server)

        ip_address = None
        if name_network in server.addresses:
            ip_address = server.addresses[name_network][0]["addr"]

        print(f"[Task {self.request.id}] Server is now active at: {ip_address}")

        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                instance.status = server.status
                instance.openstack_id = server.id
                instance.ip_address = ip_address
                db.commit()

        return {"status": "success", "vm_name": name_instance, "ip": ip_address}

    except Exception as exc:
        print(f"[Task {self.request.id}] EROARE: {str(exc)}")
        raise self.retry(exc=exc, countdown=15)