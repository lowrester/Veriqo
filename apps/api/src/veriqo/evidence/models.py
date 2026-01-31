"""Evidence database models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veriqo.db.base import Base, UUIDMixin


class EvidenceType(str, Enum):
    """Evidence file type."""

    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"


class Evidence(Base, UUIDMixin):
    """Evidence model - photos/videos with integrity verification."""

    __tablename__ = "evidence"

    # Links
    job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_result_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("test_results.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # File metadata
    evidence_type: Mapped[EvidenceType] = mapped_column(
        ENUM(EvidenceType, name="evidence_type", create_type=False),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Integrity verification
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Capture metadata
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    captured_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Optional metadata
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Created timestamp (evidence is immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Supersession (instead of delete)
    superseded_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("evidence.id"),
        nullable=True,
    )
    superseded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    job = relationship("Job", back_populates="evidence_items")
    test_result = relationship("TestResult", back_populates="evidence_items")
    captured_by = relationship("User", back_populates="evidence_items")
    superseded_by = relationship("Evidence", remote_side="Evidence.id")

    def __repr__(self) -> str:
        return f"<Evidence {self.original_filename} ({self.evidence_type})>"
