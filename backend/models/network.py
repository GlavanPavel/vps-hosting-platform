from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    openstack_network_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="networks")
    subnets: Mapped[list["Subnet"]] = relationship(
        "Subnet", back_populates="network", cascade="all, delete-orphan"
    )


class Subnet(Base):
    __tablename__ = "subnets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # CIDR block, e.g. 10.0.1.0/24
    cidr: Mapped[str] = mapped_column(String(50), nullable=False)
    openstack_subnet_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    network: Mapped["Network"] = relationship("Network", back_populates="subnets")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="subnet")


class FloatingIP(Base):
    __tablename__ = "floating_ips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    # null when the floating IP is allocated but not yet attached to an instance
    instance_id: Mapped[int | None] = mapped_column(
        ForeignKey("instances.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    openstack_floatingip_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # the external provider pool this IP came from (e.g. "public", "ext-net")
    external_network_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # mirrors OpenStack port status: ACTIVE / DOWN / ERROR
    status: Mapped[str] = mapped_column(String(20), default="DOWN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="floating_ips")
    instance: Mapped["Instance | None"] = relationship("Instance", back_populates="floating_ip")
