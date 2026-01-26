"""Add is_admin field to users.

Revision ID: 014
Revises: 013
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
