"""Job schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Schema for creating a new job."""

    device_id: Optional[str] = None
    serial_number: str = Field(..., min_length=1, max_length=100)
    customer_reference: Optional[str] = None
    batch_id: Optional[str] = None
    intake_condition: Optional[dict] = None


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    serial_number: Optional[str] = Field(None, min_length=1, max_length=100)
    customer_reference: Optional[str] = None
    batch_id: Optional[str] = None
    intake_condition: Optional[dict] = None
    qc_initials: Optional[str] = Field(None, max_length=10)
    qc_notes: Optional[str] = None


class JobTransition(BaseModel):
    """Schema for job state transition."""

    target_status: str
    notes: Optional[str] = None


class DeviceSummary(BaseModel):
    """Device summary for job responses."""

    id: str
    platform: str
    model: str

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """User summary for job responses."""

    id: str
    full_name: str
    email: str

    class Config:
        from_attributes = True


class StationSummary(BaseModel):
    """Station summary for job responses."""

    id: str
    name: str
    station_type: str

    class Config:
        from_attributes = True


class TestProgressSummary(BaseModel):
    """Test progress summary."""

    total: int
    completed: int
    passed: int
    failed: int


class JobResponse(BaseModel):
    """Job response schema."""

    id: str
    serial_number: str
    status: str
    device: Optional[DeviceSummary] = None
    assigned_technician: Optional[UserSummary] = None
    current_station: Optional[StationSummary] = None

    customer_reference: Optional[str] = None
    batch_id: Optional[str] = None
    intake_condition: Optional[dict] = None

    qc_initials: Optional[str] = None
    qc_notes: Optional[str] = None

    # Timestamps
    intake_started_at: Optional[datetime] = None
    intake_completed_at: Optional[datetime] = None
    reset_started_at: Optional[datetime] = None
    reset_completed_at: Optional[datetime] = None
    functional_started_at: Optional[datetime] = None
    functional_completed_at: Optional[datetime] = None
    qc_started_at: Optional[datetime] = None
    qc_completed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Job list response schema."""

    id: str
    serial_number: str
    status: str
    device_platform: Optional[str] = None
    device_model: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransitionResponse(BaseModel):
    """Response after job transition."""

    job: JobResponse
    from_status: str
    to_status: str
    timestamp: datetime
    warnings: list[str] = []


class JobHistoryResponse(BaseModel):
    """Job history entry response."""

    id: str
    from_status: Optional[str]
    to_status: str
    changed_by_name: str
    changed_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
