"""Add integration settings table.

Revision ID: 008
Revises: 007
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create integration_settings table
    op.create_table(
        "integration_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "integration_type",
            sa.Enum("lexoffice", "slack", "teams", name="integrationtype"),
            nullable=False,
        ),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("encrypted_config", sa.Text, nullable=False),
        sa.Column("notify_on_valid", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notify_on_invalid", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notify_on_warning", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
        sa.Column("total_requests", sa.Integer, nullable=False, server_default="0"),
        sa.Column("successful_requests", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_requests", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Index for user lookup
    op.create_index(
        "ix_integration_settings_user_id",
        "integration_settings",
        ["user_id"],
    )

    # Unique index: one integration type per user
    op.create_index(
        "ix_integration_user_type",
        "integration_settings",
        ["user_id", "integration_type"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_integration_user_type", table_name="integration_settings")
    op.drop_index("ix_integration_settings_user_id", table_name="integration_settings")
    op.drop_table("integration_settings")
    op.execute("DROP TYPE IF EXISTS integrationtype")
