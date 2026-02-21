"""Job schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobCreate(BaseModel):
    """Schema for creating a new job."""

    device_id: str | None = None
    serial_number: str = Field(..., min_length=1, max_length=100)
    imei: str | None = Field(None, max_length=100)
    customer_reference: str | None = None
    batch_id: str | None = None
    condition_notes: str | None = None
    intake_condition: dict | None = None
    brand: str | None = None
    device_type: str | None = None
    model: str | None = None
    model_number: str | None = None
    colour: str | None = None
    storage: str | None = None

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

    common_data: dict | None = Field(None, description="Common fields for all jobs (brand, model, etc.)")
    serial_numbers: list[str] = Field(..., min_length=1)
    batch_id: str | None = None
    customer_reference: str | None = None


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    serial_number: str | None = Field(None, min_length=1, max_length=100)
    imei: str | None = Field(None, min_length=1, max_length=100)
    customer_reference: str | None = None
    batch_id: str | None = None
    intake_condition: dict | None = None
    qc_initials: str | None = Field(None, max_length=10)
    qc_notes: str | None = None


class JobTransition(BaseModel):
    """Schema for job state transition."""

    target_status: str
    notes: str | None = None
    is_fully_tested: bool = True
    reason: str | None = None


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
    ticket_id: int | None = None
    serial_number: str
    status: str
    device: DeviceSummary | None = None
    assigned_technician: UserSummary | None = None
    current_station: StationSummary | None = None

    customer_reference: str | None = None
    batch_id: str | None = None
    sla_due_at: datetime | None = None
    intake_condition: dict | None = None

    qc_initials: str | None = None
    qc_notes: str | None = None

    # Timestamps
    intake_started_at: datetime | None = None
    intake_completed_at: datetime | None = None
    reset_started_at: datetime | None = None
    reset_completed_at: datetime | None = None
    functional_started_at: datetime | None = None
    functional_completed_at: datetime | None = None
    qc_started_at: datetime | None = None
    qc_completed_at: datetime | None = None
    completed_at: datetime | None = None

    # Picea Integration
    picea_verify_status: str | None = None
    picea_mdm_locked: bool = False
    picea_erase_confirmed: bool = False
    picea_erase_certificate: str | None = None
    picea_diagnostics_raw: dict | None = None

    # Overrides
    is_fully_tested: bool = True
    skip_reason: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Job list response schema."""

    id: str
    serial_number: str
    status: str
    device_brand: str | None = None
    device_type: str | None = None
    device_model: str | None = None
    assigned_technician_name: str | None = None
    customer_reference: str | None = None
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
    from_status: str | None
    to_status: str
    changed_by_name: str
    changed_at: datetime
    notes: str | None = None

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
    description: str | None = None
    sequence_order: int
    is_mandatory: bool
    requires_evidence: bool

    # Result info
    status: str = "pending"
    notes: str | None = None
    evidence: list[EvidenceSummary] = []

    model_config = ConfigDict(from_attributes=True)


class TestResultCreate(BaseModel):
    """Schema for submitting a test result."""
    status: str
    notes: str | None = None
