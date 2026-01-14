"""Add company_name to users table.

Revision ID: 009
Revises: 008_add_integration_settings
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add company_name column to users table."""
    op.add_column(
        "users",
        sa.Column("company_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Remove company_name column from users table."""
    op.drop_column("users", "company_name")
