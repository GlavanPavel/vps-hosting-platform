from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Instance lifecycle ────────────────────────────────────────────────────────

@dataclass
class InstanceProvisioningStarted(DomainEvent):
    """Raised by the service layer after the DB record is created with status=BUILD.
    Celery picks this up and performs the actual OpenStack work."""
    instance_id: int = 0
    name: str = ""
    image_name: str = ""
    flavor_name: str = ""
    # resolved from the Keypair row — the name OpenStack knows about
    keypair_openstack_name: str = ""
    # OpenStack UUID for the tenant subnet
    subnet_openstack_id: str = ""
    # OpenStack UUIDs of every security group to attach
    security_group_openstack_ids: list[str] = field(default_factory=list)


@dataclass
class InstanceBecameActive(DomainEvent):
    """Raised by the Celery task after OpenStack reports the server as ACTIVE."""
    instance_id: int = 0
    openstack_id: str = ""
    private_ip: str = ""


@dataclass
class FloatingIPAssigned(DomainEvent):
    """Raised by the Celery task after a floating IP is allocated and associated."""
    instance_id: int = 0
    floating_ip_address: str = ""
    openstack_floatingip_id: str = ""


@dataclass
class InstanceProvisioningFailed(DomainEvent):
    instance_id: int = 0
    reason: str = ""


# ── Instance deletion ─────────────────────────────────────────────────────────

@dataclass
class InstanceDeletionRequested(DomainEvent):
    """Raised by the service layer after the DB status is set to DELETING."""
    instance_id: int = 0
    openstack_id: str = ""


@dataclass
class InstanceDeleted(DomainEvent):
    """Raised by the Celery task after the server is gone from OpenStack and DB."""
    instance_id: int = 0


# ── Network lifecycle ─────────────────────────────────────────────────────────

@dataclass
class NetworkProvisioningStarted(DomainEvent):
    network_id: int = 0
    organization_id: int = 0
    name: str = ""


@dataclass
class SubnetProvisioningStarted(DomainEvent):
    subnet_id: int = 0
    network_openstack_id: str = ""
    name: str = ""
    cidr: str = ""
