from core.celery_app import celery_app
from domain.dispatcher import on
from domain.events import KeypairCreated, KeypairDeletionRequested
from models.keypair import Keypair
from tasks.common import SessionLocal, _os_connect



@on(KeypairCreated)
def handle_keypair_created(event: KeypairCreated) -> None:
    upload_keypair.delay(
        keypair_id=event.keypair_id,
        name=event.name,
        public_key=event.public_key,
    )


@on(KeypairDeletionRequested)
def handle_keypair_deletion(event: KeypairDeletionRequested) -> None:
    delete_keypair.delay(openstack_name=event.openstack_name)


# celery tasks

@celery_app.task(bind=True, max_retries=3)
def upload_keypair(self, keypair_id: int, name: str, public_key: str):
    print(f"[Task {self.request.id}] Uploading keypair '{name}' (db_id={keypair_id})")
    try:
        conn = _os_connect()
        openstack_name = f"{name}-{keypair_id}"
        conn.compute.create_keypair(name=openstack_name, public_key=public_key)

        with SessionLocal() as db:
            keypair = db.query(Keypair).filter(Keypair.id == keypair_id).first()
            if keypair:
                keypair.openstack_name = openstack_name
                db.commit()

        print(f"[Task {self.request.id}] Keypair uploaded as '{openstack_name}'")
        return {"status": "success", "keypair_id": keypair_id, "openstack_name": openstack_name}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)


@celery_app.task(bind=True, max_retries=3)
def delete_keypair(self, openstack_name: str):
    """Remove a keypair from OpenStack after its DB row has been deleted."""
    print(f"[Task {self.request.id}] Deleting keypair '{openstack_name}' from OpenStack")
    try:
        conn = _os_connect()
        keypair = conn.compute.find_keypair(openstack_name)
        if keypair:
            conn.compute.delete_keypair(keypair)
            print(f"[Task {self.request.id}] Keypair '{openstack_name}' deleted")
        else:
            print(f"[Task {self.request.id}] Keypair '{openstack_name}' not found in OpenStack")
        return {"status": "success", "openstack_name": openstack_name}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)
