from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from veriqko.db.base import get_db
from veriqko.parts.models import Part, PartUsage
from veriqko.parts.schemas import PartResponse, PartCreate, PartUsageCreate, PartUsageResponse
from veriqko.jobs.models import Job
from veriqko.integrations.erp_mock import erp_service
from datetime import datetime

router = APIRouter(prefix="/parts", tags=["parts"])

@router.get("", response_model=List[PartResponse])
async def list_parts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Part).order_by(Part.name))
    return result.scalars().all()

@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
async def create_part(part_in: PartCreate, db: AsyncSession = Depends(get_db)):
    # Check if SKU exists
    existing = await db.execute(select(Part).where(Part.sku == part_in.sku))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    part = Part(**part_in.model_dump())
    db.add(part)
    await db.commit()
    await db.refresh(part)
    return part

@router.post("/use", response_model=PartUsageResponse)
async def use_part(
    usage_in: PartUsageCreate, 
    job_id: str, 
    db: AsyncSession = Depends(get_db)
):
    # Verify Job
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Verify Part and Stock
    part = await db.get(Part, usage_in.part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    if part.quantity_on_hand < usage_in.quantity:
         raise HTTPException(status_code=400, detail="Insufficient stock")

    # Deduct stock
    part.quantity_on_hand -= usage_in.quantity
    
    # Create Usage Record
    usage = PartUsage(
        job_id=job_id,
        part_id=usage_in.part_id,
        quantity=usage_in.quantity
    )
    
    # Try to sync with ERP
    try:
        if await erp_service.sync_part_usage(part.sku, usage_in.quantity, job_id):
            usage.synced_at = datetime.utcnow()
    except Exception as e:
        # Don't fail the request if sync fails, just log it. 
        # In real app we would have a retry worker.
        pass

    db.add(usage)
    
    await db.commit()
    await db.refresh(usage)
    await db.refresh(part) # To return updated state if needed, though usage returns part object
    
    return usage

@router.get("/job/{job_id}", response_model=List[PartUsageResponse])
async def get_job_parts(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PartUsage)
        .where(PartUsage.job_id == job_id)
        .order_by(PartUsage.created_at)
        .options(select(PartUsage).joinedload(PartUsage.part))
    )
    return result.scalars().all()
