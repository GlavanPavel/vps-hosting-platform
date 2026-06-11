from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Keypair(Base):
    __tablename__ = "keypairs"
    __table_args__ = (
        # a user cannot have two keypairs with the same name
        UniqueConstraint("user_id", "name", name="uq_keypair_user_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    # SHA256 fingerprint of the public key
    fingerprint: Mapped[str] = mapped_column(String(60), nullable=False)
    # name under which this key is registered in OpenStack (set after upload)
    openstack_name: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="keypairs")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="keypair")
