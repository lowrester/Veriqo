"""Evidence router."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqo.config import get_settings
from veriqo.db.base import get_db
from veriqo.dependencies import get_current_user
from veriqo.evidence.models import Evidence, EvidenceType
from veriqo.evidence.schemas import EvidenceListResponse, EvidenceResponse, EvidenceUploadResponse
from veriqo.evidence.storage import get_storage
from veriqo.jobs.models import Job
from veriqo.users.models import User

router = APIRouter(prefix="/jobs/{job_id}/evidence", tags=["evidence"])


def _get_evidence_type(mime_type: str) -> EvidenceType:
    """Determine evidence type from MIME type."""
    if mime_type.startswith("image/"):
        return EvidenceType.PHOTO
    elif mime_type.startswith("video/"):
        return EvidenceType.VIDEO
    else:
        return EvidenceType.DOCUMENT


@router.get("", response_model=list[EvidenceListResponse])
async def list_evidence(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all evidence for a job."""
    # Verify job exists
    job_stmt = select(Job).where(Job.id == job_id, Job.deleted_at.is_(None))
    job_result = await db.execute(job_stmt)
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Get evidence
    stmt = (
        select(Evidence)
        .where(Evidence.job_id == job_id, Evidence.superseded_at.is_(None))
        .order_by(Evidence.captured_at.desc())
    )
    result = await db.execute(stmt)
    evidence_list = result.scalars().all()

    settings = get_settings()

    return [
        EvidenceListResponse(
            id=e.id,
            evidence_type=e.evidence_type.value,
            original_filename=e.original_filename,
            file_size_bytes=e.file_size_bytes,
            captured_at=e.captured_at,
            thumbnail_url=f"{settings.base_url}/api/v1/evidence/{e.id}/thumbnail"
            if e.evidence_type == EvidenceType.PHOTO
            else None,
        )
        for e in evidence_list
    ]


@router.post("", response_model=EvidenceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    job_id: str,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Upload evidence for a job."""
    # Verify job exists
    job_stmt = select(Job).where(Job.id == job_id, Job.deleted_at.is_(None))
    job_result = await db.execute(job_stmt)
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Validate content type
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content type is required",
        )

    # Save file
    storage = get_storage()
    try:
        stored = await storage.save(
            file=file.file,
            job_id=job_id,
            filename=file.filename or "unknown",
            mime_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create evidence record
    now = datetime.now(timezone.utc)
    evidence = Evidence(
        id=str(uuid4()),
        job_id=job_id,
        evidence_type=_get_evidence_type(file.content_type),
        original_filename=file.filename or "unknown",
        stored_filename=stored.stored_filename,
        file_path=stored.relative_path,
        file_size_bytes=stored.size_bytes,
        mime_type=file.content_type,
        sha256_hash=stored.sha256_hash,
        captured_at=now,
        captured_by_id=current_user.id,
        created_at=now,
    )
    db.add(evidence)
    await db.flush()

    return EvidenceUploadResponse(
        id=evidence.id,
        job_id=evidence.job_id,
        evidence_type=evidence.evidence_type.value,
        original_filename=evidence.original_filename,
        file_size_bytes=evidence.file_size_bytes,
        sha256_hash=evidence.sha256_hash,
        captured_at=evidence.captured_at,
        created_at=evidence.created_at,
    )


# Separate router for evidence access by ID (not nested under jobs)
evidence_router = APIRouter(prefix="/evidence", tags=["evidence"])


@evidence_router.get("/{evidence_id}")
async def get_evidence(
    evidence_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get evidence metadata."""
    stmt = select(Evidence).where(Evidence.id == evidence_id)
    result = await db.execute(stmt)
    evidence = result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    settings = get_settings()

    return EvidenceResponse(
        id=evidence.id,
        job_id=evidence.job_id,
        test_result_id=evidence.test_result_id,
        evidence_type=evidence.evidence_type.value,
        original_filename=evidence.original_filename,
        file_size_bytes=evidence.file_size_bytes,
        mime_type=evidence.mime_type,
        sha256_hash=evidence.sha256_hash,
        captured_at=evidence.captured_at,
        captured_by_name="Unknown",  # TODO: Load user
        caption=evidence.caption,
        download_url=f"{settings.base_url}/api/v1/evidence/{evidence.id}/download",
    )


@evidence_router.get("/{evidence_id}/download")
async def download_evidence(
    evidence_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Download evidence file."""
    stmt = select(Evidence).where(Evidence.id == evidence_id)
    result = await db.execute(stmt)
    evidence = result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    storage = get_storage()
    file_path = await storage.get_path(evidence.file_path)

    if not await storage.exists(evidence.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found",
        )

    return FileResponse(
        path=file_path,
        filename=evidence.original_filename,
        media_type=evidence.mime_type,
    )
