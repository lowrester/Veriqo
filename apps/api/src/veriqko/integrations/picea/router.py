from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_user
from veriqko.integrations.picea.service import PiceaService
from veriqko.users.models import User

router = APIRouter(prefix="/picea", tags=["integrations", "picea"])

@router.post("/sync/{job_id}", status_code=status.HTTP_200_OK)
async def sync_diagnostics(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger a manual sync of diagnostics data from Picea for a given Job.
    """
    service = PiceaService(db)
    success = await service.sync_job_diagnostics(job_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to sync diagnostics from Picea. Ensure device identifier is correct and Picea API is reachable."
        )

    return {"message": "Diagnostics synchronized successfully."}


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def picea_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint for Picea to push results.
    Expected payload contains device identifiers (serial/imei).
    """
    # 1. Extract identifier
    # Picea behavior: payload often has 'serialNumber' or 'imei'
    serial_number = payload.get("serialNumber") or payload.get("serial_number")
    imei = payload.get("imei")

    if not serial_number and not imei:
        # We can't identify the job, but we return 200 to acknowledge webhook
        return {"status": "ignored", "reason": "missing_identifier"}

    # 2. Find the job
    from veriqko.jobs.models import Job
    stmt = select(Job).where(
        or_(
            Job.serial_number == serial_number,
            Job.imei == imei
        ),
        Job.deleted_at.is_(None)
    ).order_by(Job.created_at.desc())

    job = (await db.execute(stmt)).scalar_one_or_none()

    if not job:
        return {"status": "ignored", "reason": "job_not_found"}

    # 3. Trigger sync
    # We use a system user ID or similar if needed for history
    # For now, we'll try to sync without a specific user ID if possible,
    # or use a placeholder "system_webhook"
    service = PiceaService(db)
    await service.sync_job_diagnostics(job.id, performed_by_id="system_webhook")

    return {"status": "processed", "job_id": job.id}
