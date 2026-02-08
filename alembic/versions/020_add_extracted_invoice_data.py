"""Add extracted_invoice_data table for DATEV export.

Revision ID: 020
Revises: 019
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "extracted_invoice_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "validation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("validation_logs.id", ondelete="CASCADE"),
            unique=True,
            index=True,
            nullable=False,
        ),
        # Invoice identifiers
        sa.Column("invoice_number", sa.String(100), nullable=True),
        sa.Column("invoice_date", sa.Date, nullable=True),
        # Financial totals
        sa.Column("net_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("vat_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("gross_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        # Primary VAT rate
        sa.Column("vat_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        # Seller info
        sa.Column("seller_name", sa.String(200), nullable=True),
        # Extraction metadata
        sa.Column(
            "confidence", sa.Numeric(precision=3, scale=2), nullable=False, server_default="1.0"
        ),
        sa.Column(
            "extracted_at", sa.DateTime, server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("extracted_invoice_data")
