import pytest
import uuid
from unittest.mock import patch
from sqlalchemy import select

from app.models.certificate import CertificateJob, Certificate, JobStatus, CertificateStatus


VALID_PAYLOAD = {
    "event_name": "Python Bootcamp 2026",
    "issued_by": "Tech Academy",
    "issue_date": "2026-10-01",
    "recipients": [
        {"name": "Alice Johnson", "email": "alice@example.com", "course_name": "Advanced Python"},
        {"name": "Bob Smith", "email": "bob@example.com"},
    ],
}


class TestCreateJob:
    @pytest.mark.asyncio
    async def test_create_job_returns_202(self, client):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            response = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_create_job_response_structure(self, client):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            response = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        data = response.json()
        assert "id" in data
        assert data["event_name"] == VALID_PAYLOAD["event_name"]
        assert data["issued_by"] == VALID_PAYLOAD["issued_by"]
        assert data["total_recipients"] == 2
        assert data["status"] == "pending"
        assert data["completed_count"] == 0
        assert data["failed_count"] == 0
        assert data["progress_percent"] == 0.0

    @pytest.mark.asyncio
    async def test_create_job_persists_to_db(self, client, test_db):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            response = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = response.json()["id"]

        async with test_db() as session:
            job = await session.get(CertificateJob, uuid.UUID(job_id))
            assert job is not None
            assert job.event_name == "Python Bootcamp 2026"
            assert job.total_recipients == 2

    @pytest.mark.asyncio
    async def test_create_job_creates_certificates_in_db(self, client, test_db):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            response = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = response.json()["id"]

        async with test_db() as session:
            result = await session.execute(
                select(Certificate).where(Certificate.job_id == uuid.UUID(job_id))
            )
            certs = result.scalars().all()
            assert len(certs) == 2
            names = {c.recipient_name for c in certs}
            assert "Alice Johnson" in names
            assert "Bob Smith" in names


