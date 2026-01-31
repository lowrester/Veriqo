"""Reports router."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from veriqo.config import get_settings
from veriqo.db.base import get_db
from veriqo.dependencies import get_current_user
from veriqo.jobs.models import Job, TestResult
from veriqo.reports.generator import ReportData, TestResultData, get_report_generator
from veriqo.reports.models import Report, ReportScope, ReportVariant
from veriqo.reports.qr import generate_access_token
from veriqo.reports.schemas import ReportCreate, ReportListResponse, ReportResponse
from veriqo.users.models import User

router = APIRouter(prefix="/jobs/{job_id}/reports", tags=["reports"])


@router.get("", response_model=list[ReportListResponse])
async def list_reports(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all reports for a job."""
    settings = get_settings()

    stmt = (
        select(Report)
        .where(Report.job_id == job_id)
        .order_by(Report.generated_at.desc())
    )
    result = await db.execute(stmt)
    reports = result.scalars().all()

    return [
        ReportListResponse(
            id=r.id,
            scope=r.scope.value,
            variant=r.variant.value,
            expires_at=r.expires_at,
            generated_at=r.generated_at,
            public_url=f"{settings.base_url}/r/{r.access_token}",
        )
        for r in reports
    ]


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    job_id: str,
    data: ReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Generate a new report for a job."""
    settings = get_settings()

    # Get job with relationships
    stmt = (
        select(Job)
        .options(
            selectinload(Job.device),
            selectinload(Job.assigned_technician),
            selectinload(Job.qc_technician),
            selectinload(Job.test_results).selectinload(TestResult.test_step),
        )
        .where(Job.id == job_id, Job.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Validate scope and variant
    try:
        scope = ReportScope(data.scope)
        variant = ReportVariant(data.variant)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scope or variant",
        )

    # Generate access token
    access_token = generate_access_token()
    public_url = f"{settings.base_url}/r/{access_token}"

    # Prepare report data
    test_results = []
    passed = 0
    failed = 0

    for tr in job.test_results:
        test_results.append(
            TestResultData(
                name=tr.test_step.name if tr.test_step else "Unknown",
                status=tr.status.value,
                notes=tr.notes,
            )
        )
        if tr.status.value == "pass":
            passed += 1
        elif tr.status.value == "fail":
            failed += 1

    report_data = ReportData(
        job_id=job.id,
        serial_number=job.serial_number,
        device_platform=job.device.platform if job.device else "Unknown",
        device_model=job.device.model if job.device else "Unknown",
        intake_date=job.intake_started_at or job.created_at,
        completion_date=job.completed_at,
        technician_name=job.assigned_technician.full_name if job.assigned_technician else "Unknown",
        qc_technician_name=job.qc_technician.full_name if job.qc_technician else None,
        qc_initials=job.qc_initials,
        test_results=test_results,
        total_tests=len(test_results),
        passed_tests=passed,
        failed_tests=failed,
        scope=scope.value,
        variant=variant.value,
        access_token=access_token,
        public_url=public_url,
    )

    # Generate PDF
    generator = get_report_generator()
    now = datetime.now(timezone.utc)

    output_dir = settings.storage_base_path / "reports" / str(now.year) / f"{now.month:02d}" / job_id
    output_path = output_dir / f"{uuid4()}.pdf"

    await generator.generate(report_data, output_path)

    # Calculate expiration
    expires_at = now + timedelta(days=settings.report_expiry_days)

    # Get version
    version_stmt = select(Report).where(
        Report.job_id == job_id,
        Report.scope == scope,
        Report.variant == variant,
    )
    version_result = await db.execute(version_stmt)
    existing_reports = version_result.scalars().all()
    version = len(existing_reports) + 1

    # Create report record
    report = Report(
        id=str(uuid4()),
        job_id=job_id,
        scope=scope,
        variant=variant,
        file_path=str(output_path.relative_to(settings.storage_base_path)),
        file_size_bytes=output_path.stat().st_size,
        access_token=access_token,
        expires_at=expires_at,
        generated_at=now,
        generated_by_id=current_user.id,
        version=version,
        created_at=now,
    )
    db.add(report)
    await db.flush()

    return ReportResponse(
        id=report.id,
        job_id=report.job_id,
        scope=report.scope.value,
        variant=report.variant.value,
        file_size_bytes=report.file_size_bytes,
        access_token=report.access_token,
        public_url=public_url,
        expires_at=report.expires_at,
        generated_at=report.generated_at,
        version=report.version,
    )


# Public report access router (no auth required)
public_router = APIRouter(tags=["public"])


@public_router.get("/r/{token}")
async def get_public_report(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Access a report via public token."""
    settings = get_settings()

    stmt = (
        select(Report)
        .options(selectinload(Report.job).selectinload(Job.device))
        .where(Report.access_token == token)
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Check expiration
    if report.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Report has expired",
        )

    # Return PDF file
    file_path = settings.storage_base_path / report.file_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )

    return FileResponse(
        path=file_path,
        filename=f"report_{report.job.serial_number}_{report.scope.value}.pdf",
        media_type="application/pdf",
    )
