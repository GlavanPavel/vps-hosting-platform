from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # "url" (imported via web-download) | "snapshot" (captured from an instance)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="url")
    # URL Glance fetches the disk image from — null for snapshots
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # the instance a snapshot was taken from (SET NULL so the image survives its deletion)
    source_instance_id: Mapped[int | None] = mapped_column(
        ForeignKey("instances.id", ondelete="SET NULL"), nullable=True
    )
    # Glance disk_format: qcow2 | raw | vmdk | vdi | iso
    disk_format: Mapped[str] = mapped_column(String(20), default="qcow2")
    # Glance image UUID — populated by Celery once the import/snapshot finishes
    openstack_image_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    # queued → importing/snapshotting → active | ERROR
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # when true the image is visible to every org (Glance visibility=public)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # populated from Glance once active (image size may exceed 2 GB → BigInteger)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Glance min_disk (GB) — the smallest root disk an instance needs for this image
    min_disk_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="images")
