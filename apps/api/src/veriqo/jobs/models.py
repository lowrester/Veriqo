"""Job database models - core workflow entity."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class JobStatus(str, Enum):
    """Job workflow status."""

    INTAKE = "intake"
    RESET = "reset"
    FUNCTIONAL = "functional"
    QC = "qc"
    COMPLETED = "completed"
    FAILED = "failed"
    ON_HOLD = "on_hold"


class TestResultStatus(str, Enum):
    """Test result status."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    PENDING = "pending"


class Job(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Job model - core workflow entity representing a device being processed."""

    __tablename__ = "jobs"

    # Device reference
    device_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("devices.id"),
        nullable=True,
    )
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Workflow state
    status: Mapped[JobStatus] = mapped_column(
        ENUM(JobStatus, name="job_status", create_type=False),
        nullable=False,
        default=JobStatus.INTAKE,
    )
    current_station_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stations.id"),
        nullable=True,
    )

    # Assignment
    assigned_technician_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Workflow timestamps
    intake_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    intake_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    functional_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    functional_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    qc_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    qc_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # QC sign-off
    qc_technician_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
    )
    qc_initials: Mapped[str | None] = mapped_column(String(10), nullable=True)
    qc_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Customer/batch reference
    batch_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    customer_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Intake condition
    intake_condition: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    device = relationship("Device", back_populates="jobs")
    current_station = relationship("Station", back_populates="jobs")
    assigned_technician = relationship("User", back_populates="assigned_jobs", foreign_keys=[assigned_technician_id])
    qc_technician = relationship("User", back_populates="qc_jobs", foreign_keys=[qc_technician_id])
    test_results = relationship("TestResult", back_populates="job", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="job", cascade="all, delete-orphan")
    history = relationship("JobHistory", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Job {self.serial_number} ({self.status})>"


class TestStep(Base, UUIDMixin, TimestampMixin):
    """Test step template - defines tests for a device type at a station."""

    __tablename__ = "test_steps"

    device_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("devices.id"),
        nullable=True,
    )
    station_type: Mapped[JobStatus] = mapped_column(
        ENUM(JobStatus, name="job_status", create_type=False),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    is_mandatory: Mapped[bool] = mapped_column(default=True)
    requires_evidence: Mapped[bool] = mapped_column(default=False)
    evidence_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    device = relationship("Device", back_populates="test_steps")
    results = relationship("TestResult", back_populates="test_step")

    def __repr__(self) -> str:
        return f"<TestStep {self.name}>"


class TestResult(Base, UUIDMixin, TimestampMixin):
    """Test result - job-specific test execution record."""

    __tablename__ = "test_results"

    job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_step_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("test_steps.id"),
        nullable=False,
    )

    status: Mapped[TestResultStatus] = mapped_column(
        ENUM(TestResultStatus, name="test_result_status", create_type=False),
        nullable=False,
        default=TestResultStatus.PENDING,
    )

    performed_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    measurements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="test_results")
    test_step = relationship("TestStep", back_populates="results")
    performed_by = relationship("User", back_populates="test_results")
    evidence_items = relationship("Evidence", back_populates="test_result")

    def __repr__(self) -> str:
        return f"<TestResult {self.test_step_id} ({self.status})>"


class JobHistory(Base, UUIDMixin):
    """Job history - audit trail for workflow state changes."""

    __tablename__ = "job_history"

    job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    from_status: Mapped[JobStatus | None] = mapped_column(
        ENUM(JobStatus, name="job_status", create_type=False),
        nullable=True,
    )
    to_status: Mapped[JobStatus] = mapped_column(
        ENUM(JobStatus, name="job_status", create_type=False),
        nullable=False,
    )

    changed_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    station_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stations.id"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="history")
    station = relationship("Station", back_populates="job_history")

    def __repr__(self) -> str:
        return f"<JobHistory {self.job_id}: {self.from_status} -> {self.to_status}>"
