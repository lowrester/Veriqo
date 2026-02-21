from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PartBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    quantity_on_hand: int = Field(0, ge=0)

class PartCreate(PartBase):
    pass

class PartUpdate(PartBase):
    sku: str | None = Field(None, min_length=1, max_length=100)
    name: str | None = Field(None, min_length=1, max_length=255)
    quantity_on_hand: int | None = Field(None, ge=0)

class PartResponse(PartBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PartUsageCreate(BaseModel):
    part_id: str
    quantity: int = Field(..., gt=0)

class PartUsageResponse(BaseModel):
    id: str
    job_id: str
    part_id: str
    quantity: int
    synced_at: datetime | None
    created_at: datetime
    part: PartResponse

    model_config = ConfigDict(from_attributes=True)
