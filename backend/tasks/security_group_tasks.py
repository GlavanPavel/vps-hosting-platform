from core.celery_app import celery_app
from domain.dispatcher import on
from domain.events import SecurityGroupCreated, SecurityGroupDeletionRequested
from models.security_group import SecurityGroup, SecurityGroupRule
from tasks.common import SessionLocal, _os_connect


# event handlers

@on(SecurityGroupCreated)
def handle_security_group_created(event: SecurityGroupCreated) -> None:
    provision_security_group.delay(
        security_group_id=event.security_group_id,
        name=event.name,
        description=event.description,
    )


@on(SecurityGroupDeletionRequested)
def handle_security_group_deletion(event: SecurityGroupDeletionRequested) -> None:
    delete_security_group.delay(openstack_id=event.openstack_id)


# celery tasks

@celery_app.task(bind=True, max_retries=3)
def provision_security_group(self, security_group_id: int, name: str, description: str):
    print(f"[Task {self.request.id}] Provisioning security group '{name}' (db_id={security_group_id})")
    try:
        conn = _os_connect()

        os_sg = conn.network.create_security_group(
            name=f"{name}-{security_group_id}",
            description=description,
        )

        with SessionLocal() as db:
            sg = db.query(SecurityGroup).filter(SecurityGroup.id == security_group_id).first()
            if not sg:
                raise Exception(f"Security group {security_group_id} not found in database")
            sg.openstack_id = os_sg.id

            rules = (
                db.query(SecurityGroupRule)
                .filter(SecurityGroupRule.security_group_id == security_group_id)
                .all()
            )
            for rule in rules:
                try:
                    os_rule = conn.network.create_security_group_rule(
                        security_group_id=os_sg.id,
                        direction=rule.direction,
                        protocol=rule.protocol,
                        port_range_min=rule.port_range_min,
                        port_range_max=rule.port_range_max,
                        remote_ip_prefix=rule.remote_ip_prefix,
                        ethertype="IPv4",
                    )
                    rule.openstack_id = os_rule.id
                except Exception as rule_exc:
                    # OpenStack pre-creates default egress rules — a duplicate
                    # rule conflict is not fatal for the group as a whole
                    print(f"WARNING: Could not create rule {rule.id}: {rule_exc}")

            db.commit()

        print(f"[Task {self.request.id}] Security group '{name}' provisioned: {os_sg.id}")
        return {"status": "success", "security_group_id": security_group_id, "openstack_id": os_sg.id}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)


@celery_app.task(bind=True, max_retries=3)
def delete_security_group(self, openstack_id: str):
    print(f"[Task {self.request.id}] Deleting security group {openstack_id} from OpenStack")
    try:
        conn = _os_connect()
        os_sg = conn.network.find_security_group(openstack_id)
        if os_sg:
            conn.network.delete_security_group(os_sg)
            print(f"[Task {self.request.id}] Security group {openstack_id} deleted")
        else:
            print(f"[Task {self.request.id}] Security group {openstack_id} not found in OpenStack")
        return {"status": "success", "openstack_id": openstack_id}

    except Exception as exc:
        print(f"[Task {self.request.id}] ERROR: {exc}")
        raise self.retry(exc=exc, countdown=15)
