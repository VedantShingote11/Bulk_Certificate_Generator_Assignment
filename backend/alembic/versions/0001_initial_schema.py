"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certificate_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("issued_by", sa.String(255), nullable=False),
        sa.Column("issue_date", sa.String(50), nullable=False),
        sa.Column("status", sa.Enum("pending", "processing", "completed", "failed", "partial", name="jobstatus"), nullable=False, server_default="pending"),
        sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("certificate_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("course_name", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("pending", "generating", "completed", "failed", name="certificatestatus"), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_certificates_job_id", "certificates", ["job_id"])
    op.create_index("ix_certificates_status", "certificates", ["status"])
    op.create_index("ix_certificate_jobs_status", "certificate_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("certificates")
    op.drop_table("certificate_jobs")
    op.execute("DROP TYPE IF EXISTS certificatestatus")
    op.execute("DROP TYPE IF EXISTS jobstatus")
