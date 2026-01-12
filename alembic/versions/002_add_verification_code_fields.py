"""Add verification code fields to users table.

Revision ID: 002
Revises: 001
Create Date: 2026-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification code fields
    op.add_column(
        "users",
        sa.Column("verification_code", sa.String(6), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("verification_code_expires", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "verification_code_expires")
    op.drop_column("users", "verification_code")
