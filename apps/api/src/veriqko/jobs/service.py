"""Job service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import String, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from veriqko.devices.models import Device
from veriqko.jobs.models import Job, JobHistory, JobStatus
from veriqko.jobs.schemas import JobBatchCreate, JobCreate, JobUpdate
from veriqko.jobs.state_machine import JobStateMachine, TransitionResult


class JobRepository:
    """Repository for job database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, job_id: str) -> Job | None:
        """Get a job by ID with relationships."""
        stmt = (
            select(Job)
            .options(
                selectinload(Job.device).selectinload(Device.brand),
                selectinload(Job.device).selectinload(Device.gadget_type),
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
        status: JobStatus | None = None,
        technician_id: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        current_user: User | None = None,
    ) -> list[Job]:
        """List jobs with optional filtering."""
        from veriqko.enums import UserRole

        stmt = (
            select(Job)
            .options(
                selectinload(Job.device).selectinload(Device.brand),
                selectinload(Job.device).selectinload(Device.gadget_type),
                selectinload(Job.assigned_technician)
            )
            .where(Job.deleted_at.is_(None))
            .order_by(Job.created_at.desc())
        )

        # Customer filtering
        if current_user and current_user.role == UserRole.CUSTOMER:
            stmt = stmt.where(Job.customer_reference == current_user.email)

        if status:
            stmt = stmt.where(Job.status == status)

        if technician_id:
            stmt = stmt.where(Job.assigned_technician_id == technician_id)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Job.serial_number.ilike(search_term),
                    Job.batch_id.ilike(search_term),
                    Job.customer_reference.ilike(search_term),
                    Job.ticket_id.cast(String).ilike(search_term),
                )
            )

        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_next_ticket_id(self) -> int:
        """Get the next sequential ticket ID."""
        from sqlalchemy import func
        stmt = select(func.max(Job.ticket_id))
        max_id = await self.db.scalar(stmt)
        return (max_id or 10000) + 1

    async def create(self, data: JobCreate, user_id: str) -> Job:
        """Create a new job."""
        now = datetime.now(UTC)
        ticket_id = await self._get_next_ticket_id()
        from datetime import timedelta
        job = Job(
            id=str(uuid4()),
            ticket_id=ticket_id,
            device_id=data.device_id,
            serial_number=data.serial_number,
            imei=data.imei,
            customer_reference=data.customer_reference,
            batch_id=data.batch_id,
            intake_condition=data.intake_condition,
            status=JobStatus.INTAKE,
            assigned_technician_id=user_id,
            intake_started_at=now,
            sla_due_at=now + timedelta(hours=24), # Default 24h SLA
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

    async def create_batch(self, data: JobBatchCreate, user_id: str) -> list[Job]:
        """Create multiple jobs."""
        now = datetime.now(UTC)
        start_ticket_id = await self._get_next_ticket_id()
        jobs = []

        common = data.common_data or {}
        device_id = common.get("device_id")

        for i, sn in enumerate(data.serial_numbers):
            job = Job(
                id=str(uuid4()),
                ticket_id=start_ticket_id + i,
                device_id=device_id,
                serial_number=sn,
                imei=common.get("imei"),
                customer_reference=data.customer_reference or common.get("customer_reference"),
                batch_id=data.batch_id or common.get("batch_id"),
                intake_condition=common.get("intake_condition"),
                status=JobStatus.INTAKE,
                assigned_technician_id=user_id,
                intake_started_at=now,
            )
            self.db.add(job)
            jobs.append(job)

        await self.db.flush()

        # Create history entries
        for job in jobs:
            history = JobHistory(
                id=str(uuid4()),
                job_id=job.id,
                from_status=None,
                to_status=JobStatus.INTAKE,
                changed_by_id=user_id,
                changed_at=now,
                notes="Job created (Batch)",
            )
            self.db.add(history)

        await self.db.flush()
        return jobs

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
        notes: str | None = None,
        is_fully_tested: bool = True,
        skip_reason: str | None = None,
    ) -> Job | None:
        """Update job status and record history."""
        job = await self.get(job_id)
        if not job:
            return None

        now = datetime.now(UTC)
        old_status = job.status

        # Update status
        job.status = status
        job.is_fully_tested = is_fully_tested
        if skip_reason:
            job.skip_reason = skip_reason

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
            notes=notes or skip_reason,
        )
        self.db.add(history)
        await self.db.flush()

        return await self.get(job_id)

    async def get_history(self, job_id: str) -> list[JobHistory]:
        """Get job history entries."""
        stmt = (
            select(JobHistory)
            .options(selectinload(JobHistory.changed_by))
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

        job.deleted_at = datetime.now(UTC)
        await self.db.flush()
        return True


class EvidenceRepository:
    """Repository for evidence queries (used by state machine)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_job_stage(self, job_id: str, stage: JobStatus) -> list:
        """Get evidence for a specific job stage."""
        from veriqko.evidence.models import Evidence

        stmt = select(Evidence).where(
            Evidence.job_id == job_id,
            Evidence.stage == stage,
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
        status: str | None = None,
        technician_id: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        current_user: User | None = None,
    ) -> list[Job]:
        """List jobs."""

        status_enum = JobStatus(status) if status else None

        # Enforce strict customer filtering in the repository or here
        # Actually, let's update JobRepository.list to take current_user

        return await self.repo.list(
            status=status_enum,
            technician_id=technician_id,
            search=search,
            limit=limit,
            offset=offset,
            current_user=current_user
        )

    async def create(self, data: JobCreate, user_id: str) -> Job:
        """Create a new job."""
        return await self.repo.create(data, user_id)

    async def create_batch(self, data: JobBatchCreate, user_id: str) -> list[Job]:
        """Create multiple jobs."""
        return await self.repo.create_batch(data, user_id)

    async def update(self, job_id: str, data: JobUpdate) -> Job | None:
        """Update a job."""
        return await self.repo.update(job_id, data)

    async def transition(
        self,
        job_id: str,
        target_status: str,
        user_id: str,
        notes: str | None = None,
        is_fully_tested: bool = True,
        skip_reason: str | None = None,
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
            is_fully_tested=is_fully_tested,
        )

        if result.success:
            job = await self.repo.update_status(
                job_id,
                target,
                user_id,
                notes,
                is_fully_tested=is_fully_tested,
                skip_reason=skip_reason
            )

            # Auto-trigger Picea sync when moving to RESET
            if target == JobStatus.RESET:
                from veriqko.integrations.picea.service import PiceaService
                picea_service = PiceaService(self.db)
                # Fire and forget/BG task ideally, but for now we wait to ensure UI updates with fresh data
                await picea_service.sync_job_diagnostics(job_id, user_id)
                # Re-fetch job to get updated Picea fields
                job = await self.repo.get(job_id)

            # Send completion email if job is completed
            if target == JobStatus.COMPLETED:
                from veriqko.integrations.email import email_service

                customer_email = None
                if job.customer_reference and "@" in job.customer_reference:
                    customer_email = job.customer_reference

                if customer_email:
                    customer_name = "Valued Customer"
                    # Fire and forget (bg task in production)
                    await email_service.send_completion_email(
                        recipient_email=customer_email,
                        recipient_name=customer_name,
                        job_id=job.id,
                        serial_number=job.serial_number
                    )
                else:
                    # Log that no email was sent
                    import logging
                    logging.getLogger("veriqko").info(f"No customer email found in reference for job {job.id}, skipping completion email")

        return job, result

    async def get_history(self, job_id: str) -> list[JobHistory]:
        """Get job history."""
        return await self.repo.get_history(job_id)

    def get_valid_transitions(self, job: Job) -> list[str]:
        """Get valid transitions for a job."""
        transitions = self.state_machine.get_valid_transitions(job.status)
        return [t.value for t in transitions]
