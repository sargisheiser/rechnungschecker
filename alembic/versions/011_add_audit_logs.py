"""Add audit logs table.

Revision ID: 011
Revises: 010
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit action enum
    auditaction = postgresql.ENUM(
        "login",
        "logout",
        "login_failed",
        "password_reset_request",
        "password_reset_complete",
        "password_change",
        "validate",
        "validate_batch",
        "convert",
        "api_key_create",
        "api_key_revoke",
        "client_create",
        "client_update",
        "client_delete",
        "webhook_create",
        "webhook_update",
        "webhook_delete",
        "integration_create",
        "integration_update",
        "integration_delete",
        "export_data",
        "settings_update",
        name="auditaction",
    )
    auditaction.create(op.get_bind())

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "action",
            auditaction,
            nullable=False,
        ),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )

    # Create composite index for efficient user log queries
    op.create_index(
        "ix_audit_logs_user_created",
        "audit_logs",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")
    op.drop_table("audit_logs")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS auditaction")
