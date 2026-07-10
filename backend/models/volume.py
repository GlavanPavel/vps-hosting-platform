from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Volume(Base):
    __tablename__ = "volumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    size_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    # Cinder volume UUID
    openstack_volume_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(20), default="creating")
    # nullable FK — set when attached, cleared on detach; survives instance deletion
    instance_id: Mapped[int | None] = mapped_column(
        ForeignKey("instances.id", ondelete="SET NULL"), nullable=True
    )
    # guest device path when attached, e.g. /dev/vdb
    device: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="volumes")
    instance: Mapped["Instance | None"] = relationship("Instance", back_populates="volumes")
