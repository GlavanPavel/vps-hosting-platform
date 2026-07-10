from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# instance lifecylce

@dataclass
class InstanceProvisioningStarted(DomainEvent):
    instance_id: int = 0
    name: str = ""
    image_name: str = ""
    flavor_name: str = ""
    keypair_openstack_name: str = ""
    # OpenStack UUID for the tenant subnet
    subnet_openstack_id: str = ""
    # OpenStack UUIDs of every security group to attach
    security_group_openstack_ids: list[str] = field(default_factory=list)
    # optional custom root disk size (GB)
    root_disk_gb: int = 0
    # optional extra data disk to create + attach once the server is ACTIVE
    data_volume_size_gb: int = 0
    # DB ids of existing available volumes to attach once the server is ACTIVE
    attach_volume_ids: list[int] = field(default_factory=list)
    user_data: str = ""
    # whether to allocate + associate a floating IP once the server is ACTIVE
    assign_floating_ip: bool = True


@dataclass
class InstanceBecameActive(DomainEvent):
    instance_id: int = 0
    openstack_id: str = ""
    private_ip: str = ""


@dataclass
class FloatingIPAssigned(DomainEvent):
    instance_id: int = 0
    floating_ip_address: str = ""
    openstack_floatingip_id: str = ""


@dataclass
class InstanceProvisioningFailed(DomainEvent):
    instance_id: int = 0
    reason: str = ""


# instance deletion

@dataclass
class InstanceDeletionRequested(DomainEvent):
    instance_id: int = 0
    openstack_id: str = ""


@dataclass
class InstanceDeleted(DomainEvent):
    instance_id: int = 0


# instance power actions

@dataclass
class InstanceStopRequested(DomainEvent):
    instance_id: int = 0
    openstack_id: str = ""


@dataclass
class InstanceStartRequested(DomainEvent):
    instance_id: int = 0
    openstack_id: str = ""


@dataclass
class InstanceRebootRequested(DomainEvent):
    instance_id: int = 0
    openstack_id: str = ""


# keypair lifecycle

@dataclass
class KeypairCreated(DomainEvent):
    keypair_id: int = 0
    name: str = ""
    public_key: str = ""


@dataclass
class KeypairDeletionRequested(DomainEvent):
    openstack_name: str = ""


# security group lifecycle

@dataclass
class SecurityGroupCreated(DomainEvent):
    security_group_id: int = 0
    name: str = ""
    description: str = ""


@dataclass
class SecurityGroupDeletionRequested(DomainEvent):
    openstack_id: str = ""


# network lifecycle

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


@dataclass
class NetworkDeletionRequested(DomainEvent):
    openstack_network_id: str = ""
    openstack_router_id: str | None = None


# floating ip lifecycle

@dataclass
class FloatingIPAllocationRequested(DomainEvent):
    organization_id: int = 0


@dataclass
class FloatingIPAssociationRequested(DomainEvent):
    floating_ip_id: int = 0
    openstack_floatingip_id: str = ""
    instance_openstack_id: str = ""


@dataclass
class FloatingIPDisassociationRequested(DomainEvent):
    floating_ip_id: int = 0
    openstack_floatingip_id: str = ""


@dataclass
class FloatingIPReleaseRequested(DomainEvent):
    floating_ip_id: int = 0
    openstack_floatingip_id: str = ""


# volume lifecycle

@dataclass
class VolumeCreationRequested(DomainEvent):
    volume_id: int = 0
    name: str = ""
    size_gb: int = 0


@dataclass
class VolumeDeletionRequested(DomainEvent):
    volume_id: int = 0
    openstack_volume_id: str = ""


@dataclass
class VolumeAttachRequested(DomainEvent):
    volume_id: int = 0
    openstack_volume_id: str = ""
    instance_openstack_id: str = ""


@dataclass
class VolumeDetachRequested(DomainEvent):
    volume_id: int = 0
    openstack_volume_id: str = ""
    instance_openstack_id: str = ""


# custom image lifecycle

@dataclass
class ImageCreationRequested(DomainEvent):
    image_id: int = 0
    name: str = ""
    source_url: str = ""
    disk_format: str = "qcow2"


@dataclass
class ImageDeletionRequested(DomainEvent):
    image_id: int = 0
    openstack_image_id: str = ""


@dataclass
class ImageVisibilityChangeRequested(DomainEvent):
    image_id: int = 0
    openstack_image_id: str = ""
    is_public: bool = False


@dataclass
class InstanceSnapshotRequested(DomainEvent):
    image_id: int = 0
    instance_openstack_id: str = ""
    name: str = ""


# organization lifecycle (admin)

@dataclass
class OrganizationDeletionRequested(DomainEvent):
    organization_id: int = 0
