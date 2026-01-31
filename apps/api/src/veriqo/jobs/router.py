"""Job router."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from veriqo.db.base import get_db
from veriqo.dependencies import get_current_user
from veriqo.jobs.schemas import (
    JobCreate,
    JobHistoryResponse,
    JobListResponse,
    JobResponse,
    JobTransition,
    JobUpdate,
    TransitionResponse,
)
from veriqo.jobs.service import JobService
from veriqo.users.models import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_to_response(job) -> JobResponse:
    """Convert job model to response schema."""
    return JobResponse(
        id=job.id,
        serial_number=job.serial_number,
        status=job.status.value,
        device={
            "id": job.device.id,
            "platform": job.device.platform,
            "model": job.device.model,
        }
        if job.device
        else None,
        assigned_technician={
            "id": job.assigned_technician.id,
            "full_name": job.assigned_technician.full_name,
            "email": job.assigned_technician.email,
        }
        if job.assigned_technician
        else None,
        current_station={
            "id": job.current_station.id,
            "name": job.current_station.name,
            "station_type": job.current_station.station_type.value,
        }
        if job.current_station
        else None,
        customer_reference=job.customer_reference,
        batch_id=job.batch_id,
        intake_condition=job.intake_condition,
        qc_initials=job.qc_initials,
        qc_notes=job.qc_notes,
        intake_started_at=job.intake_started_at,
        intake_completed_at=job.intake_completed_at,
        reset_started_at=job.reset_started_at,
        reset_completed_at=job.reset_completed_at,
        functional_started_at=job.functional_started_at,
        functional_completed_at=job.functional_completed_at,
        qc_started_at=job.qc_started_at,
        qc_completed_at=job.qc_completed_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("", response_model=list[JobListResponse])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: Optional[str] = Query(None),
    technician_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List jobs with optional filtering."""
    service = JobService(db)
    jobs = await service.list(
        status=status,
        technician_id=technician_id,
        limit=limit,
        offset=offset,
    )

    return [
        JobListResponse(
            id=job.id,
            serial_number=job.serial_number,
            status=job.status.value,
            device_platform=job.device.platform if job.device else None,
            device_model=job.device.model if job.device else None,
            assigned_technician_name=job.assigned_technician.full_name
            if job.assigned_technician
            else None,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new job (starts at INTAKE stage)."""
    service = JobService(db)
    job = await service.create(data, current_user.id)
    return _job_to_response(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a job by ID."""
    service = JobService(db)
    job = await service.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return _job_to_response(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    data: JobUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a job."""
    service = JobService(db)
    job = await service.update(job_id, data)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return _job_to_response(job)


@router.post("/{job_id}/transition", response_model=TransitionResponse)
async def transition_job(
    job_id: str,
    data: JobTransition,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Transition job to a new workflow state."""
    service = JobService(db)

    job, result = await service.transition(
        job_id=job_id,
        target_status=data.target_status,
        user_id=current_user.id,
        notes=data.notes,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Transition failed",
                "errors": result.errors,
            },
        )

    return TransitionResponse(
        job=_job_to_response(job),
        from_status=result.from_status.value,
        to_status=result.to_status.value,
        timestamp=result.timestamp,
        warnings=result.warnings,
    )


@router.get("/{job_id}/history", response_model=list[JobHistoryResponse])
async def get_job_history(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get job workflow history."""
    service = JobService(db)

    # Verify job exists
    job = await service.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    history = await service.get_history(job_id)

    return [
        JobHistoryResponse(
            id=h.id,
            from_status=h.from_status.value if h.from_status else None,
            to_status=h.to_status.value,
            changed_by_name="Unknown",  # TODO: Load user names
            changed_at=h.changed_at,
            notes=h.notes,
        )
        for h in history
    ]


@router.get("/{job_id}/valid-transitions", response_model=list[str])
async def get_valid_transitions(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get valid state transitions for a job."""
    service = JobService(db)
    job = await service.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return service.get_valid_transitions(job)
