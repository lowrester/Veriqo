"""Device database models."""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.db.base import Base, TimestampMixin, UUIDMixin


class Device(Base, UUIDMixin, TimestampMixin):
    """Device model - catalog of console types."""

    __tablename__ = "devices"

    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # playstation, xbox, switch
    model: Mapped[str] = mapped_column(String(100), nullable=False)  # PS5 Digital, Xbox Series X
    model_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # CFI-1015A

    # Device-specific test configuration
    test_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    jobs = relationship("Job", back_populates="device")
    test_steps = relationship("TestStep", back_populates="device")

    __table_args__ = (
        {"schema": None},
    )

    def __repr__(self) -> str:
        return f"<Device {self.platform} {self.model}>"
