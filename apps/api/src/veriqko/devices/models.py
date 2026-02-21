"""Device database models."""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqko.db.base import Base, TimestampMixin, UUIDMixin


class Brand(Base, UUIDMixin, TimestampMixin):
    """Device brand (e.g., Apple, Samsung, Sony)."""
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    devices = relationship("Device", back_populates="brand")

    def __repr__(self) -> str:
        return f"<Brand {self.name}>"


class GadgetType(Base, UUIDMixin, TimestampMixin):
    """Type of gadget (e.g., Mobile, Tablet, Console)."""
    __tablename__ = "gadget_types"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    devices = relationship("Device", back_populates="gadget_type")

    def __repr__(self) -> str:
        return f"<GadgetType {self.name}>"


class Device(Base, UUIDMixin, TimestampMixin):
    """Device model - catalog of models for specific brands and types."""

    __tablename__ = "devices"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    type_id: Mapped[str] = mapped_column(ForeignKey("gadget_types.id"), nullable=False)

    model: Mapped[str] = mapped_column(String(100), nullable=False)  # iPhone 15 Pro, Galaxy S21
    model_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # A2848, SM-G991B
    colour: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Black, White, Silver
    storage: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 64 GB, 128 GB, 256 GB

    # Device-specific test configuration
    test_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    brand = relationship("Brand", back_populates="devices")
    gadget_type = relationship("GadgetType", back_populates="devices")
    jobs = relationship("Job", back_populates="device")
    test_steps = relationship("TestStep", back_populates="device")

    __table_args__ = (
        {"schema": None},
    )

    def __repr__(self) -> str:
        return f"<Device {self.model}>"
