"""Add user notification preferences and full_name.

Revision ID: 013
Revises: 012
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add full_name column
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(255), nullable=True),
    )

    # Add notification preference columns
    op.add_column(
        "users",
        sa.Column("email_notifications", sa.Boolean, nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("notify_validation_results", sa.Boolean, nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("notify_weekly_summary", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("notify_marketing", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("users", "notify_marketing")
    op.drop_column("users", "notify_weekly_summary")
    op.drop_column("users", "notify_validation_results")
    op.drop_column("users", "email_notifications")
    op.drop_column("users", "full_name")
