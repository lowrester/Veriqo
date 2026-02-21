"""User database models."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqko.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from veriqko.enums import UserRole
from veriqko.jobs.models import JobStatus


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    sla_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Default SLA for jobs created by this user

    # Relationships
    assigned_jobs = relationship("Job", back_populates="assigned_technician", foreign_keys="Job.assigned_technician_id")
    qc_jobs = relationship("Job", back_populates="qc_technician", foreign_keys="Job.qc_technician_id")
    test_results = relationship("TestResult", back_populates="performed_by")
    evidence_items = relationship("Evidence", back_populates="captured_by")
    reports = relationship("Report", back_populates="generated_by")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
