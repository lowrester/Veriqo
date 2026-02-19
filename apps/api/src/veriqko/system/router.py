from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from veriqko.system.service import system_service, SystemVersion, UpdateStatus
from veriqko.dependencies import get_current_active_user
from veriqko.users.models import User
from veriqko.enums import UserRole

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/version", response_model=SystemVersion)
async def get_system_version(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current system version and check for updates."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return await system_service.check_for_updates()

@router.post("/update")
async def trigger_system_update(
    current_user: Annotated[User, Depends(get_current_active_user)],
    target_version: str = "main"
):
    """Trigger a system update to the specified version."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update the system")
        
    system_service.trigger_update(target_version)
    return {"message": "Update initiated. Check status for progress."}

@router.get("/status", response_model=UpdateStatus)
async def get_update_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get the status of the ongoing update."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return await system_service.get_update_status()
