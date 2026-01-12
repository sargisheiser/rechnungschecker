"""Add clients table and client_id to validation_logs.

Revision ID: 006
Revises: 005
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create clients table
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Client information
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("client_number", sa.String(50), nullable=True),
        sa.Column("tax_number", sa.String(50), nullable=True),
        sa.Column("vat_id", sa.String(20), nullable=True),
        # Contact
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        # Address
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="DE"),
        # Notes
        sa.Column("notes", sa.Text, nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # Statistics
        sa.Column("validation_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_validation_at", sa.DateTime, nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Add client_id to validation_logs
    op.add_column(
        "validation_logs",
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("validation_logs", "client_id")
    op.drop_table("clients")
