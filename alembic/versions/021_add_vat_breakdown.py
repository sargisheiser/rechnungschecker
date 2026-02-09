"""Add vat_breakdown column for multi-rate invoice support.

Revision ID: 021
Revises: 020
Create Date: 2026-02-09

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "extracted_invoice_data",
        sa.Column("vat_breakdown", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("extracted_invoice_data", "vat_breakdown")
