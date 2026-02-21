from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# API Keys
class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = ["jobs:read"]

class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    created_at: datetime
    last_used_at: datetime | None
    is_active: bool

class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str  # Only returned once

# Webhooks
class WebhookCreate(BaseModel):
    url: str
    description: str | None = None
    events: list[str]

class WebhookResponse(BaseModel):
    id: UUID
    url: str
    description: str | None
    events: list[str]
    is_active: bool
    failure_count: int
    secret_key: str  # Returned so user can verify signatures
    created_at: datetime
