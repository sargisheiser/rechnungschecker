"""Add templates table.

Revision ID: 012
Revises: 011
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create template_type enum
    template_type_enum = postgresql.ENUM("sender", "receiver", name="templatetype", create_type=False)
    template_type_enum.create(op.get_bind(), checkfirst=True)

    # Create templates table
    op.create_table(
        "templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Template identification
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "template_type",
            template_type_enum,
            nullable=False,
        ),
        # Company information
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("street", sa.String(200), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="DE"),
        # Tax information
        sa.Column("vat_id", sa.String(20), nullable=True),
        sa.Column("tax_id", sa.String(30), nullable=True),
        # Contact information
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        # Bank details
        sa.Column("iban", sa.String(34), nullable=True),
        sa.Column("bic", sa.String(11), nullable=True),
        # Default flag
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("templates")

    # Drop the enum type
    template_type_enum = postgresql.ENUM("sender", "receiver", name="templatetype")
    template_type_enum.drop(op.get_bind(), checkfirst=True)
