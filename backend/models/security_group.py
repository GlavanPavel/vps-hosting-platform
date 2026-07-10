from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Table, Column
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


# many-to-many junction table
instance_security_groups = Table(
    "instance_security_groups",
    Base.metadata,
    Column("instance_id", Integer, ForeignKey("instances.id", ondelete="CASCADE"), primary_key=True),
    Column("security_group_id", Integer, ForeignKey("security_groups.id", ondelete="CASCADE"), primary_key=True),
)


class SecurityGroup(Base):
    __tablename__ = "security_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # OpenStack UUID for this security group (set after creation in OS)
    openstack_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="security_groups")
    rules: Mapped[list["SecurityGroupRule"]] = relationship(
        "SecurityGroupRule", back_populates="security_group", cascade="all, delete-orphan"
    )
    instances: Mapped[list["Instance"]] = relationship(
        "Instance", secondary=instance_security_groups, back_populates="security_groups"
    )


class SecurityGroupRule(Base):
    __tablename__ = "security_group_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    security_group_id: Mapped[int] = mapped_column(
        ForeignKey("security_groups.id", ondelete="CASCADE"), nullable=False
    )
    # ingress or egress
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    # tcp / udp / icmp — null means all protocols
    protocol: Mapped[str | None] = mapped_column(String(10), nullable=True)
    port_range_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    port_range_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # CIDR notation, e.g. 0.0.0.0/0
    remote_ip_prefix: Mapped[str | None] = mapped_column(String(50), nullable=True)
    openstack_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    security_group: Mapped["SecurityGroup"] = relationship("SecurityGroup", back_populates="rules")
