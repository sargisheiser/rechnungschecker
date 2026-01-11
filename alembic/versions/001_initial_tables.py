"""Initial tables for users, guest usage, and validation logs.

Revision ID: 001
Revises:
Create Date: 2026-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    plan_type = postgresql.ENUM(
        "free", "starter", "pro", "steuerberater",
        name="plantype",
        create_type=True,
    )
    plan_type.create(op.get_bind(), checkfirst=True)

    file_type = postgresql.ENUM(
        "xrechnung", "zugferd",
        name="filetype",
        create_type=True,
    )
    file_type.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_verified", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "plan",
            postgresql.ENUM(
                "free", "starter", "pro", "steuerberater",
                name="plantype",
                create_type=False,
            ),
            default="free",
            nullable=False,
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("plan_valid_until", sa.DateTime(), nullable=True),
        sa.Column("validations_this_month", sa.Integer(), default=0, nullable=False),
        sa.Column("conversions_this_month", sa.Integer(), default=0, nullable=False),
        sa.Column("usage_reset_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )

    # Guest usage table
    op.create_table(
        "guest_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ip_address", sa.String(45), nullable=False, index=True),
        sa.Column("cookie_id", sa.String(64), nullable=True, index=True),
        sa.Column("validations_used", sa.Integer(), default=0, nullable=False),
        sa.Column(
            "first_validation_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_validation_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_guest_usage_ip_cookie",
        "guest_usage",
        ["ip_address", "cookie_id"],
    )

    # Validation logs table
    op.create_table(
        "validation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column(
            "file_type",
            postgresql.ENUM(
                "xrechnung", "zugferd",
                name="filetype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("error_count", sa.Integer(), default=0, nullable=False),
        sa.Column("warning_count", sa.Integer(), default=0, nullable=False),
        sa.Column("info_count", sa.Integer(), default=0, nullable=False),
        sa.Column("xrechnung_version", sa.String(20), nullable=True),
        sa.Column("zugferd_profile", sa.String(50), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=False),
        sa.Column("validator_version", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("validation_logs")
    op.drop_table("guest_usage")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS filetype")
    op.execute("DROP TYPE IF EXISTS plantype")
