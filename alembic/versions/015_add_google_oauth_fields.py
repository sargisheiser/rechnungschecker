"""Add Google OAuth fields to users.

Revision ID: 015
Revises: 014
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_id column for linking Google accounts
    op.add_column(
        "users",
        sa.Column("google_id", sa.String(255), nullable=True),
    )
    # Add unique constraint on google_id
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    # Add oauth_provider column to track which OAuth provider was used
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "oauth_provider")
    op.drop_column("users", "google_id")
