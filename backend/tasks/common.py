import openstack
from core.config import config
from models.instance import Instance
from models.network import FloatingIP
from models.volume import Volume
from models.image import Image
from models.instance_event import InstanceEvent

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


def _set_instance_status(instance_id: int, status: str) -> None:
    with SessionLocal() as db:
        inst = db.query(Instance).filter(Instance.id == instance_id).first()
        if inst:
            inst.status = status
            db.commit()


def _log_event(instance_id: int, severity: str, message: str) -> None:
    try:
        with SessionLocal() as db:
            db.add(InstanceEvent(
                instance_id=instance_id, severity=severity, message=message[:255]
            ))
            db.commit()
    except Exception as exc:
        print(f"[_log_event] failed for instance {instance_id}: {exc}")


def _wait_for_status(conn, server_id: str, target: str, timeout: int = 180):
    import time
    remaining = timeout
    while remaining > 0:
        server = conn.compute.get_server(server_id)
        if server.status == target:
            return server
        if server.status == "ERROR":
            raise Exception(f"server entered ERROR while waiting for {target}")
        time.sleep(3)
        remaining -= 3
    raise Exception(f"timed out waiting for status {target}")


def _set_volume_status(volume_id: int, status: str) -> None:
    with SessionLocal() as db:
        vol = db.query(Volume).filter(Volume.id == volume_id).first()
        if vol:
            vol.status = status
            db.commit()


def _set_fip_status(floating_ip_id: int, status: str) -> None:
    with SessionLocal() as db:
        fip = db.query(FloatingIP).filter(FloatingIP.id == floating_ip_id).first()
        if fip:
            fip.status = status
            db.commit()


def _wait_for_volume_status(conn, volume_os_id: str, target: str, timeout: int = 180):
    import time
    remaining = timeout
    while remaining > 0:
        vol = conn.block_storage.get_volume(volume_os_id)
        if vol.status == target:
            return vol
        if vol.status in ("error", "error_deleting"):
            raise Exception(f"volume entered {vol.status} while waiting for {target}")
        time.sleep(3)
        remaining -= 3
    raise Exception(f"timed out waiting for volume status {target}")


def _set_image_status(image_id: int, status: str) -> None:
    with SessionLocal() as db:
        img = db.query(Image).filter(Image.id == image_id).first()
        if img:
            img.status = status
            db.commit()


def _wait_for_image_active(conn, image_os_id: str, timeout: int = 1800):
    import time
    remaining = timeout
    while remaining > 0:
        img = conn.image.get_image(image_os_id)
        if img.status == "active":
            return img
        if img.status in ("killed", "deleted", "deactivated"):
            raise Exception(f"image entered {img.status} during import")
        time.sleep(5)
        remaining -= 5
    raise Exception("timed out waiting for image to become active")
