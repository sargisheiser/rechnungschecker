"""Add file_name column to validation_logs table.

Revision ID: 003
Revises: 002
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "validation_logs",
        sa.Column("file_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("validation_logs", "file_name")
