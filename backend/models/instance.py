from sqlalchemy import String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from backend.core.database import Base

class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # numele dat de utilizator
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # id-ul returnat de openstack
    openstack_id: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)

    status: Mapped[str] = mapped_column(String(20), default="BUILD")
    flavor_name: Mapped[str] = mapped_column(String(50), nullable=True)
    image_name: Mapped[str] = mapped_column(String(50), nullable=True)

    # data si ora la care a fost ceruta instanta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())