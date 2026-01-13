"""Add webhook tables.

Revision ID: 007
Revises: 006
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webhook_subscriptions table
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Configuration
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "events",
            postgresql.ARRAY(sa.String(50)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("secret", sa.String(100), nullable=False),
        # Status
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # Statistics
        sa.Column("total_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("successful_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_deliveries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime, nullable=True),
        sa.Column("last_success_at", sa.DateTime, nullable=True),
        sa.Column("last_failure_at", sa.DateTime, nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Create webhook_deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Event details
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        # Delivery status
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        # Retry tracking
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="4"),
        sa.Column("next_retry_at", sa.DateTime, nullable=True),
        # Response details
        sa.Column("response_status_code", sa.Integer, nullable=True),
        sa.Column("response_body", sa.Text, nullable=True),
        sa.Column("response_time_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("last_attempt_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Create partial index for retry processing
    op.create_index(
        "ix_webhook_deliveries_retry",
        "webhook_deliveries",
        ["status", "next_retry_at"],
        postgresql_where=sa.text("status = 'retrying'"),
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_retry", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_subscriptions")
