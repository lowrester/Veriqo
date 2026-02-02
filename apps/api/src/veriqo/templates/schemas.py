from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class TestStepBase(BaseModel):
    name: str
    description: Optional[str] = None
    station_type: str
    sequence_order: int
    is_mandatory: bool = True
    requires_evidence: bool = False
    evidence_instructions: Optional[str] = None
    criteria: Optional[dict[str, Any]] = None

class TestStepCreate(TestStepBase):
    device_id: str

class TestStepUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    station_type: Optional[str] = None
    sequence_order: Optional[int] = None
    is_mandatory: Optional[bool] = None
    requires_evidence: Optional[bool] = None
    evidence_instructions: Optional[str] = None
    criteria: Optional[dict[str, Any]] = None

class TestStepResponse(TestStepBase):
    id: str
    device_id: str
    created_at: Any = None
    updated_at: Any = None

    model_config = ConfigDict(from_attributes=True)
