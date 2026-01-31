"""Report database models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.db.base import Base, UUIDMixin


class ReportScope(str, Enum):
    """Report scope - which part of the workflow to report on."""

    MASTER = "master"
    INTAKE = "intake"
    RESET = "reset"
    FUNCTIONAL = "functional"
    QC = "qc"


class ReportVariant(str, Enum):
    """Report variant - customer-facing or internal."""

    CUSTOMER = "customer"
    INTERNAL = "internal"


class Report(Base, UUIDMixin):
    """Report model - generated PDF reports with public access."""

    __tablename__ = "reports"

    job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report type
    scope: Mapped[ReportScope] = mapped_column(
        ENUM(ReportScope, name="report_scope", create_type=False),
        nullable=False,
    )
    variant: Mapped[ReportVariant] = mapped_column(
        ENUM(ReportVariant, name="report_variant", create_type=False),
        nullable=False,
    )

    # Generated file
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Public access token
    access_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Generation metadata
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Created timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="reports")
    generated_by = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report {self.job_id} ({self.scope}/{self.variant})>"
