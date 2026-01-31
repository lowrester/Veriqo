"""User database models."""

from enum import Enum

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class UserRole(str, Enum):
    """User roles for access control."""

    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=False),
        nullable=False,
        default=UserRole.TECHNICIAN,
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
