from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from models.security_group import instance_security_groups


class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # UUID returned by OpenStack after server creation
    openstack_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    # BUILD → ACTIVE → DELETING → (row deleted)  |  ERROR on failure
    status: Mapped[str] = mapped_column(String(20), default="BUILD")
    flavor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    image_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # FK to the keypair the user selected — nullable so rows survive keypair deletion
    keypair_id: Mapped[int | None] = mapped_column(
        ForeignKey("keypairs.id", ondelete="SET NULL"), nullable=True
    )
    # the private subnet this instance lives on
    subnet_id: Mapped[int] = mapped_column(ForeignKey("subnets.id"), nullable=False)

    # private IP assigned by OpenStack on the tenant subnet (populated after BUILD)
    private_ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="instances")
    user: Mapped["User"] = relationship("User", back_populates="instances")
    keypair: Mapped["Keypair | None"] = relationship("Keypair", back_populates="instances")
    subnet: Mapped["Subnet"] = relationship("Subnet", back_populates="instances")
    security_groups: Mapped[list["SecurityGroup"]] = relationship(
        "SecurityGroup", secondary=instance_security_groups, back_populates="instances"
    )
    # one-to-one: a floating IP points at most one instance
    floating_ip: Mapped["FloatingIP | None"] = relationship(
        "FloatingIP", back_populates="instance", uselist=False
    )
