from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqo.db.base import get_db
from veriqo.dependencies import get_current_user
from veriqo.jobs.models import TestStep, JobStatus
from veriqo.templates.schemas import TestStepCreate, TestStepResponse, TestStepUpdate
from veriqo.users.models import User

router = APIRouter(prefix="/admin/templates", tags=["templates"])

@router.get("", response_model=list[TestStepResponse])
async def list_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    device_id: Optional[str] = Query(None),
    station_type: Optional[str] = Query(None),
):
    """List test step templates, optionally filtered."""
    stmt = select(TestStep).order_by(TestStep.station_type, TestStep.sequence_order)
    
    if device_id:
        stmt = stmt.where(TestStep.device_id == device_id)
    if station_type:
        stmt = stmt.where(TestStep.station_type == station_type)
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=TestStepResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TestStepCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new test step template."""
    # Convert string station_type to enum if needed, though SQLAlchemy usually handles it if passed as string matching enum value
    # But let's be safe
    try:
        # Validate station_type 
        JobStatus(data.station_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid station type")

    step = TestStep(**data.model_dump())
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return step

@router.put("/{step_id}", response_model=TestStepResponse)
async def update_template(
    step_id: str,
    data: TestStepUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a test step template."""
    step = await db.get(TestStep, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Test step not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(step, field, value)

    await db.commit()
    await db.refresh(step)
    return step

@router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    step_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a test step template."""
    step = await db.get(TestStep, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Test step not found")
    
    await db.delete(step)
    await db.commit()
