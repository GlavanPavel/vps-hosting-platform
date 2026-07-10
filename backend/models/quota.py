from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Quota(Base):
    __tablename__ = "quotas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, unique=True
    )
    max_instances: Mapped[int] = mapped_column(Integer, nullable=False)
    max_vcpus: Mapped[int] = mapped_column(Integer, nullable=False)
    max_ram_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    max_volumes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_storage_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    max_floating_ips: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization")
