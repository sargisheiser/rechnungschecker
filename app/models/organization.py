"""Organization and team management models."""

import enum
import secrets
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import PlanType


class OrganizationRole(str, enum.Enum):
    """Role within an organization."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Organization(Base):
    """Organization/team model for multi-user accounts."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Owner is the user who created the organization
    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Subscription (shared across all members)
    plan: Mapped[PlanType] = mapped_column(
        Enum(PlanType, values_callable=lambda x: [e.value for e in x]),
        default=PlanType.FREE,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan_valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Limits
    max_members: Mapped[int] = mapped_column(Integer, default=5)

    # Usage tracking (reset monthly, shared across org)
    validations_this_month: Mapped[int] = mapped_column(Integer, default=0)
    conversions_this_month: Mapped[int] = mapped_column(Integer, default=0)
    usage_reset_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    invitations = relationship(
        "OrganizationInvitation",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def get_validation_limit(self) -> int | None:
        """Return monthly validation limit based on plan. None = unlimited."""
        limits = {
            PlanType.FREE: 10,  # Slightly higher for org
            PlanType.STARTER: 200,
            PlanType.PRO: None,
            PlanType.STEUERBERATER: None,
        }
        return limits[self.plan]

    def get_conversion_limit(self) -> int:
        """Return monthly conversion limit based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.STARTER: 40,
            PlanType.PRO: 200,
            PlanType.STEUERBERATER: 1000,
        }
        return limits[self.plan]

    def can_validate(self) -> bool:
        """Check if organization can perform another validation."""
        limit = self.get_validation_limit()
        if limit is None:
            return True
        return self.validations_this_month < limit

    def can_convert(self) -> bool:
        """Check if organization can perform another conversion."""
        limit = self.get_conversion_limit()
        return self.conversions_this_month < limit


class OrganizationMember(Base):
    """Membership link between users and organizations."""

    __tablename__ = "organization_members"
    __table_args__ = (
        Index("ix_org_member_user_org", "user_id", "organization_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[OrganizationRole] = mapped_column(
        Enum(OrganizationRole, values_callable=lambda x: [e.value for e in x]),
        default=OrganizationRole.MEMBER,
    )

    # Who invited this member
    invited_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    invited_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])

    def can_manage_members(self) -> bool:
        """Check if this member can manage other members."""
        return self.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN)

    def can_manage_billing(self) -> bool:
        """Check if this member can manage billing."""
        return self.role == OrganizationRole.OWNER


class OrganizationInvitation(Base):
    """Pending invitation to join an organization."""

    __tablename__ = "organization_invitations"
    __table_args__ = (
        Index("ix_org_invite_email_org", "email", "organization_id"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[OrganizationRole] = mapped_column(
        Enum(OrganizationRole, values_callable=lambda x: [e.value for e in x]),
        default=OrganizationRole.MEMBER,
    )

    # Secure token for invitation link
    token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(32)
    )

    # Who created the invitation
    created_by_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    # Status
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.now(UTC).replace(tzinfo=None) > self.expires_at

    def is_valid(self) -> bool:
        """Check if invitation is valid (not expired and not accepted)."""
        return not self.is_expired() and self.accepted_at is None
