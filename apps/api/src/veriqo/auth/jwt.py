"""JWT token handling."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel

from veriqo.config import get_settings


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # User ID
    email: str
    role: str
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create a new access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, email: str, role: str) -> str:
    """Create a new refresh token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(user_id: str, email: str, role: str) -> TokenPair:
    """Create access and refresh token pair."""
    settings = get_settings()

    return TokenPair(
        access_token=create_access_token(user_id, email, role),
        refresh_token=create_refresh_token(user_id, email, role),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT token."""
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> TokenPayload | None:
    """Verify a token is valid and of the correct type."""
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.type != token_type:
        return None

    return payload
