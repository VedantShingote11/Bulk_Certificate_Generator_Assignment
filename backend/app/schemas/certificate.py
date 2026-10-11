import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.certificate import JobStatus, CertificateStatus


class RecipientInput(BaseModel):
    name: str
    email: EmailStr
    course_name: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Recipient name cannot be blank")
        if len(v) < 2:
            raise ValueError("Recipient name must be at least 2 characters")
        if len(v) > 255:
            raise ValueError("Recipient name must be under 255 characters")
        return v

    @field_validator("course_name")
    @classmethod
    def course_name_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) > 255:
                raise ValueError("Course name must be under 255 characters")
        return v


class JobCreateRequest(BaseModel):
    event_name: str
    issued_by: str
    issue_date: str
    recipients: list[RecipientInput]

    @field_validator("event_name")
    @classmethod
    def event_name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Event name cannot be blank")
        return v

    @field_validator("issued_by")
    @classmethod
    def issued_by_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Issued by cannot be blank")
        return v

    @field_validator("issue_date")
    @classmethod
    def issue_date_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Issue date cannot be blank")
        return v

    @model_validator(mode="after")
    def recipients_not_empty(self) -> "JobCreateRequest":
        if not self.recipients:
            raise ValueError("At least one recipient is required")
        if len(self.recipients) > 1000:
            raise ValueError("Maximum 1000 recipients per job")
        return self


class CertificateResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    recipient_name: str
    recipient_email: str
    course_name: Optional[str]
    status: CertificateStatus
    file_url: Optional[str] = None
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: uuid.UUID
    event_name: str
    issued_by: str
    issue_date: str
    status: JobStatus
    total_recipients: int
    completed_count: int
    failed_count: int
    progress_percent: float = 0.0
    created_at: datetime
    updated_at: datetime
    certificates: Optional[list[CertificateResponse]] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_job(cls, job, include_certificates: bool = False, base_url: str = "") -> "JobResponse":
        processed = job.completed_count + job.failed_count
        progress = (processed / job.total_recipients * 100) if job.total_recipients > 0 else 0.0

        certs = None
        if include_certificates and job.certificates:
            certs = [
                CertificateResponse(
                    **{k: v for k, v in cert.__dict__.items() if not k.startswith("_")},
                    file_url=f"{base_url}/static/certificates/{cert.file_path.split('/')[-1]}" if cert.file_path else None,
                )
                for cert in job.certificates
            ]

        return cls(
            id=job.id,
            event_name=job.event_name,
            issued_by=job.issued_by,
            issue_date=job.issue_date,
            status=job.status,
            total_recipients=job.total_recipients,
            completed_count=job.completed_count,
            failed_count=job.failed_count,
            progress_percent=round(progress, 2),
            created_at=job.created_at,
            updated_at=job.updated_at,
            certificates=certs,
        )


class JobListResponse(BaseModel):
    total: int
    jobs: list[JobResponse]
