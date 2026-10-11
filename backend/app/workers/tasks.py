import uuid
import logging

from app.workers.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.models.certificate import CertificateJob, Certificate, JobStatus, CertificateStatus
from app.services.certificate_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="workers.process_certificate_job", max_retries=0)
def process_certificate_job(self, job_id: str) -> dict:
    db = SyncSessionLocal()
    try:
        job = db.query(CertificateJob).filter(CertificateJob.id == uuid.UUID(job_id)).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"status": "error", "message": "Job not found"}

        job.status = JobStatus.PROCESSING
        db.commit()

        certificates = db.query(Certificate).filter(Certificate.job_id == job.id).all()

        for cert in certificates:
            cert.status = CertificateStatus.GENERATING
            db.commit()

            try:
                filepath = generate_certificate_pdf(
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    issued_by=job.issued_by,
                    issue_date=job.issue_date,
                    course_name=cert.course_name or "",
                )

                cert.status = CertificateStatus.COMPLETED
                cert.file_path = filepath
                job.completed_count += 1
                logger.info(f"Generated certificate for {cert.recipient_name} (job {job_id})")

            except Exception as exc:
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(exc)
                job.failed_count += 1
                logger.error(f"Failed to generate certificate for {cert.recipient_name}: {exc}")

            db.commit()

        if job.failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif job.completed_count == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PARTIAL

        db.commit()
        return {"status": job.status.value, "job_id": job_id}

    except Exception as exc:
        logger.exception(f"Unexpected error processing job {job_id}: {exc}")
        if db:
            job = db.query(CertificateJob).filter(CertificateJob.id == uuid.UUID(job_id)).first()
            if job:
                job.status = JobStatus.FAILED
                db.commit()
        raise

    finally:
        db.close()
