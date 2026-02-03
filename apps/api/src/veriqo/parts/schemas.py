from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PartBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    quantity_on_hand: int = Field(0, ge=0)

class PartCreate(PartBase):
    pass

class PartUpdate(PartBase):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity_on_hand: Optional[int] = Field(None, ge=0)

class PartResponse(PartBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PartUsageCreate(BaseModel):
    part_id: str
    quantity: int = Field(..., gt=0)

class PartUsageResponse(BaseModel):
    id: str
    job_id: str
    part_id: str
    quantity: int
    synced_at: Optional[datetime]
    created_at: datetime
    part: PartResponse

    class Config:
        from_attributes = True
