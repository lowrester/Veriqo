"""User database models."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.jobs.models import JobStatus

# ... imports ...

class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    # ... existing columns ...
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.TECHNICIAN,
    )
    station_type: Mapped[JobStatus | None] = mapped_column(
        ENUM(JobStatus, name="job_status", create_type=False),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    assigned_jobs = relationship("Job", back_populates="assigned_technician", foreign_keys="Job.assigned_technician_id")
    qc_jobs = relationship("Job", back_populates="qc_technician", foreign_keys="Job.qc_technician_id")
    test_results = relationship("TestResult", back_populates="performed_by")
    evidence_items = relationship("Evidence", back_populates="captured_by")
    reports = relationship("Report", back_populates="generated_by")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
