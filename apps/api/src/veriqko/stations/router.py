from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

# Placeholder schemas (defining inline simple ones if no schemas.py)
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_user
from veriqko.jobs.models import Job, JobStatus
from veriqko.stations.models import Station
from veriqko.users.models import User, UserRole


class StationBase(BaseModel):
    name: str
    station_type: str
    is_active: bool = True
    capabilities: list = []

class StationCreate(StationBase):
    pass

class StationResponse(StationBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

router = APIRouter(prefix="/stations", tags=["stations"])

@router.get("", response_model=list[StationResponse])
async def list_stations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all stations."""
    stmt = select(Station)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    data: StationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new station (Admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        JobStatus(data.station_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid station type")

    station = Station(**data.model_dump())
    db.add(station)
    await db.commit()
    await db.refresh(station)
    return station

@router.get("/{station_id}/queue")
async def get_station_queue(
    station_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get active jobs in station queue."""
    station = await db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    stmt = select(Job).where(
        and_(
            Job.current_station_id == station_id,
            Job.status.notin_([JobStatus.COMPLETED, JobStatus.FAILED])
        )
    ).order_by(Job.updated_at)

    result = await db.execute(stmt)
    return result.scalars().all()
