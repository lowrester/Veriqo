from typing import Any

from pydantic import BaseModel, ConfigDict


class TestStepBase(BaseModel):
    name: str
    description: str | None = None
    station_type: str
    sequence_order: int
    is_mandatory: bool = True
    requires_evidence: bool = False
    evidence_instructions: str | None = None
    criteria: dict[str, Any] | None = None

class TestStepCreate(TestStepBase):
    device_id: str

class TestStepUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    station_type: str | None = None
    sequence_order: int | None = None
    is_mandatory: bool | None = None
    requires_evidence: bool | None = None
    evidence_instructions: str | None = None
    criteria: dict[str, Any] | None = None

class TestStepResponse(TestStepBase):
    id: str
    device_id: str
    created_at: Any = None
    updated_at: Any = None

    model_config = ConfigDict(from_attributes=True)
