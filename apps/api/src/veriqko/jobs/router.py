"""Job router."""

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_user
from veriqko.jobs.schemas import (
    JobBatchCreate,
    JobCreate,
    JobHistoryResponse,
    JobListResponse,
    JobResponse,
    JobTransition,
    JobUpdate,
    TransitionResponse,
    TestStepResponse,
    TestResultCreate,
    EvidenceSummary,
)
from veriqko.jobs.service import JobService
from veriqko.users.models import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_to_response(job) -> JobResponse:
    """Convert job model to response schema."""
    return JobResponse(
        id=job.id,
        ticket_id=job.ticket_id,
        serial_number=job.serial_number,
        imei=job.imei,
        status=job.status.value,
        device={
            "id": job.device.id,
            "brand": job.device.brand.name,
            "device_type": job.device.gadget_type.name,
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
        # Picea
        picea_verify_status=job.picea_verify_status,
        picea_mdm_locked=job.picea_mdm_locked,
        picea_erase_confirmed=job.picea_erase_confirmed,
        picea_erase_certificate=job.picea_erase_certificate,
        picea_diagnostics_raw=job.picea_diagnostics_raw,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("", response_model=list[JobListResponse])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: Optional[str] = Query(None),
    technician_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List jobs with optional filtering."""
    service = JobService(db)
    jobs = await service.list(
        status=status,
        technician_id=technician_id,
        search=search,
        limit=limit,
        offset=offset,
    )

    return [
        JobListResponse(
            id=job.id,
            serial_number=job.serial_number,
            status=job.status.value,
            device_brand=job.device.brand.name if job.device else None,
            device_type=job.device.gadget_type.name if job.device else None,
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


@router.post("/batch", response_model=list[JobResponse], status_code=status.HTTP_201_CREATED)
async def create_jobs_batch(
    data: JobBatchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create multiple jobs at once."""
    service = JobService(db)
    jobs = await service.create_batch(data, current_user.id)
    return [_job_to_response(job) for job in jobs]


@router.get("/security/check-imei/{imei}")
async def check_imei_security(
    imei: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Check if an IMEI is blacklisted."""
    from veriqko.jobs.security import check_imei_blacklist
    is_blacklisted, reason = await check_imei_blacklist(imei)
    return {"is_blacklisted": is_blacklisted, "reason": reason}


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
            changed_by_name=h.changed_by.full_name if h.changed_by else "Unknown",
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


@router.get("/{job_id}/steps", response_model=list[TestStepResponse])
async def get_job_steps(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get workflow steps with current status for the job."""
    # Logic:
    # 1. Get Job -> get current_station_id (or status to infer station type)
    # 2. Get TestSteps for device_id + station_type
    # 3. Get TestResults for job_id
    # 4. Merge
    
    # Ideally this logic belongs in Service, but implementing here for brevity/speed as per constraints
    from veriqko.jobs.models import Job, TestStep, TestResult, JobStatus
    
    # Get Job with session.get but we need relationships
    stmt = (
        select(Job)
        .options(
            selectinload(Job.device).selectinload(Device.brand),
            selectinload(Job.device).selectinload(Device.gadget_type)
        )
        .where(Job.id == job_id, Job.deleted_at.is_(None))
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Determine station type from job status (INTAKE, RESET, FUNCTIONAL, QC)
    # Mapping job status to station type enum
    current_stage = job.status
    
    # If job is completed or failed, we show the steps from the last station (QC)
    # or expose all steps. For now, matching the active stations.
    if current_stage in [JobStatus.COMPLETED, JobStatus.FAILED]:
        # Show QC steps for completed/failed as it's the final verification point
        display_stage = JobStatus.QC
    else:
        display_stage = current_stage
        
    if display_stage not in [JobStatus.INTAKE, JobStatus.RESET, JobStatus.FUNCTIONAL, JobStatus.QC]:
        return []

    # Get Steps
    stmt = select(TestStep).where(
        TestStep.device_id == job.device_id,
        TestStep.station_type == display_stage
    ).order_by(TestStep.sequence_order)
    steps = (await db.execute(stmt)).scalars().all()
    
    stmt_results = (
        select(TestResult)
        .options(selectinload(TestResult.evidence_items))
        .where(TestResult.job_id == job_id)
    )
    results = (await db.execute(stmt_results)).scalars().all()
    results_map = {r.test_step_id: r for r in results}
    
    # Build response
    response = []
    for step in steps:
        result = results_map.get(step.id)
        
        evidence_list = []
        if result:
            evidence_list = [
                EvidenceSummary(
                    id=ev.id,
                    original_filename=ev.original_filename,
                    evidence_type=ev.evidence_type.value,
                    created_at=ev.created_at
                ) for ev in result.evidence_items
            ]

        response.append(TestStepResponse(
            id=step.id,
            name=step.name,
            description=step.description,
            sequence_order=step.sequence_order,
            is_mandatory=step.is_mandatory,
            requires_evidence=step.requires_evidence,
            status=result.status.value if result else "pending",
            notes=result.notes if result else None,
            evidence=evidence_list
        ))
        
    return response


@router.post("/{job_id}/results/{step_id}", status_code=status.HTTP_200_OK)
async def submit_step_result(
    job_id: str,
    step_id: str,
    data: TestResultCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Submit a test result."""
    from veriqko.jobs.models import TestResult, TestResultStatus
    from datetime import datetime
    
    # Check if result exists
    stmt = select(TestResult).where(
        TestResult.job_id == job_id,
        TestResult.test_step_id == step_id
    )
    result = (await db.execute(stmt)).scalar_one_or_none()
    
    if result:
        result.status = TestResultStatus(data.status)
        result.notes = data.notes
        result.performed_at = datetime.now(timezone.utc)
        result.performed_by_id = current_user.id
    else:
        result = TestResult(
            job_id=job_id,
            test_step_id=step_id,
            status=TestResultStatus(data.status),
            performed_by_id=current_user.id,
            performed_at=datetime.now(timezone.utc),
            notes=data.notes
        )
        db.add(result)
        
    await db.commit()
    return {"status": "success"}
