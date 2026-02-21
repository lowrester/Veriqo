from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_user
from veriqko.devices.models import Device
from veriqko.jobs.models import Job, JobStatus, TestResult, TestResultStatus, TestStep
from veriqko.users.models import User

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/dashboard")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
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
            JobStatus.FUNCTIONAL,
            JobStatus.QC
        ]), 1), else_=0)).label("in_progress")
    ).where(Job.deleted_at.is_(None))

    result = await session.execute(query)
    stats = result.one()

    # Calculate yield (Pass rate)
    total_closed = (stats.completed or 0) + (stats.failed or 0)
    yield_rate = 0
    if total_closed > 0:
        yield_rate = (stats.completed / total_closed) * 100

    # Get recent jobs (limit 5)
    recent_query = (
        select(Job)
        .options(
            selectinload(Job.device).selectinload(Device.brand),
            selectinload(Job.device).selectinload(Device.gadget_type)
        )
        .where(Job.deleted_at.is_(None))
        .order_by(Job.created_at.desc())
        .limit(5)
    )
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
                "brand": job.device.brand.name if job.device and job.device.brand else "Unknown",
                "device_type": job.device.gadget_type.name if job.device and job.device.gadget_type else "Unknown",
                "model": job.device.model if job.device else "Unknown",
                "updated_at": job.updated_at,
                "sla_status": _get_sla_status(job.sla_due_at)
            } for job in recent_jobs
        ]
    }

def _get_sla_status(due_at: datetime | None) -> str:
    if not due_at:
        return "none"

    now = datetime.now(UTC)

    # Ensure due_at is timezone-aware if it's not
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=UTC)

    diff = due_at - now
    hours = diff.total_seconds() / 3600

    if hours < 0:
        return "critical" # Overdue
    if hours < 4:
        return "warning" # Less than 4h
    return "healthy"


from veriqko.stations.models import Station


@router.get("/floor")
async def get_floor_status(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
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
        selectinload(Job.device).selectinload(Device.brand),
        selectinload(Job.device).selectinload(Device.gadget_type)
    ).where(
        and_(
            Job.status.notin_([JobStatus.COMPLETED, JobStatus.FAILED]),
            Job.deleted_at.is_(None)
        )
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
            "brand": job.device.brand.name if job.device and job.device.brand else "Unknown",
            "device_type": job.device.gadget_type.name if job.device and job.device.gadget_type else "Unknown",
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

@router.get("/defects")
async def get_defect_heatmap(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """
    Get defect heatmap aggregated by Device Model and Test Step.
    Returns list of { model, test_step, count }.
    """
    # Query: Count failed TestResults grouped by Job->Device->Model and TestStep->Name
    query = (
        select(
            Device.model,
            TestStep.name.label("test_step"),
            func.count(TestResult.id).label("failure_count")
        )
        .select_from(TestResult)
        .join(TestResult.job)
        .join(Job.device)
        .join(TestResult.test_step)
        .where(
            and_(
                TestResult.status == TestResultStatus.FAIL,
                Job.deleted_at.is_(None)
            )
        )
        .group_by(Device.model, TestStep.name)
        .order_by(func.count(TestResult.id).desc())
        .limit(100)
    )

    result = await session.execute(query)
    rows = result.all()

    return [
        {
            "model": row.model,
            "test_step": row.test_step,
            "count": row.failure_count
        } for row in rows
    ]

@router.get("/technicians")
async def get_technician_leaderboard(
    days: int = 7,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """
    Get technician efficiency leaderboard for the last N days.
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Query: Jobs completed per assigned technician in period
    query = (
        select(
            User.full_name,
            func.count(Job.id).label("jobs_completed")
        )
        .select_from(Job)
        .join(Job.assigned_technician)
        .where(
            and_(
                Job.status == JobStatus.COMPLETED,
                Job.completed_at >= cutoff,
                Job.deleted_at.is_(None)
            )
        )
        .group_by(User.id, User.full_name)
        .order_by(func.count(Job.id).desc())
        .limit(10)
    )

    result = await session.execute(query)
    rows = result.all()

    return [
        {
            "name": row.full_name,
            "jobs_completed": row.jobs_completed
        } for row in rows
    ]
