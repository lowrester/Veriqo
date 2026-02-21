"""SLA background monitoring task."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select

from veriqko.db.base import get_db
from veriqko.jobs.models import Job, JobStatus

logger = structlog.get_logger(__name__)

async def check_sla_breaches():
    """
    Check all active jobs for SLA breaches or upcoming breaches.
    Sends notifications to technicians/managers.
    """
    logger.info("Starting SLA breach check")

    async for db in get_db():
        try:
            now = datetime.now(UTC)

            # 1. Find jobs that are active and have an SLA
            stmt = select(Job).where(
                Job.status.not_in([JobStatus.COMPLETED, JobStatus.FAILED]),
                Job.sla_due_at.is_not(None),
                Job.deleted_at.is_(None)
            )

            result = await db.execute(stmt)
            jobs = result.scalars().all()

            for job in jobs:
                # Check for breach
                if job.sla_due_at < now:
                    logger.warning("SLA breached", job_id=job.id, serial_number=job.serial_number)
                    # In a real app, we'd avoid spamming by checking a 'last_notified_at' field
                    # await email_service.send_sla_alert(job, level="BREACHED")

                # Check for near breach (within 2 hours)
                elif job.sla_due_at < now + timedelta(hours=2):
                    logger.info("SLA near breach", job_id=job.id, serial_number=job.serial_number)
                    # await email_service.send_sla_alert(job, level="WARNING")

        except Exception as e:
            logger.exception("Error during SLA check", error=str(e))
        finally:
            # get_session is a generator, we break after one iteration or use it properly
            break

async def run_sla_checker():
    """Runner for the SLA checker."""
    await check_sla_breaches()
