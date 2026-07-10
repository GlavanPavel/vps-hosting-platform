import base64
import openstack
from core.celery_app import celery_app
from core.config import config
from domain.dispatcher import on
from domain.events import (
    InstanceProvisioningStarted,
    InstanceDeletionRequested,
    InstanceStopRequested,
    InstanceStartRequested,
    InstanceRebootRequested,
)
from models.instance import Instance
from models.network import FloatingIP
from models.volume import Volume
from tasks.common import (
    SessionLocal,
    _os_connect,
    _set_instance_status,
    _log_event,
    _wait_for_status,
    _wait_for_volume_status,
)


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
        root_disk_gb=event.root_disk_gb,
        data_volume_size_gb=event.data_volume_size_gb,
        attach_volume_ids=event.attach_volume_ids,
        user_data=event.user_data,
        assign_floating_ip=event.assign_floating_ip,
    )


@on(InstanceDeletionRequested)
def handle_deletion_requested(event: InstanceDeletionRequested) -> None:
    delete_instance.delay(
        instance_id=event.instance_id,
        openstack_id=event.openstack_id,
    )


@on(InstanceStopRequested)
def handle_stop_requested(event: InstanceStopRequested) -> None:
    stop_instance.delay(instance_id=event.instance_id, openstack_id=event.openstack_id)


@on(InstanceStartRequested)
def handle_start_requested(event: InstanceStartRequested) -> None:
    start_instance.delay(instance_id=event.instance_id, openstack_id=event.openstack_id)


@on(InstanceRebootRequested)
def handle_reboot_requested(event: InstanceRebootRequested) -> None:
    reboot_instance.delay(instance_id=event.instance_id, openstack_id=event.openstack_id)


# celery tasks

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
    root_disk_gb: int = 0,
    data_volume_size_gb: int = 0,
    attach_volume_ids: list[int] | None = None,
    user_data: str = "",
    assign_floating_ip: bool = True,
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

        # resolve the tenant network from the subnet before creating the server
        subnet_obj = conn.network.get_subnet(subnet_openstack_id)
        network_id = subnet_obj.network_id

        server_kwargs = dict(
            name=name,
            flavor_id=flavor.id,
            networks=[{"uuid": network_id}],
            key_name=keypair.name,
            security_groups=[{"name": sg_id} for sg_id in security_group_openstack_ids],
        )
        if root_disk_gb and root_disk_gb > 0:
            # boot from a fresh Cinder volume created from the image
            server_kwargs["block_device_mapping_v2"] = [{
                "boot_index": 0,
                "uuid": image.id,
                "source_type": "image",
                "destination_type": "volume",
                "volume_size": root_disk_gb,
                "delete_on_termination": True,
            }]
        else:
            server_kwargs["image_id"] = image.id

        if user_data:
            # nova expects user_data base64-encoded
            server_kwargs["user_data"] = base64.b64encode(user_data.encode("utf-8")).decode("ascii")

        server = conn.compute.create_server(**server_kwargs)

        print(f"[Task {self.request.id}] Waiting for server to become ACTIVE...")
        server = conn.compute.wait_for_server(server)

        private_ip = None
        for net_name, addresses in server.addresses.items():
            if addresses:
                private_ip = addresses[0]["addr"]
                break

        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                instance.openstack_id = server.id
                instance.private_ip_address = private_ip
                instance.status = "ACTIVE"
                db.commit()

        _log_event(instance_id, "info", f"Instance is active (private IP {private_ip})")

        if assign_floating_ip:
            _allocate_floating_ip(conn, instance_id, server.id, network_id)

        # create/attach any requested block-storage volumes
        try:
            _attach_instance_volumes(
                conn, instance_id, server.id, data_volume_size_gb, attach_volume_ids or []
            )
        except Exception as vol_exc:
            print(f"[Task {self.request.id}] WARNING: volume setup failed: {vol_exc}")
            _log_event(instance_id, "warning", f"Volume setup failed: {vol_exc}")

        print(f"[Task {self.request.id}] Instance '{name}' is ACTIVE at private IP {private_ip}")
        return {"status": "success", "instance_id": instance_id, "private_ip": private_ip}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        with SessionLocal() as db:
            instance = db.query(Instance).filter(Instance.id == instance_id).first()
            if instance:
                instance.status = "ERROR"
                db.commit()
        _log_event(instance_id, "error", f"Provisioning failed: {exc}")
        raise self.retry(exc=exc, countdown=15)


