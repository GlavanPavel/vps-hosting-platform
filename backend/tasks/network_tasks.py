from core.celery_app import celery_app
from core.config import config
from domain.dispatcher import on
from domain.events import NetworkProvisioningStarted, NetworkDeletionRequested
from models.network import Network, Subnet
from tasks.common import SessionLocal, _os_connect



@on(NetworkProvisioningStarted)
def handle_network_provisioning(event: NetworkProvisioningStarted) -> None:
    provision_network.delay(
        network_id=event.network_id,
        organization_id=event.organization_id,
        name=event.name,
    )


@on(NetworkDeletionRequested)
def handle_network_deletion(event: NetworkDeletionRequested) -> None:
    delete_network.delay(
        openstack_network_id=event.openstack_network_id,
        openstack_router_id=event.openstack_router_id,
    )


# celery tasks

@celery_app.task(bind=True, max_retries=3)
def provision_network(self, network_id: int, organization_id: int, name: str):
    print(f"[Task {self.request.id}] Provisioning network '{name}' (db_id={network_id})")
    try:
        conn = _os_connect()

        os_network = conn.network.create_network(name=name)

        # provision all subnets and collect their openstack ids for router wiring
        os_subnet_ids = []
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
                os_subnet_ids.append(os_subnet.id)

            db.commit()

        # Create a router, set its external gateway, and attach each subnet
        external_net = conn.network.find_network(
            config.OS_EXTERNAL_NETWORK, is_router_external=True
        )
        if not external_net:
            raise Exception(f"External network '{config.OS_EXTERNAL_NETWORK}' not found")

        os_router = conn.network.create_router(
            name=f"{name}-router",
            external_gateway_info={"network_id": external_net.id},
        )
        for subnet_id in os_subnet_ids:
            conn.network.add_interface_to_router(os_router, subnet_id=subnet_id)

        with SessionLocal() as db:
            network = db.query(Network).filter(Network.id == network_id).first()
            if network:
                network.openstack_router_id = os_router.id
                db.commit()

        print(
            f"[Task {self.request.id}] Network '{name}' provisioned: "
            f"network={os_network.id} router={os_router.id}"
        )
        return {
            "status": "success",
            "network_id": network_id,
            "openstack_network_id": os_network.id,
            "openstack_router_id": os_router.id,
        }

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)


@celery_app.task(bind=True, max_retries=3)
def delete_network(self, openstack_network_id: str, openstack_router_id: str | None = None):
    print(f"[Task {self.request.id}] Deleting network {openstack_network_id} from OpenStack")
    try:
        conn = _os_connect()

        # detach all subnet interfaces and delete the router first
        if openstack_router_id:
            router = conn.network.find_router(openstack_router_id)
            if router:
                for port in conn.network.ports(device_id=router.id, device_owner="network:router_interface"):
                    try:
                        conn.network.remove_interface_from_router(router, subnet_id=port.fixed_ips[0]["subnet_id"])
                    except Exception as e:
                        print(f"WARNING: Could not remove router interface: {e}")
                conn.network.delete_router(router)
                print(f"[Task {self.request.id}] Router {openstack_router_id} deleted")

        os_network = conn.network.find_network(openstack_network_id)
        if os_network:
            for subnet_id in os_network.subnet_ids:
                conn.network.delete_subnet(subnet_id, ignore_missing=True)
            conn.network.delete_network(os_network)
            print(f"[Task {self.request.id}] Network {openstack_network_id} deleted")
        else:
            print(f"[Task {self.request.id}] Network {openstack_network_id} not found in OpenStack")

        return {"status": "success", "openstack_network_id": openstack_network_id}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)
