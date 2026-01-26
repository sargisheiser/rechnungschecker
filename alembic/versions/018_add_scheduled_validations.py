"""Add scheduled validation tables for cloud storage integration.

Revision ID: 018
Revises: 017
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cloud_storage_provider enum
    cloud_provider = postgresql.ENUM(
        "s3", "gcs", "azure_blob", name="cloudstorageprovider", create_type=False
    )
    cloud_provider.create(op.get_bind(), checkfirst=True)

    # Create job_status enum
    job_status = postgresql.ENUM(
        "active", "paused", "error", name="jobstatus", create_type=False
    )
    job_status.create(op.get_bind(), checkfirst=True)

    # Create run_status enum
    run_status = postgresql.ENUM(
        "pending", "running", "completed", "failed", name="runstatus", create_type=False
    )
    run_status.create(op.get_bind(), checkfirst=True)

    # Create scheduled_validation_jobs table
    op.create_table(
        "scheduled_validation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        # Cloud storage config
        sa.Column(
            "provider",
            postgresql.ENUM(
                "s3", "gcs", "azure_blob",
                name="cloudstorageprovider",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("encrypted_credentials", sa.Text, nullable=False),
        sa.Column("bucket_name", sa.String(255), nullable=False),
        sa.Column("prefix", sa.String(500), nullable=True),
        sa.Column("file_pattern", sa.String(100), nullable=False, server_default="*.xml"),
        # Schedule config
        sa.Column("schedule_cron", sa.String(100), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Europe/Berlin"),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "status",
            postgresql.ENUM("active", "paused", "error", name="jobstatus", create_type=False),
            nullable=False,
            server_default="active",
        ),
        # Post-validation options
        sa.Column("delete_after_validation", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("move_to_folder", sa.String(500), nullable=True),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        # Statistics
        sa.Column("last_run_at", sa.DateTime, nullable=True),
        sa.Column("last_run_status", sa.String(50), nullable=True),
        sa.Column("total_runs", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_files_validated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_files_valid", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_files_invalid", sa.Integer, nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_scheduled_validation_jobs_user_id",
        "scheduled_validation_jobs",
        ["user_id"],
    )

    # Create scheduled_validation_runs table
    op.create_table(
        "scheduled_validation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scheduled_validation_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "running", "completed", "failed",
                name="runstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        # File statistics
        sa.Column("files_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_validated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_valid", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_invalid", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index(
        "ix_scheduled_validation_runs_job_id",
        "scheduled_validation_runs",
        ["job_id"],
    )

    # Create scheduled_validation_files table
    op.create_table(
        "scheduled_validation_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scheduled_validation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_key", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False, server_default="0"),
        # Validation results
        sa.Column("is_valid", sa.Boolean, nullable=True),
        sa.Column("error_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "validation_log_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("validation_logs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index(
        "ix_scheduled_validation_files_run_id",
        "scheduled_validation_files",
        ["run_id"],
    )


def downgrade() -> None:
    # Drop scheduled_validation_files table
    op.drop_index("ix_scheduled_validation_files_run_id", table_name="scheduled_validation_files")
    op.drop_table("scheduled_validation_files")

    # Drop scheduled_validation_runs table
    op.drop_index("ix_scheduled_validation_runs_job_id", table_name="scheduled_validation_runs")
    op.drop_table("scheduled_validation_runs")

    # Drop scheduled_validation_jobs table
    op.drop_index("ix_scheduled_validation_jobs_user_id", table_name="scheduled_validation_jobs")
    op.drop_table("scheduled_validation_jobs")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS runstatus")
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS cloudstorageprovider")
