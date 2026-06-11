import openstack
from core.celery_app import celery_app
from core.config import config
from domain.events import (
    InstanceProvisioningStarted,
    InstanceDeletionRequested,
    NetworkProvisioningStarted,
    SubnetProvisioningStarted,
)
from domain.dispatcher import on
from models.instance import Instance
from models.network import Network, Subnet, FloatingIP

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sync_db_url = config.DATABASE_URL.replace("+aiomysql", "+pymysql")
engine = create_engine(sync_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _os_connect() -> openstack.connection.Connection:
    return openstack.connect(
        auth_url=config.OS_AUTH_URL,
        project_name=config.OS_PROJECT_NAME,
        username=config.OS_USERNAME,
        password=config.OS_PASSWORD,
        user_domain_name=config.OS_USER_DOMAIN_NAME,
        project_domain_name=config.OS_PROJECT_DOMAIN_NAME,
    )


# ── Event handlers (wire domain events → Celery tasks) ───────────────────────

@on(InstanceProvisioningStarted)
def handle_provisioning_started(event: InstanceProvisioningStarted) -> None:
    provision_instance.delay(
        instance_id=event.instance_id,
        name=event.name,
        image_name=event.image_name,
        flavor_name=event.flavor_name,
        keypair_openstack_name=event.keypair_openstack_name,
        subnet_openstack_id=event.subnet_openstack_id,
        security_group_openstack_ids=event.security_group_openstack_ids,
    )


@on(InstanceDeletionRequested)
def handle_deletion_requested(event: InstanceDeletionRequested) -> None:
    delete_instance.delay(
        instance_id=event.instance_id,
        openstack_id=event.openstack_id,
    )


@on(NetworkProvisioningStarted)
def handle_network_provisioning(event: NetworkProvisioningStarted) -> None:
    provision_network.delay(
        network_id=event.network_id,
        organization_id=event.organization_id,
        name=event.name,
    )


# ── Celery tasks ──────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3)
def provision_instance(
    self,
    instance_id: int,
    name: str,
    image_name: str,
    flavor_name: str,
    keypair_openstack_name: str,
    subnet_openstack_id: str,
    security_group_openstack_ids: list[str],
):
    print(f"[Task {self.request.id}] Provisioning instance '{name}' (db_id={instance_id})")
    try:
        conn = _os_connect()

        image = conn.compute.find_image(image_name)
        flavor = conn.compute.find_flavor(flavor_name)
        keypair = conn.compute.find_keypair(keypair_openstack_name)

        if not all([image, flavor, keypair]):
            raise Exception(
                f"OpenStack resource not found — image={image}, flavor={flavor}, keypair={keypair}"
            )

        # Resolve the tenant network from the subnet before creating the server
        subnet_obj = conn.network.get_subnet(subnet_openstack_id)
        network_id = subnet_obj.network_id

        server = conn.compute.create_server(
            name=name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=[{"uuid": network_id}],
            key_name=keypair.name,
            security_groups=[{"name": sg_id} for sg_id in security_group_openstack_ids],
        )

        print(f"[Task {self.request.id}] Waiting for server to become ACTIVE...")
        server = conn.compute.wait_for_server(server)

        # Extract private IP from the tenant network
        private_ip = None
        for net_name, addresses in server.addresses.items():
            if addresses:
                private_ip = addresses[0]["addr"]
                break

        # Update instance record with OpenStack info
        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                instance.openstack_id = server.id
                instance.private_ip_address = private_ip
                instance.status = "ACTIVE"
                db.commit()

        # Allocate and associate a floating IP from the external provider pool
        _allocate_floating_ip(conn, instance_id, server.id, network_id)

        print(f"[Task {self.request.id}] Instance '{name}' is ACTIVE at private IP {private_ip}")
        return {"status": "success", "instance_id": instance_id, "private_ip": private_ip}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                instance.status = "ERROR"
                db.commit()
        raise self.retry(exc=exc, countdown=15)


def _allocate_floating_ip(
    conn: openstack.connection.Connection,
    instance_id: int,
    openstack_server_id: str,
    network_id: str,
) -> None:
    """Allocate a floating IP from the external network and attach it to the server.
    Writes a FloatingIP row to the database on success."""
    try:
        external_net = conn.network.find_network(config.OS_EXTERNAL_NETWORK, is_router_external=True)
        if not external_net:
            raise Exception(f"External network '{config.OS_EXTERNAL_NETWORK}' not found")

        floating_ip = conn.network.create_ip(floating_network_id=external_net.id)

        # Find the server's port on our tenant network to associate with
        ports = list(conn.network.ports(device_id=openstack_server_id, network_id=network_id))
        if not ports:
            raise Exception("No port found for server on tenant network")

        conn.network.update_ip(floating_ip, port_id=ports[0].id)

        print(f"Floating IP {floating_ip.floating_ip_address} associated with instance {instance_id}")

        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                fip = FloatingIP(
                    organization_id=instance.organization_id,
                    instance_id=instance_id,
                    ip_address=floating_ip.floating_ip_address,
                    openstack_floatingip_id=floating_ip.id,
                    external_network_name=config.OS_EXTERNAL_NETWORK,
                    status="ACTIVE",
                )
                db.add(fip)
                db.commit()

    except Exception as exc:
        # Floating IP failure is non-fatal for the instance itself — log and continue
        print(f"WARNING: Could not allocate floating IP for instance {instance_id}: {exc}")


@celery_app.task(bind=True, max_retries=3)
def delete_instance(self, instance_id: int, openstack_id: str):
    print(f"[Task {self.request.id}] Deleting instance {openstack_id}...")
    try:
        conn = _os_connect()

        # Disassociate and release any floating IPs before deleting the server
        with SessionLocal() as db:
            fip = db.query(FloatingIP).filter(FloatingIP.instance_id == instance_id).first()
            if fip:
                try:
                    conn.network.update_ip(fip.openstack_floatingip_id, port_id=None)
                    conn.network.delete_ip(fip.openstack_floatingip_id)
                except Exception as e:
                    print(f"WARNING: Could not release floating IP {fip.ip_address}: {e}")
                db.delete(fip)
                db.commit()

        server = conn.compute.find_server(openstack_id)
        if server:
            conn.compute.delete_server(server)
            conn.compute.wait_for_delete(server)
            print(f"[Task {self.request.id}] OpenStack server deleted")
        else:
            print(f"[Task {self.request.id}] Server not found in OpenStack — removing DB record only")

        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                db.delete(instance)
                db.commit()
                print(f"[Task {self.request.id}] Instance {instance_id} removed from database")

        return {"status": "success", "instance_id": instance_id}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)


@celery_app.task(bind=True, max_retries=3)
def provision_network(self, network_id: int, organization_id: int, name: str):
    """Create the OpenStack network + all pending subnets for this org."""
    print(f"[Task {self.request.id}] Provisioning network '{name}' (db_id={network_id})")
    try:
        conn = _os_connect()

        os_network = conn.network.create_network(name=name)

        with SessionLocal() as db:
            network = db.query(Network).filter(Network.id == network_id).first()
            if not network:
                raise Exception(f"Network {network_id} not found in database")
            network.openstack_network_id = os_network.id

            subnets = db.query(Subnet).filter(Subnet.network_id == network_id).all()
            for subnet in subnets:
                os_subnet = conn.network.create_subnet(
                    network_id=os_network.id,
                    name=subnet.name,
                    cidr=subnet.cidr,
                    ip_version=4,
                )
                subnet.openstack_subnet_id = os_subnet.id

            db.commit()

        print(f"[Task {self.request.id}] Network '{name}' provisioned: {os_network.id}")
        return {"status": "success", "network_id": network_id, "openstack_network_id": os_network.id}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)