def _attach_instance_volumes(
    conn, instance_id: int, server_os_id: str, data_volume_size_gb: int, attach_volume_ids: list[int]
) -> None:
    server = conn.compute.get_server(server_os_id)

    # a new data disk requested on the create form
    if data_volume_size_gb and data_volume_size_gb > 0:
        try:
            with SessionLocal() as db:
                inst = db.query(Instance).filter(Instance.id == instance_id).first()
                row = Volume(
                    organization_id=inst.organization_id,
                    name=f"{inst.name}-data",
                    size_gb=data_volume_size_gb,
                    status="creating",
                    instance_id=instance_id,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                row_id, vol_name = row.id, row.name
            os_vol = conn.block_storage.create_volume(name=f"{vol_name}-{row_id}", size=data_volume_size_gb)
            conn.block_storage.wait_for_status(os_vol, status="available", wait=300)
            attachment = conn.compute.create_volume_attachment(server, volume_id=os_vol.id)
            _wait_for_volume_status(conn, os_vol.id, "in-use", timeout=180)
            with SessionLocal() as db:
                row = db.query(Volume).filter(Volume.id == row_id).first()
                if row:
                    row.openstack_volume_id = os_vol.id
                    row.status = "in-use"
                    row.device = getattr(attachment, "device", None)
                    db.commit()
        except Exception as exc:
            print(f"[_attach_instance_volumes] new data volume failed: {exc}")

    # existing volumes selected on the create form
    for vid in attach_volume_ids:
        try:
            with SessionLocal() as db:
                row = db.query(Volume).filter(Volume.id == vid).first()
                if (not row or not row.openstack_volume_id
                        or row.instance_id is not None or row.status != "available"):
                    continue
                os_vol_id = row.openstack_volume_id
                row.status = "attaching"
                row.instance_id = instance_id
                db.commit()
            attachment = conn.compute.create_volume_attachment(server, volume_id=os_vol_id)
            _wait_for_volume_status(conn, os_vol_id, "in-use", timeout=180)
            with SessionLocal() as db:
                row = db.query(Volume).filter(Volume.id == vid).first()
                if row:
                    row.status = "in-use"
                    row.device = getattr(attachment, "device", None)
                    db.commit()
        except Exception as exc:
            print(f"[_attach_instance_volumes] attach volume {vid} failed: {exc}")
            with SessionLocal() as db:
                row = db.query(Volume).filter(Volume.id == vid).first()
                if row:
                    row.status = "available"
                    row.instance_id = None
                    row.device = None
                    db.commit()


def _allocate_floating_ip(
    conn: openstack.connection.Connection,
    instance_id: int,
    openstack_server_id: str,
    network_id: str,
) -> None:
    try:
        external_net = conn.network.find_network(config.OS_EXTERNAL_NETWORK, is_router_external=True)
        if not external_net:
            raise Exception(f"External network '{config.OS_EXTERNAL_NETWORK}' not found")

        floating_ip = conn.network.create_ip(floating_network_id=external_net.id)

        # find the server's port on our tenant network to associate with
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
                    status="in-use",
                )
                db.add(fip)
                db.commit()

        _log_event(instance_id, "info", f"Public IP {floating_ip.floating_ip_address} assigned")

    except Exception as exc:
        print(f"WARNING: Could not allocate floating IP for instance {instance_id}: {exc}")
        _log_event(instance_id, "warning", f"Could not assign a public IP: {exc}")


@celery_app.task(bind=True, max_retries=3)
def delete_instance(self, instance_id: int, openstack_id: str):
    print(f"[Task {self.request.id}] Deleting instance {openstack_id}...")
    try:
        conn = _os_connect()
        with SessionLocal() as db:
            fip = db.query(FloatingIP).filter(FloatingIP.instance_id == instance_id).first()
            if fip:
                try:
                    conn.network.update_ip(fip.openstack_floatingip_id, port_id=None)
                except Exception as e:
                    print(f"WARNING: Could not disassociate floating IP {fip.ip_address}: {e}")
                fip.instance_id = None
                fip.status = "available"
                db.commit()

        server = conn.compute.find_server(openstack_id)
        if server:
            conn.compute.delete_server(server)
            conn.compute.wait_for_delete(server)
            print(f"[Task {self.request.id}] OpenStack server deleted")
        else:
            print(f"[Task {self.request.id}] Server not found in OpenStack — removing DB record only")

        # nova auto-detaches volumes on server delete
        with SessionLocal() as db:
            for vol in db.query(Volume).filter(Volume.instance_id == instance_id).all():
                vol.status = "available"
                vol.instance_id = None
                vol.device = None
            db.commit()

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


