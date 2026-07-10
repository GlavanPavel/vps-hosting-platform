from datetime import datetime
from sqlalchemy import Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class CloudStats(Base):
    __tablename__ = "cloud_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hypervisor_count: Mapped[int] = mapped_column(Integer, default=0)
    vcpus_total: Mapped[int] = mapped_column(Integer, default=0)
    vcpus_used: Mapped[int] = mapped_column(Integer, default=0)
    ram_mb_total: Mapped[int] = mapped_column(Integer, default=0)
    ram_mb_used: Mapped[int] = mapped_column(Integer, default=0)
    disk_gb_total: Mapped[int] = mapped_column(Integer, default=0)
    disk_gb_used: Mapped[int] = mapped_column(Integer, default=0)
    running_vms: Mapped[int] = mapped_column(Integer, default=0)
    # Cinder pool capacity — nullable (best-effort)
    storage_gb_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_gb_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