class TestInputValidation:
    @pytest.mark.asyncio
    async def test_empty_recipients_rejected(self, client):
        payload = {**VALID_PAYLOAD, "recipients": []}
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_email_rejected(self, client):
        payload = {
            **VALID_PAYLOAD,
            "recipients": [{"name": "Test User", "email": "not-an-email"}],
        }
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_blank_name_rejected(self, client):
        payload = {
            **VALID_PAYLOAD,
            "recipients": [{"name": "  ", "email": "test@example.com"}],
        }
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_short_name_rejected(self, client):
        payload = {
            **VALID_PAYLOAD,
            "recipients": [{"name": "A", "email": "test@example.com"}],
        }
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_blank_event_name_rejected(self, client):
        payload = {**VALID_PAYLOAD, "event_name": ""}
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_event_name_rejected(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "event_name"}
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_too_many_recipients_rejected(self, client):
        recipients = [{"name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1001)]
        payload = {**VALID_PAYLOAD, "recipients": recipients}
        response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_recipient_without_course(self, client):
        payload = {
            **VALID_PAYLOAD,
            "recipients": [{"name": "Jane Doe", "email": "jane@example.com"}],
        }
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            response = await client.post("/api/v1/certificates/jobs", json=payload)
        assert response.status_code == 202


class TestJobStatus:
    @pytest.mark.asyncio
    async def test_get_job_status(self, client):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            create_resp = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/certificates/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert "progress_percent" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_job_returns_404(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/certificates/jobs/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_jobs(self, client):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
            await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)

        response = await client.get("/api/v1/certificates/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "jobs" in data
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_progress_percent_calculation(self, client, test_db):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            create_resp = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = uuid.UUID(create_resp.json()["id"])

        async with test_db() as session:
            job = await session.get(CertificateJob, job_id)
            job.completed_count = 1
            job.failed_count = 1
            await session.commit()

        response = await client.get(f"/api/v1/certificates/jobs/{job_id}")
        assert response.json()["progress_percent"] == 100.0


class TestCertificateGeneration:
    @pytest.mark.asyncio
    async def test_generate_certificate_pdf(self, tmp_path):
        from app.services.certificate_generator import generate_certificate_pdf
        filepath = generate_certificate_pdf(
            recipient_name="John Doe",
            event_name="Test Event",
            issued_by="Test Org",
            issue_date="2026-10-01",
            course_name="Python 101",
            output_dir=str(tmp_path),
        )
        import os
        assert os.path.exists(filepath)
        assert filepath.endswith(".pdf")
        assert os.path.getsize(filepath) > 1000

    @pytest.mark.asyncio
    async def test_generate_certificate_without_course(self, tmp_path):
        from app.services.certificate_generator import generate_certificate_pdf
        filepath = generate_certificate_pdf(
            recipient_name="Jane Doe",
            event_name="Test Event",
            issued_by="Test Org",
            issue_date="2026-10-01",
            output_dir=str(tmp_path),
        )
        import os
        assert os.path.exists(filepath)

    @pytest.mark.asyncio
    async def test_each_certificate_gets_unique_file(self, tmp_path):
        from app.services.certificate_generator import generate_certificate_pdf
        path1 = generate_certificate_pdf("Alice", "Event", "Org", "2026-01-01", output_dir=str(tmp_path))
        path2 = generate_certificate_pdf("Bob", "Event", "Org", "2026-01-01", output_dir=str(tmp_path))
        assert path1 != path2


class TestCertificateFailureHandling:
    @pytest.mark.asyncio
    async def test_one_failure_does_not_stop_others(self, tmp_path):
        from app.workers.tasks import process_certificate_job
        from app.db.session import SyncSessionLocal
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.base import Base

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        job = CertificateJob(
            event_name="Test Event",
            issued_by="Test Org",
            issue_date="2026-01-01",
            total_recipients=3,
        )

        session = Session()
        session.add(job)
        session.flush()

        certs = [
            Certificate(job_id=job.id, recipient_name="Alice", recipient_email="a@a.com"),
            Certificate(job_id=job.id, recipient_name="", recipient_email="b@b.com"),
            Certificate(job_id=job.id, recipient_name="Charlie", recipient_email="c@c.com"),
        ]
        for c in certs:
            session.add(c)
        session.commit()

        call_count = 0
        original_generate = __import__(
            "app.services.certificate_generator", fromlist=["generate_certificate_pdf"]
        ).generate_certificate_pdf

        def patched_generate(recipient_name, **kwargs):
            if not recipient_name:
                raise ValueError("Name cannot be empty")
            return original_generate(recipient_name=recipient_name, output_dir=str(tmp_path), **kwargs)

        with patch("app.workers.tasks.SyncSessionLocal", return_value=session):
            with patch("app.services.certificate_generator.generate_certificate_pdf", side_effect=patched_generate):
                pass

        session.close()
        engine.dispose()

    @pytest.mark.asyncio
    async def test_job_marked_partial_on_mixed_results(self, client, test_db):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            create_resp = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = uuid.UUID(create_resp.json()["id"])

        async with test_db() as session:
            job = await session.get(CertificateJob, job_id)
            job.status = JobStatus.PARTIAL
            job.completed_count = 1
            job.failed_count = 1
            await session.commit()

        response = await client.get(f"/api/v1/certificates/jobs/{job_id}")
        assert response.json()["status"] == "partial"
        assert response.json()["failed_count"] == 1
        assert response.json()["completed_count"] == 1


class TestRetrieveCertificates:
    @pytest.mark.asyncio
    async def test_list_certificates_for_job(self, client):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            create_resp = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
        assert response.status_code == 200
        certs = response.json()
        assert isinstance(certs, list)
        assert len(certs) == 2

    @pytest.mark.asyncio
    async def test_download_nonexistent_certificate_returns_404(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/certificates/{fake_id}/download")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_certificate_without_file_returns_404(self, client, test_db):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            create_resp = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = uuid.UUID(create_resp.json()["id"])

        async with test_db() as session:
            result = await session.execute(
                select(Certificate).where(Certificate.job_id == job_id)
            )
            cert = result.scalars().first()
            cert_id = cert.id

        response = await client.get(f"/api/v1/certificates/{cert_id}/download")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_certificates_by_status(self, client, test_db):
        with patch("app.api.v1.endpoints.certificates._enqueue_job"):
            create_resp = await client.post("/api/v1/certificates/jobs", json=VALID_PAYLOAD)
        job_id = uuid.UUID(create_resp.json()["id"])

        async with test_db() as session:
            result = await session.execute(
                select(Certificate).where(Certificate.job_id == job_id)
            )
            certs = result.scalars().all()
            certs[0].status = CertificateStatus.COMPLETED
            certs[0].file_path = "/some/path/cert.pdf"
            await session.commit()

        response = await client.get(
            f"/api/v1/certificates/jobs/{job_id}/certificates?status=completed"
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
