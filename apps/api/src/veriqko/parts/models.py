from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqko.db.base import Base, TimestampMixin, UUIDMixin


class Part(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "parts"

    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

class PartUsage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "part_usages"

    job_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("jobs.id"), nullable=False)
    part_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("parts.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job", backref="parts_used")
    part = relationship("Part")
