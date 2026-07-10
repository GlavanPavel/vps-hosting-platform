from core.celery_app import celery_app
from domain.dispatcher import on
from domain.events import (
    ImageCreationRequested,
    ImageDeletionRequested,
    ImageVisibilityChangeRequested,
    InstanceSnapshotRequested,
)
from models.image import Image
from models.instance import Instance
from tasks.common import (
    SessionLocal,
    _os_connect,
    _log_event,
    _set_image_status,
    _wait_for_image_active,
)


@on(ImageCreationRequested)
def handle_image_creation(event: ImageCreationRequested) -> None:
    provision_image.delay(
        image_id=event.image_id,
        name=event.name,
        source_url=event.source_url,
        disk_format=event.disk_format,
    )


@on(ImageDeletionRequested)
def handle_image_deletion(event: ImageDeletionRequested) -> None:
    delete_image.delay(image_id=event.image_id, openstack_image_id=event.openstack_image_id)


@on(ImageVisibilityChangeRequested)
def handle_image_visibility(event: ImageVisibilityChangeRequested) -> None:
    set_image_visibility.delay(
        image_id=event.image_id,
        openstack_image_id=event.openstack_image_id,
        is_public=event.is_public,
    )


@on(InstanceSnapshotRequested)
def handle_snapshot_requested(event: InstanceSnapshotRequested) -> None:
    snapshot_instance.delay(
        image_id=event.image_id,
        instance_openstack_id=event.instance_openstack_id,
        name=event.name,
    )


# celery tasks

@celery_app.task
def provision_image(image_id: int, name: str, source_url: str, disk_format: str):
    print(f"[provision_image] importing '{name}' from {source_url} (db_id={image_id})")
    try:
        conn = _os_connect()
        # create a queued image record, then start the URL import
        os_image = conn.image.create_image(
            name=f"{name}-{image_id}",
            disk_format=disk_format,
            container_format="bare",
            visibility="private",
            allow_duplicates=True,
        )
        _set_image_status(image_id, "importing")
        conn.image.import_image(os_image, method="web-download", uri=source_url)

        img = _wait_for_image_active(conn, os_image.id)
        with SessionLocal() as db:
            row = db.query(Image).filter(Image.id == image_id).first()
            if row:
                row.openstack_image_id = os_image.id
                row.status = "active"
                row.size_bytes = img.size
                row.min_disk_gb = img.min_disk
                db.commit()
        print(f"[provision_image] '{name}' active as {os_image.id}")
        return {"status": "success", "image_id": image_id, "openstack_image_id": os_image.id}
    except Exception as exc:
        print(f"[provision_image] ERROR: {exc}")
        _set_image_status(image_id, "ERROR")
        return {"status": "error", "image_id": image_id, "error": str(exc)}


@celery_app.task
def delete_image(image_id: int, openstack_image_id: str):
    print(f"[delete_image] deleting {openstack_image_id} (db_id={image_id})")
    try:
        conn = _os_connect()
        img = conn.image.find_image(openstack_image_id)
        if img:
            conn.image.delete_image(img)
        with SessionLocal() as db:
            row = db.query(Image).filter(Image.id == image_id).first()
            if row:
                db.delete(row)
                db.commit()
        return {"status": "success", "image_id": image_id}
    except Exception as exc:
        print(f"[delete_image] ERROR: {exc}")
        _set_image_status(image_id, "ERROR")
        return {"status": "error", "image_id": image_id, "error": str(exc)}


@celery_app.task
def set_image_visibility(image_id: int, openstack_image_id: str, is_public: bool):
    visibility = "public" if is_public else "private"
    print(f"[set_image_visibility] {openstack_image_id} -> {visibility}")
    try:
        conn = _os_connect()
        conn.image.update_image(openstack_image_id, visibility=visibility)
        return {"status": "success", "image_id": image_id, "visibility": visibility}
    except Exception as exc:
        print(f"[set_image_visibility] ERROR: {exc}")
        return {"status": "error", "image_id": image_id, "error": str(exc)}


@celery_app.task
def snapshot_instance(image_id: int, instance_openstack_id: str, name: str):
    glance_name = f"{name}-{image_id}"
    print(f"[snapshot_instance] snapshotting {instance_openstack_id} -> '{glance_name}' (db_id={image_id})")

    # resolve the DB instance id from its OpenStack id so we can log to its event feed
    with SessionLocal() as db:
        src = db.query(Instance).filter(Instance.openstack_id == instance_openstack_id).first()
        src_instance_id = src.id if src else None

    try:
        conn = _os_connect()
        server = conn.compute.find_server(instance_openstack_id)
        if not server:
            raise Exception("server not found")
        snap = conn.compute.create_server_image(server, glance_name)
        img = _wait_for_image_active(conn, snap.id)
        with SessionLocal() as db:
            row = db.query(Image).filter(Image.id == image_id).first()
            if row:
                row.openstack_image_id = snap.id
                row.status = "active"
                row.size_bytes = img.size
                row.min_disk_gb = img.min_disk
                row.disk_format = getattr(img, "disk_format", None) or row.disk_format
                db.commit()
        print(f"[snapshot_instance] '{glance_name}' active as {snap.id}")
        if src_instance_id:
            _log_event(src_instance_id, "info", f"Snapshot “{name}” created")
        return {"status": "success", "image_id": image_id, "openstack_image_id": snap.id}
    except Exception as exc:
        print(f"[snapshot_instance] ERROR: {exc}")
        _set_image_status(image_id, "ERROR")
        if src_instance_id:
            _log_event(src_instance_id, "error", f"Snapshot failed: {exc}")
        return {"status": "error", "image_id": image_id, "error": str(exc)}
