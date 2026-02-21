"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = "technician"


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    sla_hours: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """User list response."""

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
