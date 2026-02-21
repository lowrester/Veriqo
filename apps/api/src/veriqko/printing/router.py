from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_active_user
from veriqko.printing.models import LabelTemplate
from veriqko.users.models import User, UserRole

router = APIRouter(prefix="/printing", tags=["printing"])

# --- Schemas ---
class LabelTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    zpl_code: str
    dimensions: str | None = None
    is_default: bool = False

class LabelTemplateResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    zpl_code: str
    dimensions: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/templates", response_model=list[LabelTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all label templates."""
    query = select(LabelTemplate).order_by(LabelTemplate.name)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/templates", response_model=LabelTemplateResponse)
async def create_template(
    template: LabelTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new label template (Admin only)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_template = LabelTemplate(**template.model_dump())
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    return db_template

@router.get("/templates/{template_id}", response_model=LabelTemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific template."""
    template = await db.get(LabelTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/templates/{template_id}", response_model=LabelTemplateResponse)
async def update_template(
    template_id: UUID,
    data: LabelTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a label template (Admin only)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not authorized")

    template = await db.get(LabelTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # If setting as default, unset others first
    if data.is_default:
        from sqlalchemy import update
        await db.execute(
            update(LabelTemplate).where(LabelTemplate.id != template_id).values(is_default=False)
        )

    for field, value in data.model_dump().items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template

@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a label template (Admin only)."""
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    template = await db.get(LabelTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()
    return None