@celery_app.task
def stop_instance(instance_id: int, openstack_id: str):
    print(f"[stop_instance] stopping {openstack_id} (db_id={instance_id})")
    try:
        conn = _os_connect()
        server = conn.compute.find_server(openstack_id)
        if server and server.status != "SHUTOFF":
            conn.compute.stop_server(server)
            _wait_for_status(conn, openstack_id, "SHUTOFF", timeout=180)
        _set_instance_status(instance_id, "SHUTOFF")
        _log_event(instance_id, "info", "Instance powered off")
        return {"status": "success", "instance_id": instance_id, "state": "SHUTOFF"}
    except Exception as exc:
        print(f"[stop_instance] ERROR: {exc}")
        _set_instance_status(instance_id, "ERROR")
        _log_event(instance_id, "error", f"Stop failed: {exc}")
        return {"status": "error", "instance_id": instance_id, "error": str(exc)}


@celery_app.task
def start_instance(instance_id: int, openstack_id: str):
    print(f"[start_instance] starting {openstack_id} (db_id={instance_id})")
    try:
        conn = _os_connect()
        server = conn.compute.find_server(openstack_id)
        if server and server.status != "ACTIVE":
            conn.compute.start_server(server)
            _wait_for_status(conn, openstack_id, "ACTIVE", timeout=300)
        _set_instance_status(instance_id, "ACTIVE")
        _log_event(instance_id, "info", "Instance started")
        return {"status": "success", "instance_id": instance_id, "state": "ACTIVE"}
    except Exception as exc:
        print(f"[start_instance] ERROR: {exc}")
        _set_instance_status(instance_id, "ERROR")
        _log_event(instance_id, "error", f"Start failed: {exc}")
        return {"status": "error", "instance_id": instance_id, "error": str(exc)}


@celery_app.task
def reboot_instance(instance_id: int, openstack_id: str):
    import time
    print(f"[reboot_instance] rebooting {openstack_id} (db_id={instance_id})")
    try:
        conn = _os_connect()
        server = conn.compute.find_server(openstack_id)
        if server:
            conn.compute.reboot_server(server, "SOFT")
            # let nova move into REBOOT before we wait for the return to ACTIVE,
            # otherwise we'd catch the brief pre-reboot ACTIVE and return early
            time.sleep(5)
            _wait_for_status(conn, openstack_id, "ACTIVE", timeout=300)
        _set_instance_status(instance_id, "ACTIVE")
        _log_event(instance_id, "info", "Reboot completed")
        return {"status": "success", "instance_id": instance_id, "state": "ACTIVE"}
    except Exception as exc:
        print(f"[reboot_instance] ERROR: {exc}")
        _set_instance_status(instance_id, "ERROR")
        _log_event(instance_id, "error", f"Reboot failed: {exc}")
        return {"status": "error", "instance_id": instance_id, "error": str(exc)}


# synchronous tasks

@celery_app.task
def get_console_url(openstack_id: str) -> dict:
    conn = _os_connect()
    server = conn.compute.find_server(openstack_id)
    if not server:
        raise Exception(f"Server {openstack_id} not found in OpenStack")
    remote = conn.compute.create_server_remote_console(server, protocol="vnc", type="novnc")
    return {"url": remote.url}


@celery_app.task
def get_console_output(openstack_id: str, length: int = 200) -> dict:
    conn = _os_connect()
    server = conn.compute.find_server(openstack_id)
    if not server:
        raise Exception(f"Server {openstack_id} not found in OpenStack")
    result = conn.compute.get_server_console_output(server, length=length)
    # the SDK returns {"output": "..."}
    output = result.get("output", "") if isinstance(result, dict) else str(result or "")
    return {"output": output}
