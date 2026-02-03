from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# API Keys
class ApiKeyCreate(BaseModel):
    name: str
    scopes: List[str] = ["jobs:read"]

class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str  # Only returned once

# Webhooks
class WebhookCreate(BaseModel):
    url: str
    description: Optional[str] = None
    events: List[str]

class WebhookResponse(BaseModel):
    id: UUID
    url: str
    description: Optional[str]
    events: List[str]
    is_active: bool
    failure_count: int
    secret_key: str  # Returned so user can verify signatures
    created_at: datetime
