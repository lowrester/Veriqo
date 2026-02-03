from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import Dict, Any, List
from datetime import datetime, timedelta

from veriqo.db.base import get_session
from veriqo.users.auth import get_current_user
from veriqo.jobs.models import Job, JobStatus
from veriqo.users.models import User

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/dashboard")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated statistics for the dashboard.
    """
    
    # Base query for counts
    # We'll do a single aggregation query for efficiency
    query = select(
        func.count(Job.id).label("total"),
        func.sum(case((Job.status == JobStatus.COMPLETED, 1), else_=0)).label("completed"),
        func.sum(case((Job.status == JobStatus.FAILED, 1), else_=0)).label("failed"),
        func.sum(case((Job.status.in_([
            JobStatus.INTAKE, 
            JobStatus.RESET, 
            JobStatus.FUNCTIONAL_TEST, 
            JobStatus.QC
        ]), 1), else_=0)).label("in_progress")
    )
    
    result = await session.execute(query)
    stats = result.one()
    
    # Calculate yield (Pass rate)
    total_closed = (stats.completed or 0) + (stats.failed or 0)
    yield_rate = 0
    if total_closed > 0:
        yield_rate = (stats.completed / total_closed) * 100
        
    # Get recent jobs (limit 5)
    recent_query = select(Job).order_by(Job.created_at.desc()).limit(5)
    recent_result = await session.execute(recent_query)
    recent_jobs = recent_result.scalars().all()
    
    return {
        "counts": {
            "total": stats.total or 0,
            "completed": stats.completed or 0,
            "failed": stats.failed or 0,
            "in_progress": stats.in_progress or 0
        },
        "metrics": {
            "yield_rate": round(yield_rate, 1)
        },
        "recent_activity": [
            {
                "id": str(job.id),
                "serial_number": job.serial_number,
                "status": job.status,
                "platform": job.device.platform if job.device else "Unknown",  # Assuming eager load or simple access
                "model": job.device.model if job.device else "Unknown",
                "updated_at": job.updated_at
            } for job in recent_jobs
        ]
    }

from sqlalchemy.orm import selectinload
from veriqo.stations.models import Station

@router.get("/floor")
async def get_floor_status(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get live floor status: stations with their active jobs.
    """
    # Fetch all active stations
    stations_query = select(Station).where(Station.is_active == True).order_by(Station.name)
    stations_result = await session.execute(stations_query)
    stations = stations_result.scalars().all()
    
    # Fetch all active jobs with device details
    # We fetch them effectively properly instead of relying on intricate relationship loading filtering
    jobs_query = select(Job).options(
        selectinload(Job.device)
    ).where(
        Job.status.notin_([JobStatus.COMPLETED, JobStatus.FAILED])
    )
    jobs_result = await session.execute(jobs_query)
    active_jobs = jobs_result.scalars().all()
    
    # Group jobs by station
    jobs_by_station = {}
    for job in active_jobs:
        station_id = str(job.current_station_id) if job.current_station_id else "unassigned"
        if station_id not in jobs_by_station:
            jobs_by_station[station_id] = []
        
        jobs_by_station[station_id].append({
            "id": str(job.id),
            "serial_number": job.serial_number,
            "status": job.status,
            "platform": job.device.platform if job.device else "Unknown",
            "model": job.device.model if job.device else "Unknown",
            "updated_at": job.updated_at,
            "batches": job.batch_id
        })
        
    # Build response structure
    floor_view = []
    
    # 1. Add "Intake/Unassigned" virtual column if there are strictly unassigned jobs (optional, depends on workflow)
    if "unassigned" in jobs_by_station and jobs_by_station["unassigned"]:
        floor_view.append({
            "id": "unassigned",
            "name": "Unassigned / Intake Queue",
            "type": "queue",
            "jobs": jobs_by_station["unassigned"]
        })
        
    # 2. Add actual Stations
    for station in stations:
        s_id = str(station.id)
        floor_view.append({
            "id": s_id,
            "name": station.name,
            "type": station.station_type,
            "jobs": jobs_by_station.get(s_id, [])
        })
        
    return floor_view
