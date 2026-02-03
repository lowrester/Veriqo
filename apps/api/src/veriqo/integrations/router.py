from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from veriqo.db.base import get_session
from veriqo.auth.dependencies import get_current_user
from veriqo.users.models import User
from veriqo.integrations.service import IntegrationService
from veriqo.integrations.schemas import (
    ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse,
    WebhookCreate, WebhookResponse
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = IntegrationService(session)
    api_key, raw_key = await service.create_api_key(data.name, data.scopes, current_user.id)
    
    # Convert to Pydantic
    response = ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        raw_key=raw_key
    )
    return response

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = IntegrationService(session)
    keys = await service.list_api_keys()
    return keys

@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = IntegrationService(session)
    webhook = await service.create_webhook(data.url, data.events, current_user.id)
    return webhook

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = IntegrationService(session)
    hooks = await service.list_webhooks()
    return hooks
