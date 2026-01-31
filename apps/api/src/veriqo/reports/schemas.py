"""Report schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReportCreate(BaseModel):
    """Schema for creating a report."""

    scope: str  # master, intake, reset, functional, qc
    variant: str = "customer"  # customer, internal


class ReportResponse(BaseModel):
    """Report response schema."""

    id: str
    job_id: str
    scope: str
    variant: str
    file_size_bytes: int
    access_token: str
    public_url: str
    expires_at: datetime
    generated_at: datetime
    version: int

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Report list response."""

    id: str
    scope: str
    variant: str
    expires_at: datetime
    generated_at: datetime
    public_url: str

    class Config:
        from_attributes = True


class PublicReportResponse(BaseModel):
    """Public report access response."""

    job_serial_number: str
    device_platform: str
    device_model: str
    status: str
    generated_at: datetime
    download_url: str
