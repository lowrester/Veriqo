"""Job service."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from veriqo.jobs.models import Job, JobHistory, JobStatus
from veriqo.jobs.schemas import JobCreate, JobUpdate
from veriqo.jobs.state_machine import JobStateMachine, TransitionResult


class JobRepository:
    """Repository for job database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, job_id: str) -> Job | None:
        """Get a job by ID with relationships."""
        stmt = (
            select(Job)
            .options(
                selectinload(Job.device),
                selectinload(Job.assigned_technician),
                selectinload(Job.current_station),
                selectinload(Job.qc_technician),
            )
            .where(Job.id == job_id, Job.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        status: Optional[JobStatus] = None,
        technician_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs with optional filtering."""
        stmt = (
            select(Job)
            .options(selectinload(Job.device), selectinload(Job.assigned_technician))
            .where(Job.deleted_at.is_(None))
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if status:
            stmt = stmt.where(Job.status == status)

        if technician_id:
            stmt = stmt.where(Job.assigned_technician_id == technician_id)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: JobCreate, user_id: str) -> Job:
        """Create a new job."""
        now = datetime.now(timezone.utc)
        job = Job(
            id=str(uuid4()),
            device_id=data.device_id,
            serial_number=data.serial_number,
            customer_reference=data.customer_reference,
            batch_id=data.batch_id,
            intake_condition=data.intake_condition,
            status=JobStatus.INTAKE,
            assigned_technician_id=user_id,
            intake_started_at=now,
        )
        self.db.add(job)
        await self.db.flush()

        # Create initial history entry
        history = JobHistory(
            id=str(uuid4()),
            job_id=job.id,
            from_status=None,
            to_status=JobStatus.INTAKE,
            changed_by_id=user_id,
            changed_at=now,
            notes="Job created",
        )
        self.db.add(history)
        await self.db.flush()

        return await self.get(job.id)

    async def update(self, job_id: str, data: JobUpdate) -> Job | None:
        """Update a job."""
        job = await self.get(job_id)
        if not job:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        await self.db.flush()
        return await self.get(job_id)

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        user_id: str,
        notes: Optional[str] = None,
    ) -> Job | None:
        """Update job status and record history."""
        job = await self.get(job_id)
        if not job:
            return None

        now = datetime.now(timezone.utc)
        old_status = job.status

        # Update status
        job.status = status

        # Update relevant timestamp
        if status == JobStatus.RESET:
            job.intake_completed_at = now
            job.reset_started_at = now
        elif status == JobStatus.FUNCTIONAL:
            job.reset_completed_at = now
            job.functional_started_at = now
        elif status == JobStatus.QC:
            job.functional_completed_at = now
            job.qc_started_at = now
        elif status == JobStatus.COMPLETED:
            job.qc_completed_at = now
            job.completed_at = now

        # Create history entry
        history = JobHistory(
            id=str(uuid4()),
            job_id=job_id,
            from_status=old_status,
            to_status=status,
            changed_by_id=user_id,
            changed_at=now,
            notes=notes,
        )
        self.db.add(history)
        await self.db.flush()

        return await self.get(job_id)

    async def get_history(self, job_id: str) -> list[JobHistory]:
        """Get job history entries."""
        stmt = (
            select(JobHistory)
            .where(JobHistory.job_id == job_id)
            .order_by(JobHistory.changed_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, job_id: str) -> bool:
        """Soft delete a job."""
        job = await self.get(job_id)
        if not job:
            return False

        job.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True


class EvidenceRepository:
    """Repository for evidence queries (used by state machine)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_job_stage(self, job_id: str, stage: JobStatus) -> list:
        """Get evidence for a specific job stage."""
        from veriqo.evidence.models import Evidence

        stmt = select(Evidence).where(
            Evidence.job_id == job_id,
            Evidence.superseded_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class JobService:
    """Job service for business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JobRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.state_machine = JobStateMachine(self.repo, self.evidence_repo)

    async def get(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        return await self.repo.get(job_id)

    async def list(
        self,
        status: Optional[str] = None,
        technician_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs."""
        status_enum = JobStatus(status) if status else None
        return await self.repo.list(
            status=status_enum,
            technician_id=technician_id,
            limit=limit,
            offset=offset,
        )

    async def create(self, data: JobCreate, user_id: str) -> Job:
        """Create a new job."""
        return await self.repo.create(data, user_id)

    async def update(self, job_id: str, data: JobUpdate) -> Job | None:
        """Update a job."""
        return await self.repo.update(job_id, data)

    async def transition(
        self,
        job_id: str,
        target_status: str,
        user_id: str,
        notes: Optional[str] = None,
    ) -> tuple[Job | None, TransitionResult]:
        """Transition job to a new status."""
        job = await self.repo.get(job_id)
        if not job:
            return None, None

        target = JobStatus(target_status)

        result = await self.state_machine.transition(
            job_id=job_id,
            current_status=job.status,
            target_status=target,
            user_id=user_id,
            notes=notes,
        )

        if result.success:
            job = await self.repo.update_status(job_id, target, user_id, notes)

        return job, result

    async def get_history(self, job_id: str) -> list[JobHistory]:
        """Get job history."""
        return await self.repo.get_history(job_id)

    def get_valid_transitions(self, job: Job) -> list[str]:
        """Get valid transitions for a job."""
        transitions = self.state_machine.get_valid_transitions(job.status)
        return [t.value for t in transitions]
