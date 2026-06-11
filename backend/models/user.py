from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # OpenStack project this org maps to — populated after OS project provisioning
    openstack_project_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    openstack_project_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="organization")
    networks: Mapped[list["Network"]] = relationship("Network", back_populates="organization")
    security_groups: Mapped[list["SecurityGroup"]] = relationship("SecurityGroup", back_populates="organization")
    floating_ips: Mapped[list["FloatingIP"]] = relationship("FloatingIP", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    keypairs: Mapped[list["Keypair"]] = relationship("Keypair", back_populates="user")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="user")
