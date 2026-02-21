from datetime import UTC, datetime
from uuid import uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.config import get_settings
from veriqko.integrations.picea.client import PiceaClient
from veriqko.jobs.models import Job, TestResult, TestResultStatus, TestStep

logger = structlog.get_logger(__name__)

class PiceaService:
    """Service to handle Picea Diagnostics synchronization logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.client = PiceaClient(self.settings)

    async def sync_job_diagnostics(self, job_id: str, performed_by_id: str) -> bool:
        """
        Fetch diagnostics from Picea and update Job test results.
        Performed by ID is the user triggering the sync.
        """
        # 1. Fetch Job
        job_result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if not job:
            return False

        # 2. Call Picea API
        picea_data = await self.client.get_test_results(
            serial_number=job.serial_number,
            imei=job.imei
        )
        if not picea_data:
            return False

        # 3. Update Job-level Picea metadata
        # Structure depends on Picea API - assuming common fields based on analysis
        job.picea_diagnostics_raw = picea_data

        # Extract Verify status
        job.picea_verify_status = picea_data.get("verifyStatus") or picea_data.get("verify_status")

        # Extract MDM status
        # Picea often returns MDM locked as a boolean or a specific test result
        picea_mdm = picea_data.get("mdmLocked") or picea_data.get("mdm_locked")
        if picea_mdm is not None:
            job.picea_mdm_locked = bool(picea_mdm)

        # Extract Erase status & Certificate
        # Look for Erase result in tests or top-level fields
        erase_data = picea_data.get("erase") or {}
        picea_erase = erase_data.get("status") == "passed" or picea_data.get("erase_confirmed", False)

        # If not in top-level, search in tests list
        tests = picea_data.get("tests", [])
        if not tests and isinstance(picea_data, list):
            tests = picea_data

        if not picea_erase:
            for test in tests:
                # Look for tests related to Data Erase
                t_name = str(test.get("name", "")).lower()
                if "erase" in t_name or "data removal" in t_name:
                    if test.get("status", "").lower() in ["pass", "passed", "ok"]:
                        picea_erase = True
                        break

        job.picea_erase_confirmed = picea_erase
        job.picea_erase_certificate = erase_data.get("certificate_url") or picea_data.get("erase_certificate")

        # 4. Map Picea data to TestResults
        for picea_test in tests:
            name = picea_test.get("name")
            picea_status = picea_test.get("status", "").lower()
            notes = picea_test.get("notes") or picea_test.get("description")

            # Map Picea status to Veriqko status
            status = TestResultStatus.PENDING
            if picea_status in ["pass", "passed", "ok", "success"]:
                status = TestResultStatus.PASS
            elif picea_status in ["fail", "failed", "error", "bad"]:
                status = TestResultStatus.FAIL
            elif picea_status in ["skip", "skipped", "n/a"]:
                status = TestResultStatus.SKIP

            # Find matching TestStep for this device type
            step_result = await self.session.execute(
                select(TestStep).where(
                    TestStep.device_id == job.device_id,
                    TestStep.name == name
                )
            )
            step = step_result.scalar_one_or_none()

            if step:
                await self._upsert_test_result(
                    job_id=job.id,
                    step_id=step.id,
                    status=status,
                    notes=notes,
                    performed_by_id=performed_by_id
                )
            else:
                logger.warning(
                    "Unknown Picea test step ignored",
                    test_name=name,
                    job_id=job.id,
                    serial_number=job.serial_number
                )

        await self.session.commit()
        return True

    async def _upsert_test_result(
        self,
        job_id: str,
        step_id: str,
        status: TestResultStatus,
        notes: str | None,
        performed_by_id: str
    ):
        """Helper to update existing result or create new one."""
        # Check if result exists
        existing_result = await self.session.execute(
            select(TestResult).where(
                TestResult.job_id == job_id,
                TestResult.test_step_id == step_id
            )
        )
        test_result = existing_result.scalar_one_or_none()

        now = datetime.now(UTC)
        if test_result:
            test_result.status = status
            test_result.notes = f"(Picea Sync) {notes}" if notes else "(Picea Sync)"
            test_result.performed_by_id = performed_by_id
            test_result.performed_at = now
            test_result.updated_at = now
        else:
            test_result = TestResult(
                id=str(uuid4()),
                job_id=job_id,
                test_step_id=step_id,
                status=status,
                notes=f"(Picea Sync) {notes}" if notes else "(Picea Sync)",
                performed_by_id=performed_by_id,
                performed_at=now,
                created_at=now,
                updated_at=now
            )
            self.session.add(test_result)
