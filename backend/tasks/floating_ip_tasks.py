from core.celery_app import celery_app
from core.config import config
from domain.dispatcher import on
from domain.events import (
    FloatingIPAllocationRequested,
    FloatingIPAssociationRequested,
    FloatingIPDisassociationRequested,
    FloatingIPReleaseRequested,
)
from models.network import FloatingIP
from tasks.common import SessionLocal, _os_connect, _set_fip_status


# event handlers

@on(FloatingIPAllocationRequested)
def handle_floating_ip_allocation(event: FloatingIPAllocationRequested) -> None:
    allocate_floating_ip.delay(organization_id=event.organization_id)


@on(FloatingIPAssociationRequested)
def handle_floating_ip_association(event: FloatingIPAssociationRequested) -> None:
    associate_floating_ip.delay(
        floating_ip_id=event.floating_ip_id,
        openstack_floatingip_id=event.openstack_floatingip_id,
        instance_openstack_id=event.instance_openstack_id,
    )


@on(FloatingIPDisassociationRequested)
def handle_floating_ip_disassociation(event: FloatingIPDisassociationRequested) -> None:
    disassociate_floating_ip.delay(
        floating_ip_id=event.floating_ip_id,
        openstack_floatingip_id=event.openstack_floatingip_id,
    )


@on(FloatingIPReleaseRequested)
def handle_floating_ip_release(event: FloatingIPReleaseRequested) -> None:
    release_floating_ip.delay(
        floating_ip_id=event.floating_ip_id,
        openstack_floatingip_id=event.openstack_floatingip_id,
    )


# celery tasks

@celery_app.task
def allocate_floating_ip(organization_id: int):
    print(f"[allocate_floating_ip] org={organization_id}")
    try:
        conn = _os_connect()
        external_net = conn.network.find_network(config.OS_EXTERNAL_NETWORK, is_router_external=True)
        if not external_net:
            raise Exception(f"External network '{config.OS_EXTERNAL_NETWORK}' not found")
        floating_ip = conn.network.create_ip(floating_network_id=external_net.id)
        with SessionLocal() as db:
            row = FloatingIP(
                organization_id=organization_id,
                instance_id=None,
                ip_address=floating_ip.floating_ip_address,
                openstack_floatingip_id=floating_ip.id,
                external_network_name=config.OS_EXTERNAL_NETWORK,
                status="available",
            )
            db.add(row)
            db.commit()
        print(f"[allocate_floating_ip] reserved {floating_ip.floating_ip_address}")
        return {"status": "success", "ip": floating_ip.floating_ip_address}
    except Exception as exc:
        print(f"[allocate_floating_ip] ERROR: {exc}")
        return {"status": "error", "error": str(exc)}


@celery_app.task
def associate_floating_ip(floating_ip_id: int, openstack_floatingip_id: str, instance_openstack_id: str):
    print(f"[associate_floating_ip] {openstack_floatingip_id} -> {instance_openstack_id}")
    try:
        conn = _os_connect()
        # a server has one port on its tenant network — the one with fixed IPs
        ports = [p for p in conn.network.ports(device_id=instance_openstack_id) if p.fixed_ips]
        if not ports:
            raise Exception("no port found for server on its tenant network")
        conn.network.update_ip(openstack_floatingip_id, port_id=ports[0].id)
        _set_fip_status(floating_ip_id, "in-use")
        return {"status": "success", "floating_ip_id": floating_ip_id}
    except Exception as exc:
        print(f"[associate_floating_ip] ERROR: {exc}")
        with SessionLocal() as db:
            fip = db.query(FloatingIP).filter(FloatingIP.id == floating_ip_id).first()
            if fip:
                fip.instance_id = None
                fip.status = "available"
                db.commit()
        return {"status": "error", "floating_ip_id": floating_ip_id, "error": str(exc)}


@celery_app.task
def disassociate_floating_ip(floating_ip_id: int, openstack_floatingip_id: str):
    print(f"[disassociate_floating_ip] {openstack_floatingip_id}")
    try:
        conn = _os_connect()
        conn.network.update_ip(openstack_floatingip_id, port_id=None)
        with SessionLocal() as db:
            fip = db.query(FloatingIP).filter(FloatingIP.id == floating_ip_id).first()
            if fip:
                fip.instance_id = None
                fip.status = "available"
                db.commit()
        return {"status": "success", "floating_ip_id": floating_ip_id}
    except Exception as exc:
        print(f"[disassociate_floating_ip] ERROR: {exc}")
        _set_fip_status(floating_ip_id, "ERROR")
        return {"status": "error", "floating_ip_id": floating_ip_id, "error": str(exc)}


@celery_app.task
def release_floating_ip(floating_ip_id: int, openstack_floatingip_id: str):
    print(f"[release_floating_ip] {openstack_floatingip_id}")
    try:
        conn = _os_connect()
        try:
            conn.network.update_ip(openstack_floatingip_id, port_id=None)
        except Exception:
            pass  # may already be detached
        conn.network.delete_ip(openstack_floatingip_id, ignore_missing=True)
        with SessionLocal() as db:
            fip = db.query(FloatingIP).filter(FloatingIP.id == floating_ip_id).first()
            if fip:
                db.delete(fip)
                db.commit()
        return {"status": "success", "floating_ip_id": floating_ip_id}
    except Exception as exc:
        print(f"[release_floating_ip] ERROR: {exc}")
        _set_fip_status(floating_ip_id, "ERROR")
        return {"status": "error", "floating_ip_id": floating_ip_id, "error": str(exc)}
