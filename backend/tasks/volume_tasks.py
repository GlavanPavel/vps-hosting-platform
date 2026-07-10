from core.celery_app import celery_app
from domain.dispatcher import on
from domain.events import (
    VolumeCreationRequested,
    VolumeDeletionRequested,
    VolumeAttachRequested,
    VolumeDetachRequested,
)
from models.volume import Volume
from tasks.common import SessionLocal, _os_connect, _set_volume_status, _wait_for_volume_status


@on(VolumeCreationRequested)
def handle_volume_creation(event: VolumeCreationRequested) -> None:
    provision_volume.delay(volume_id=event.volume_id, name=event.name, size_gb=event.size_gb)


@on(VolumeDeletionRequested)
def handle_volume_deletion(event: VolumeDeletionRequested) -> None:
    delete_volume.delay(volume_id=event.volume_id, openstack_volume_id=event.openstack_volume_id)


@on(VolumeAttachRequested)
def handle_volume_attach(event: VolumeAttachRequested) -> None:
    attach_volume.delay(
        volume_id=event.volume_id,
        openstack_volume_id=event.openstack_volume_id,
        instance_openstack_id=event.instance_openstack_id,
    )


@on(VolumeDetachRequested)
def handle_volume_detach(event: VolumeDetachRequested) -> None:
    detach_volume.delay(
        volume_id=event.volume_id,
        openstack_volume_id=event.openstack_volume_id,
        instance_openstack_id=event.instance_openstack_id,
    )


# celery tasks

@celery_app.task
def provision_volume(volume_id: int, name: str, size_gb: int):
    print(f"[provision_volume] creating '{name}' ({size_gb}GB, db_id={volume_id})")
    try:
        conn = _os_connect()
        os_vol = conn.block_storage.create_volume(name=f"{name}-{volume_id}", size=size_gb)
        conn.block_storage.wait_for_status(os_vol, status="available", wait=300)
        with SessionLocal() as db:
            vol = db.query(Volume).filter(Volume.id == volume_id).first()
            if vol:
                vol.openstack_volume_id = os_vol.id
                vol.status = "available"
                db.commit()
        return {"status": "success", "volume_id": volume_id, "openstack_volume_id": os_vol.id}
    except Exception as exc:
        print(f"[provision_volume] ERROR: {exc}")
        _set_volume_status(volume_id, "ERROR")
        return {"status": "error", "volume_id": volume_id, "error": str(exc)}


@celery_app.task
def delete_volume(volume_id: int, openstack_volume_id: str):
    print(f"[delete_volume] deleting {openstack_volume_id} (db_id={volume_id})")
    try:
        conn = _os_connect()
        os_vol = conn.block_storage.find_volume(openstack_volume_id)
        if os_vol:
            conn.block_storage.delete_volume(os_vol)
            try:
                conn.block_storage.wait_for_delete(os_vol, wait=180)
            except Exception:
                pass
        with SessionLocal() as db:
            vol = db.query(Volume).filter(Volume.id == volume_id).first()
            if vol:
                db.delete(vol)
                db.commit()
        return {"status": "success", "volume_id": volume_id}
    except Exception as exc:
        print(f"[delete_volume] ERROR: {exc}")
        _set_volume_status(volume_id, "ERROR")
        return {"status": "error", "volume_id": volume_id, "error": str(exc)}


@celery_app.task
def attach_volume(volume_id: int, openstack_volume_id: str, instance_openstack_id: str):
    print(f"[attach_volume] {openstack_volume_id} -> {instance_openstack_id}")
    try:
        conn = _os_connect()
        server = conn.compute.find_server(instance_openstack_id)
        if not server:
            raise Exception("server not found")
        attachment = conn.compute.create_volume_attachment(server, volume_id=openstack_volume_id)
        _wait_for_volume_status(conn, openstack_volume_id, "in-use", timeout=180)
        with SessionLocal() as db:
            vol = db.query(Volume).filter(Volume.id == volume_id).first()
            if vol:
                vol.status = "in-use"
                vol.device = getattr(attachment, "device", None)
                db.commit()
        return {"status": "success", "volume_id": volume_id}
    except Exception as exc:
        print(f"[attach_volume] ERROR: {exc}")
        with SessionLocal() as db:
            vol = db.query(Volume).filter(Volume.id == volume_id).first()
            if vol:
                vol.status = "available"
                vol.instance_id = None
                vol.device = None
                db.commit()
        return {"status": "error", "volume_id": volume_id, "error": str(exc)}


@celery_app.task
def detach_volume(volume_id: int, openstack_volume_id: str, instance_openstack_id: str):
    print(f"[detach_volume] {openstack_volume_id} from {instance_openstack_id}")
    try:
        conn = _os_connect()
        server = conn.compute.find_server(instance_openstack_id)
        if server:
            conn.compute.delete_volume_attachment(openstack_volume_id, server, ignore_missing=True)
        _wait_for_volume_status(conn, openstack_volume_id, "available", timeout=180)
        with SessionLocal() as db:
            vol = db.query(Volume).filter(Volume.id == volume_id).first()
            if vol:
                vol.status = "available"
                vol.instance_id = None
                vol.device = None
                db.commit()
        return {"status": "success", "volume_id": volume_id}
    except Exception as exc:
        print(f"[detach_volume] ERROR: {exc}")
        _set_volume_status(volume_id, "ERROR")
        return {"status": "error", "volume_id": volume_id, "error": str(exc)}
