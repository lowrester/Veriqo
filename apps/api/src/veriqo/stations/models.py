"""Station database models."""

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from veriqo.jobs.models import JobStatus


class Station(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Station model - physical workstation configuration."""

    __tablename__ = "stations"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    station_type: Mapped[JobStatus] = mapped_column(
        ENUM(JobStatus, name="job_status", create_type=False),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Station capabilities
    capabilities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Relationships
    jobs = relationship("Job", back_populates="current_station")
    job_history = relationship("JobHistory", back_populates="station")

    def __repr__(self) -> str:
        return f"<Station {self.name} ({self.station_type})>"
