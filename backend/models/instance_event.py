from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class InstanceEvent(Base):
    __tablename__ = "instance_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # info | warning | error — drives the icon/colour on the detail page
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="info")
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), index=True
    )
