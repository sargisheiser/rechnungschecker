"""Add batch validation tables.

Revision ID: 010
Revises: 009
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create batch job status enum
    batchjobstatus = postgresql.ENUM(
        "pending", "processing", "completed", "failed", "cancelled",
        name="batchjobstatus",
    )
    batchjobstatus.create(op.get_bind())

    # Create batch file status enum
    batchfilestatus = postgresql.ENUM(
        "pending", "processing", "completed", "failed", "skipped",
        name="batchfilestatus",
    )
    batchfilestatus.create(op.get_bind())

    # Create batch_jobs table
    op.create_table(
        "batch_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # Job metadata
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status",
            batchjobstatus,
            nullable=False,
            server_default="pending",
        ),
        # Progress tracking
        sa.Column("total_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("processed_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("successful_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer, nullable=False, server_default="0"),
        # Error tracking
        sa.Column("error_message", sa.Text, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Create batch_files table
    op.create_table(
        "batch_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("batch_jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # File info
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("file_content", sa.LargeBinary, nullable=True),
        # Status
        sa.Column(
            "status",
            batchfilestatus,
            nullable=False,
            server_default="pending",
        ),
        # Result reference
        sa.Column(
            "validation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("validation_logs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Error info
        sa.Column("error_message", sa.Text, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("batch_files")
    op.drop_table("batch_jobs")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS batchfilestatus")
    op.execute("DROP TYPE IF EXISTS batchjobstatus")
