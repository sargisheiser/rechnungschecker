"""Add invoice_drafts table for invoice creator wizard.

Revision ID: 017
Revises: 016
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoice_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False, server_default="Neue Rechnung"),
        sa.Column("output_format", sa.String(20), nullable=False, server_default="xrechnung"),
        sa.Column("invoice_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("current_step", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_complete", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("generated_xml", sa.Text, nullable=True),
        sa.Column("validation_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invoice_drafts_user_id", "invoice_drafts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_invoice_drafts_user_id", table_name="invoice_drafts")
    op.drop_table("invoice_drafts")
