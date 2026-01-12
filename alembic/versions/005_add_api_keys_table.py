"""Add API keys table.

Revision ID: 005
Revises: 004
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
        sa.Column("usage_count", sa.Integer, default=0, nullable=False),
        sa.Column("requests_this_month", sa.Integer, default=0, nullable=False),
        sa.Column("requests_reset_date", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
