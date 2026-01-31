"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Current user response schema."""

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
