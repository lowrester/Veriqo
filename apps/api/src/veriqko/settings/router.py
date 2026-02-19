from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from pydantic import BaseModel
from uuid import UUID

from veriqko.db.base import get_db
from veriqko.settings.models import SystemSetting
from veriqko.dependencies import get_current_active_user
from veriqko.users.models import User, UserRole

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingResponse(BaseModel):
    key: str
    value: Any
    description: str | None = None

    class Config:
        from_attributes = True

class SettingUpdate(BaseModel):
    value: Any

@router.get("", response_model=List[SettingResponse])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all global settings (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(SystemSetting)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific setting."""
    query = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(query)
    setting = result.scalar_one_or_none()
    
    if not setting:
        # Return default if not found (or 404)
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return setting

@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    data: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update or create a setting (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(query)
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = data.value
    else:
        setting = SystemSetting(key=key, value=data.value)
        db.add(setting)

    await db.commit()
    await db.refresh(setting)
    return setting
