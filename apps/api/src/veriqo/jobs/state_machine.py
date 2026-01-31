"""Job workflow state machine."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from veriqo.jobs.models import JobStatus


@dataclass
class TransitionContext:
    """Context for state transition."""

    job_id: str
    current_status: JobStatus
    target_status: JobStatus
    user_id: str
    notes: Optional[str] = None


@dataclass
class TransitionResult:
    """Result of a state transition."""

    success: bool
    from_status: JobStatus
    to_status: Optional[JobStatus]
    timestamp: datetime
    warnings: list[str]
    errors: list[str]


# Type aliases
Guard = Callable[[TransitionContext, "JobRepository"], tuple[bool, Optional[str]]]


class JobStateMachine:
    """
    Finite State Machine for job workflow.

    Workflow: INTAKE -> RESET -> FUNCTIONAL -> QC -> COMPLETED

    Any state can transition to FAILED or ON_HOLD.
    ON_HOLD can return to any active state.
    QC can send back to FUNCTIONAL.
    """

    # Define valid transitions
    TRANSITIONS: dict[JobStatus, list[JobStatus]] = {
        JobStatus.INTAKE: [JobStatus.RESET, JobStatus.FAILED, JobStatus.ON_HOLD],
        JobStatus.RESET: [JobStatus.FUNCTIONAL, JobStatus.FAILED, JobStatus.ON_HOLD],
        JobStatus.FUNCTIONAL: [JobStatus.QC, JobStatus.FAILED, JobStatus.ON_HOLD],
        JobStatus.QC: [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.ON_HOLD,
            JobStatus.FUNCTIONAL,  # QC can send back
        ],
        JobStatus.ON_HOLD: [
            JobStatus.INTAKE,
            JobStatus.RESET,
            JobStatus.FUNCTIONAL,
            JobStatus.QC,
        ],
        JobStatus.COMPLETED: [],  # Terminal
        JobStatus.FAILED: [],  # Terminal
    }

    def __init__(self, job_repo: "JobRepository", evidence_repo: "EvidenceRepository"):
        self.job_repo = job_repo
        self.evidence_repo = evidence_repo

    def can_transition(
        self,
        current_status: JobStatus,
        target_status: JobStatus,
    ) -> tuple[bool, list[str]]:
        """Check if transition is valid."""
        valid_targets = self.TRANSITIONS.get(current_status, [])

        if target_status not in valid_targets:
            return False, [
                f"Cannot transition from {current_status.value} to {target_status.value}"
            ]

        return True, []

    def get_valid_transitions(self, current_status: JobStatus) -> list[JobStatus]:
        """Get list of valid target states from current state."""
        return self.TRANSITIONS.get(current_status, [])

    async def transition(
        self,
        job_id: str,
        current_status: JobStatus,
        target_status: JobStatus,
        user_id: str,
        notes: Optional[str] = None,
        force: bool = False,
    ) -> TransitionResult:
        """Execute a state transition."""
        timestamp = datetime.now(timezone.utc)
        errors = []
        warnings = []

        # Validate transition
        if not force:
            can_transit, validation_errors = self.can_transition(current_status, target_status)
            if not can_transit:
                return TransitionResult(
                    success=False,
                    from_status=current_status,
                    to_status=None,
                    timestamp=timestamp,
                    warnings=[],
                    errors=validation_errors,
                )

        # Run transition-specific guards
        if not force:
            guard_errors = await self._run_guards(job_id, current_status, target_status, user_id)
            if guard_errors:
                return TransitionResult(
                    success=False,
                    from_status=current_status,
                    to_status=None,
                    timestamp=timestamp,
                    warnings=[],
                    errors=guard_errors,
                )

        return TransitionResult(
            success=True,
            from_status=current_status,
            to_status=target_status,
            timestamp=timestamp,
            warnings=warnings,
            errors=[],
        )

    async def _run_guards(
        self,
        job_id: str,
        current_status: JobStatus,
        target_status: JobStatus,
        user_id: str,
    ) -> list[str]:
        """Run transition-specific validation guards."""
        errors = []

        # INTAKE -> RESET: Require intake condition
        if current_status == JobStatus.INTAKE and target_status == JobStatus.RESET:
            job = await self.job_repo.get(job_id)
            if not job.intake_condition:
                errors.append("Intake condition assessment must be completed")

        # RESET -> FUNCTIONAL: Require reset evidence
        elif current_status == JobStatus.RESET and target_status == JobStatus.FUNCTIONAL:
            evidence = await self.evidence_repo.get_for_job_stage(job_id, JobStatus.RESET)
            if not evidence:
                errors.append("Factory reset evidence (photo/video) is required")

        # QC -> COMPLETED: Require QC sign-off
        elif current_status == JobStatus.QC and target_status == JobStatus.COMPLETED:
            job = await self.job_repo.get(job_id)
            if not job.qc_initials or not job.qc_technician_id:
                errors.append("QC sign-off is required before completion")

        return errors

    def get_timestamp_field(self, status: JobStatus, is_start: bool = True) -> str:
        """Get the timestamp field name for a status."""
        suffix = "started_at" if is_start else "completed_at"

        if status == JobStatus.INTAKE:
            return f"intake_{suffix}"
        elif status == JobStatus.RESET:
            return f"reset_{suffix}"
        elif status == JobStatus.FUNCTIONAL:
            return f"functional_{suffix}"
        elif status == JobStatus.QC:
            return f"qc_{suffix}"
        elif status == JobStatus.COMPLETED:
            return "completed_at"

        return None
