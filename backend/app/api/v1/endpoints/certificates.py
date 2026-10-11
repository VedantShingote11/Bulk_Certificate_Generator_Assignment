import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.certificate import CertificateJob, Certificate, JobStatus
from app.schemas.certificate import (
    JobCreateRequest,
    JobResponse,
    JobListResponse,
    CertificateResponse,
)
from app.core.config import settings

router = APIRouter()


def _enqueue_job(job_id: str):
    from app.workers.tasks import process_certificate_job
    process_certificate_job.delay(job_id)


@router.post("/jobs", response_model=JobResponse, status_code=202)
async def create_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job = CertificateJob(
        event_name=payload.event_name,
        issued_by=payload.issued_by,
        issue_date=payload.issue_date,
        total_recipients=len(payload.recipients),
    )
    db.add(job)
    await db.flush()

    for recipient in payload.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            course_name=recipient.course_name,
        )
        db.add(cert)

    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_enqueue_job, str(job.id))

    return JobResponse.from_job(job, include_certificates=False, base_url=settings.BASE_URL)


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count(CertificateJob.id)))
    total = count_result.scalar()

    result = await db.execute(
        select(CertificateJob).order_by(CertificateJob.created_at.desc()).offset(skip).limit(limit)
    )
    jobs = result.scalars().all()

    return JobListResponse(
        total=total,
        jobs=[JobResponse.from_job(j, base_url=settings.BASE_URL) for j in jobs],
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CertificateJob).where(CertificateJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.from_job(job, include_certificates=False, base_url=settings.BASE_URL)


@router.get("/jobs/{job_id}/certificates", response_model=list[CertificateResponse])
async def list_job_certificates(
    job_id: uuid.UUID,
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    job_check = await db.execute(select(CertificateJob.id).where(CertificateJob.id == job_id))
    if not job_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    query = select(Certificate).where(Certificate.job_id == job_id)
    if status:
        query = query.where(Certificate.status == status)

    result = await db.execute(query.order_by(Certificate.created_at))
    certs = result.scalars().all()

    return [
        CertificateResponse(
            **{k: v for k, v in cert.__dict__.items() if not k.startswith("_")},
            file_url=f"{settings.BASE_URL}/static/certificates/{cert.file_path.split('/')[-1]}" if cert.file_path else None,
        )
        for cert in certs
    ]


@router.get("/{certificate_id}/download")
async def download_certificate(certificate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Certificate).where(Certificate.id == certificate_id))
    cert = result.scalar_one_or_none()

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not cert.file_path:
        raise HTTPException(status_code=404, detail="Certificate file not yet generated")

    from pathlib import Path
    from app.services.certificate_generator import BACKEND_ROOT

    stored = Path(cert.file_path)
    abs_path = stored if stored.is_absolute() else BACKEND_ROOT / stored

    if not abs_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Certificate file missing on server (looked at: {abs_path})"
        )

    filename = f"certificate_{cert.recipient_name.replace(' ', '_')}.pdf"
    return FileResponse(str(abs_path), media_type="application/pdf", filename=filename)

