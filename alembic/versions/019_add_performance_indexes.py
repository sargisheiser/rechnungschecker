"""Add compound indexes for performance optimization.

Revision ID: 019
Revises: 018
Create Date: 2026-01-26

"""
from alembic import op

# revision identifiers, used by Alembic
revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Compound indexes on ValidationLog for faster filtered queries
    op.create_index(
        "ix_validation_user_created",
        "validation_logs",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_validation_client_created",
        "validation_logs",
        ["client_id", "created_at"],
    )

    # Compound index on BatchFile for faster status lookups
    op.create_index(
        "ix_batch_file_job_status",
        "batch_files",
        ["batch_job_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_batch_file_job_status", "batch_files")
    op.drop_index("ix_validation_client_created", "validation_logs")
    op.drop_index("ix_validation_user_created", "validation_logs")
