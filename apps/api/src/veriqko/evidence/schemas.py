"""Evidence schemas."""

from datetime import datetime

from pydantic import BaseModel


class EvidenceUploadResponse(BaseModel):
    """Response after uploading evidence."""

    id: str
    job_id: str
    evidence_type: str
    original_filename: str
    file_size_bytes: int
    sha256_hash: str
    captured_at: datetime
    created_at: datetime


class EvidenceResponse(BaseModel):
    """Evidence response schema."""

    id: str
    job_id: str
    test_result_id: str | None = None
    evidence_type: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    captured_at: datetime
    captured_by_name: str
    caption: str | None = None
    download_url: str

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    """Evidence list response."""

    id: str
    evidence_type: str
    original_filename: str
    file_size_bytes: int
    captured_at: datetime
    thumbnail_url: str | None = None

    class Config:
        from_attributes = True
