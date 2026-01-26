"""Add organization tables for team accounts.

Revision ID: 016
Revises: 015
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organization_role enum
    org_role = postgresql.ENUM(
        "owner", "admin", "member", name="organizationrole", create_type=False
    )
    org_role.create(op.get_bind(), checkfirst=True)

    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan",
            postgresql.ENUM(
                "free", "starter", "pro", "steuerberater",
                name="plantype",
                create_type=False,
            ),
            nullable=False,
            server_default="free",
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("plan_valid_until", sa.DateTime, nullable=True),
        sa.Column("max_members", sa.Integer, nullable=False, server_default="5"),
        sa.Column("validations_this_month", sa.Integer, nullable=False, server_default="0"),
        sa.Column("conversions_this_month", sa.Integer, nullable=False, server_default="0"),
        sa.Column("usage_reset_date", sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_owner_id", "organizations", ["owner_id"])

    # Create organization_members table
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            postgresql.ENUM("owner", "admin", "member", name="organizationrole", create_type=False),
            nullable=False,
            server_default="member",
        ),
        sa.Column(
            "invited_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("invited_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("joined_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_organization_members_organization_id", "organization_members", ["organization_id"])
    op.create_index("ix_organization_members_user_id", "organization_members", ["user_id"])
    op.create_index(
        "ix_org_member_user_org",
        "organization_members",
        ["user_id", "organization_id"],
        unique=True,
    )

    # Create organization_invitations table
    op.create_table(
        "organization_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("owner", "admin", "member", name="organizationrole", create_type=False),
            nullable=False,
            server_default="member",
        ),
        sa.Column("token", sa.String(64), unique=True, nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("accepted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organization_invitations_organization_id", "organization_invitations", ["organization_id"])
    op.create_index("ix_organization_invitations_email", "organization_invitations", ["email"])
    op.create_index("ix_organization_invitations_token", "organization_invitations", ["token"], unique=True)
    op.create_index(
        "ix_org_invite_email_org",
        "organization_invitations",
        ["email", "organization_id"],
    )

    # Add current_organization_id to users table
    op.add_column(
        "users",
        sa.Column("current_organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    # Remove current_organization_id from users
    op.drop_column("users", "current_organization_id")

    # Drop organization_invitations table
    op.drop_index("ix_org_invite_email_org", table_name="organization_invitations")
    op.drop_index("ix_organization_invitations_token", table_name="organization_invitations")
    op.drop_index("ix_organization_invitations_email", table_name="organization_invitations")
    op.drop_index("ix_organization_invitations_organization_id", table_name="organization_invitations")
    op.drop_table("organization_invitations")

    # Drop organization_members table
    op.drop_index("ix_org_member_user_org", table_name="organization_members")
    op.drop_index("ix_organization_members_user_id", table_name="organization_members")
    op.drop_index("ix_organization_members_organization_id", table_name="organization_members")
    op.drop_table("organization_members")

    # Drop organizations table
    op.drop_index("ix_organizations_owner_id", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS organizationrole")
