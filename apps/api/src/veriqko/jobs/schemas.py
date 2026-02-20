"""Job schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class JobCreate(BaseModel):
    """Schema for creating a new job."""

    device_id: Optional[str] = None
    serial_number: str = Field(..., min_length=1, max_length=100)
    imei: Optional[str] = Field(None, max_length=100)
    customer_reference: Optional[str] = None
    batch_id: Optional[str] = None
    condition_notes: Optional[str] = None
    intake_condition: Optional[dict] = None
    brand: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    model_number: Optional[str] = None
    colour: Optional[str] = None
    storage: Optional[str] = None

    @field_validator('imei', 'customer_reference', 'batch_id', 'condition_notes',
                     'brand', 'device_type', 'model', 'model_number', 'colour', 'storage',
                     mode='before')
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == '':
            return None
        return v


class JobBatchCreate(BaseModel):
    """Schema for creating multiple jobs in one go."""

    common_data: Optional[dict] = Field(None, description="Common fields for all jobs (brand, model, etc.)")
    serial_numbers: list[str] = Field(..., min_length=1)
    batch_id: Optional[str] = None
    customer_reference: Optional[str] = None


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    serial_number: Optional[str] = Field(None, min_length=1, max_length=100)
    imei: Optional[str] = Field(None, min_length=1, max_length=100)
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
    brand: str
    device_type: str
    model: str

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    """User summary for job responses."""

    id: str
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class StationSummary(BaseModel):
    """Station summary for job responses."""

    id: str
    name: str
    station_type: str

    model_config = ConfigDict(from_attributes=True)


class TestProgressSummary(BaseModel):
    """Test progress summary."""

    total: int
    completed: int
    passed: int
    failed: int


class JobResponse(BaseModel):
    """Job response schema."""

    id: str
    ticket_id: Optional[int] = None
    serial_number: str
    status: str
    device: Optional[DeviceSummary] = None
    assigned_technician: Optional[UserSummary] = None
    current_station: Optional[StationSummary] = None

    customer_reference: Optional[str] = None
    batch_id: Optional[str] = None
    sla_due_at: Optional[datetime] = None
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

    # Picea Integration
    picea_verify_status: Optional[str] = None
    picea_mdm_locked: bool = False
    picea_erase_confirmed: bool = False
    picea_erase_certificate: Optional[str] = None
    picea_diagnostics_raw: Optional[dict] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Job list response schema."""

    id: str
    serial_number: str
    status: str
    device_brand: Optional[str] = None
    device_type: Optional[str] = None
    device_model: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    customer_reference: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class EvidenceSummary(BaseModel):
    """Evidence item summary."""
    id: str
    original_filename: str
    evidence_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TestStepResponse(BaseModel):
    """Workflow step with current result status."""
    id: str
    name: str
    description: Optional[str] = None
    sequence_order: int
    is_mandatory: bool
    requires_evidence: bool
    
    # Result info
    status: str = "pending"
    notes: Optional[str] = None
    evidence: list[EvidenceSummary] = []
    
    model_config = ConfigDict(from_attributes=True)


class TestResultCreate(BaseModel):
    """Schema for submitting a test result."""
    status: str
    notes: Optional[str] = None
