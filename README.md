# CertForge — Bulk Certificate Generator

A production-ready full-stack application for generating PDF certificates in bulk. Submit a single API request with hundreds of recipients and get personalized, professionally designed PDF certificates for each one.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Running the Application](#running-the-application)
6. [Running Tests](#running-tests)
7. [API Reference](#api-reference)
8. [Design Decisions](#design-decisions)
9. [Certificate Template](#certificate-template)
10. [Error Handling Strategy](#error-handling-strategy)

---

## Architecture Overview

```
┌─────────────────┐     HTTP      ┌──────────────────┐     Celery Task    ┌────────────────────┐
│   React Frontend│ ──────────▶  │  FastAPI Backend  │ ──────────────▶   │   Celery Worker    │
│   (Vite + RQ)   │              │  (Async API)      │                    │  (Background Jobs) │
└─────────────────┘              └──────────┬────────┘                    └─────────┬──────────┘
                                            │                                       │
                                     ┌──────┴──────┐                        ┌──────┴──────┐
                                     │  PostgreSQL  │◀────────────────────── │    Redis    │
                                     │  Database   │                         │   (Broker)  │
                                     └─────────────┘                         └─────────────┘
```

**Request flow:**

1. Client submits a `POST /api/v1/certificates/jobs` with a list of recipients
2. FastAPI validates input, creates a `CertificateJob` and one `Certificate` row per recipient in PostgreSQL, then returns `202 Accepted` immediately
3. A **Celery background task** is enqueued via Redis
4. The worker picks up the task, iterates over each recipient, generates a PDF, and updates each `Certificate` record independently
5. Client polls `GET /api/v1/certificates/jobs/{id}` to track progress
6. Completed PDFs are downloadable via `GET /api/v1/certificates/{id}/download`

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend API | FastAPI (Python) | Async-first, auto-generated OpenAPI docs, fast |
| Database | PostgreSQL | ACID compliance, UUIDs, reliable for job tracking |
| ORM | SQLAlchemy 2.0 (async) | Modern async support, type-safe mapped columns |
| Migrations | Alembic | Industry standard for schema versioning |
| Background Jobs | Celery + Redis | Decouples long-running generation from HTTP request lifecycle |
| PDF Generation | ReportLab | Pure Python, no external dependencies, full layout control |
| Frontend | React + Vite | Fast HMR, modern tooling |
| State Management | TanStack Query | Server state with auto-polling/refetch |
| Testing | pytest + pytest-asyncio | Async-aware test runner |

---

## Project Structure

```
Assignment/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Route handlers
│   │   ├── core/               # Config (pydantic-settings)
│   │   ├── db/                 # SQLAlchemy engine, session, base
│   │   ├── models/             # ORM models (CertificateJob, Certificate)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # certificate_generator.py (PDF logic)
│   │   ├── workers/            # Celery app + tasks
│   │   ├── static/certificates/ # Generated PDF files (served statically)
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # Database migrations
│   ├── tests/                  # pytest test suite
│   ├── .env                    # Local environment config
│   ├── alembic.ini
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/client.js       # Axios API wrapper
    │   ├── components/         # Sidebar, StatusBadge, RecipientsEditor, Modal
    │   ├── pages/              # Dashboard, CreateJob, JobList
    │   └── App.jsx
    ├── index.html
    └── package.json
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### 1. Clone and navigate

```bash
git clone <repo-url>
cd Assignment
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Copy the example and fill in your values
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/certificates_db
SYNC_DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/certificates_db
REDIS_URL=redis://localhost:6379/0
CERTIFICATE_OUTPUT_DIR=app/static/certificates
BASE_URL=http://localhost:8000
```

### 4. Create database and run migrations

```bash
# Create the database (run in psql or pgAdmin)
createdb certificates_db

# Run migrations
cd backend
alembic upgrade head
```

### 5. Frontend setup

```bash
cd frontend
npm install
```

---

## Running the Application

You need three terminal windows running simultaneously.

### Terminal 1 — FastAPI Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API available at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

### Terminal 2 — Celery Worker

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

> **Windows note:** Celery has limited Windows support. Add `--pool=solo` for local development:
> ```bash
> celery -A app.workers.celery_app worker --loglevel=info --pool=solo
> ```

### Terminal 3 — React Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:5173

---

## Running Tests

```bash
cd backend

# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test class
pytest tests/test_certificates.py::TestInputValidation -v

# Run a specific test
pytest tests/test_certificates.py::TestCreateJob::test_create_job_returns_202 -v
```

Tests use an **in-memory SQLite** database and mock out Celery task enqueueing — no PostgreSQL or Redis required to run the test suite.

---

## API Reference

### Create a Certificate Job

```
POST /api/v1/certificates/jobs
Content-Type: application/json
```

**Request body:**

```json
{
  "event_name": "Python Bootcamp 2026",
  "issued_by": "Tech Academy",
  "issue_date": "2026-10-01",
  "recipients": [
    {
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "course_name": "Advanced Python"
    },
    {
      "name": "Bob Smith",
      "email": "bob@example.com"
    }
  ]
}
```

**Response `202 Accepted`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "event_name": "Python Bootcamp 2026",
  "issued_by": "Tech Academy",
  "issue_date": "2026-10-01",
  "status": "pending",
  "total_recipients": 2,
  "completed_count": 0,
  "failed_count": 0,
  "progress_percent": 0.0,
  "created_at": "2026-10-01T12:00:00Z",
  "updated_at": "2026-10-01T12:00:00Z"
}
```

**Validation rules:**
- `event_name`, `issued_by`, `issue_date` — required, non-blank
- `recipients` — at least 1, max 1000
- `name` — at least 2 characters, max 255
- `email` — valid email format required
- `course_name` — optional, max 255 characters

---

### Check Job Status / Progress

```
GET /api/v1/certificates/jobs/{job_id}
```

Returns the job with `progress_percent`, counts, and `status` which can be:

| Status | Meaning |
|---|---|
| `pending` | Job accepted, waiting for worker |
| `processing` | Worker is generating certificates |
| `completed` | All certificates generated successfully |
| `partial` | Some succeeded, some failed |
| `failed` | All certificates failed |

---

### List All Jobs

```
GET /api/v1/certificates/jobs?skip=0&limit=20
```

---

### List Certificates for a Job

```
GET /api/v1/certificates/jobs/{job_id}/certificates
GET /api/v1/certificates/jobs/{job_id}/certificates?status=completed
GET /api/v1/certificates/jobs/{job_id}/certificates?status=failed
```

Each certificate includes `status`, `error_message` (if failed), and `file_url` (if completed).

---

### Download a Certificate PDF

```
GET /api/v1/certificates/{certificate_id}/download
```

Returns the PDF file as `application/pdf`. Only available when `status == completed`.

---

### Health Check

```
GET /health
```

---

## Design Decisions

### Why Celery + Redis for background processing?

The core requirement is **bulk generation** — potentially hundreds or thousands of certificates per request. Generating PDFs synchronously within the HTTP request would:
- Block the request for many seconds or minutes
- Risk timeout errors at the load balancer or client
- Provide no way to track partial progress

By using Celery with Redis as the broker, the API instantly returns `202 Accepted` with the job ID. The client can then poll for progress without holding an open connection. This is the standard pattern for long-running background tasks.

### Why isolate per-certificate failures?

The task iterates over each certificate inside a `try/except` block. If one PDF fails (e.g., a name with unusual characters triggers a rendering bug), the error is recorded on that `Certificate` row and processing continues for all others. A job is marked `partial` if some succeed and some fail, giving the client full visibility into which recipients need reprocessing.

### Why PostgreSQL over a job queue database?

PostgreSQL gives us:
- **ACID transactions** — no partial writes when creating a job + N certificates
- **Rich querying** — filter by status, paginate, join
- **Durability** — Celery's Redis result backend is volatile; the database is the source of truth for job state

### Why `202 Accepted` instead of `200 OK` or `201 Created`?

`202 Accepted` is the semantically correct HTTP status for "the request has been received and will be processed asynchronously." It signals to the client that the work is not done yet.

### Synchronous vs. asynchronous (async/await) in the Celery worker

Celery workers are synchronous by nature — they run in a thread pool, not an async event loop. That's why `SyncSessionLocal` (a regular `sessionmaker`) is used in the Celery task, while the FastAPI routes use the `AsyncSession`. Both share the same PostgreSQL database, just through different driver connections (`asyncpg` for async, `psycopg2` for sync).

### File storage

Generated PDFs are stored on disk under `app/static/` and served directly by FastAPI's `StaticFiles` mount. In a production system, these would be stored in object storage (S3, GCS) and served via signed URLs. The current approach is simple and appropriate for this scope.

---

## Certificate Template

All certificates use a single predefined dark-themed PDF template generated with ReportLab:

- **A4 Landscape** format
- **Dark navy background** (`#070b14`) with gold border ornaments
- **Recipient name** displayed prominently in large white text
- **Course/Event name** in gold
- **Issued by** and **Issue date** in a two-column footer with signature lines
- **Unique certificate ID** embedded in the footer

The template is defined in `app/services/certificate_generator.py` and requires no external template files.

---

## CSV Import (Frontend)

The UI supports bulk-importing recipients from a CSV file. Format:

```csv
name,email,course_name
Alice Johnson,alice@example.com,Advanced Python
Bob Smith,bob@example.com,
```

- Column headers must be: `name`, `email`, `course_name` (case-insensitive)
- `course_name` column is optional
- Empty rows are skipped automatically
