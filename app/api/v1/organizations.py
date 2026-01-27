"""Organization/Team management API endpoints."""

import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.organization import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
    OrganizationRole,
)
from app.models.user import User
from app.schemas.organization import (
    InvitationResponse,
    MemberInvite,
    MemberListResponse,
    MemberResponse,
    MemberUpdate,
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from organization name."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Add random suffix for uniqueness
    suffix = secrets.token_hex(4)
    return f"{slug}-{suffix}"


async def get_org_with_permission(
    db: DbSession,
    org_id: UUID,
    user: User,
    require_admin: bool = False,
) -> tuple[Organization, OrganizationMember]:
    """Get organization and verify user has permission."""
    # Get organization
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation nicht gefunden",
        )

    # Get membership
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kein Mitglied dieser Organisation",
        )

    if require_admin and not member.can_manage_members():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administratorrechte erforderlich",
        )

    return org, member


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
    description="Create a new organization/team.",
)
async def create_organization(
    data: OrganizationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> OrganizationResponse:
    """Create a new organization with the current user as owner."""
    # Generate unique slug
    slug = generate_slug(data.name)

    # Check slug uniqueness (should be unique due to random suffix)
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    if result.scalar_one_or_none():
        slug = generate_slug(data.name)  # Regenerate

    # Create organization
    org = Organization(
        name=data.name,
        slug=slug,
        description=data.description,
        owner_id=current_user.id,
    )

    db.add(org)
    await db.flush()

    # Add owner as first member
    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrganizationRole.OWNER,
        joined_at=datetime.now(UTC).replace(tzinfo=None),
    )

    db.add(member)
    await db.flush()
    await db.refresh(org)

    logger.info(f"Organization created: {org.name} by {current_user.email}")

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        owner_id=org.owner_id,
        plan=org.plan.value,
        max_members=org.max_members,
        is_active=org.is_active,
        validations_this_month=org.validations_this_month,
        conversions_this_month=org.conversions_this_month,
        member_count=1,
        created_at=org.created_at,
    )


@router.get(
    "/",
    response_model=OrganizationListResponse,
    summary="List organizations",
    description="List all organizations the current user is a member of.",
)
async def list_organizations(
    current_user: CurrentUser,
    db: DbSession,
) -> OrganizationListResponse:
    """List organizations the user belongs to."""
    result = await db.execute(
        select(Organization, func.count(OrganizationMember.id).label("member_count"))
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == current_user.id)
        .group_by(Organization.id)
    )

    orgs = result.all()

    return OrganizationListResponse(
        organizations=[
            OrganizationResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                description=org.description,
                owner_id=org.owner_id,
                plan=org.plan.value,
                max_members=org.max_members,
                is_active=org.is_active,
                validations_this_month=org.validations_this_month,
                conversions_this_month=org.conversions_this_month,
                member_count=member_count,
                created_at=org.created_at,
            )
            for org, member_count in orgs
        ],
        total=len(orgs),
    )


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
    description="Get organization details.",
)
async def get_organization(
    org_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> OrganizationResponse:
    """Get organization details."""
    org, _ = await get_org_with_permission(db, org_id, current_user)

    # Get member count
    result = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == org_id
        )
    )
    member_count = result.scalar()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        owner_id=org.owner_id,
        plan=org.plan.value,
        max_members=org.max_members,
        is_active=org.is_active,
        validations_this_month=org.validations_this_month,
        conversions_this_month=org.conversions_this_month,
        member_count=member_count,
        created_at=org.created_at,
    )


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update organization details. Requires admin role.",
)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> OrganizationResponse:
    """Update organization details."""
    org, _ = await get_org_with_permission(db, org_id, current_user, require_admin=True)

    if data.name is not None:
        org.name = data.name
    if data.description is not None:
        org.description = data.description

    await db.flush()
    await db.refresh(org)

    logger.info(f"Organization updated: {org.name}")

    # Get member count
    result = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == org_id
        )
    )
    member_count = result.scalar()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        owner_id=org.owner_id,
        plan=org.plan.value,
        max_members=org.max_members,
        is_active=org.is_active,
        validations_this_month=org.validations_this_month,
        conversions_this_month=org.conversions_this_month,
        member_count=member_count,
        created_at=org.created_at,
    )


@router.delete(
    "/{org_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete organization",
    description="Delete organization. Only the owner can delete.",
)
async def delete_organization(
    org_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Delete organization (owner only)."""
    org, member = await get_org_with_permission(db, org_id, current_user)

    if member.role != OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Inhaber kann die Organisation loeschen",
        )

    await db.delete(org)
    await db.flush()

    logger.info(f"Organization deleted: {org.name}")

    return {"message": "Organisation erfolgreich geloescht"}


# Member management endpoints


@router.get(
    "/{org_id}/members",
    response_model=MemberListResponse,
    summary="List members",
    description="List all members of the organization.",
)
async def list_members(
    org_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MemberListResponse:
    """List organization members."""
    await get_org_with_permission(db, org_id, current_user)

    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .where(OrganizationMember.organization_id == org_id)
    )

    members = result.all()

    return MemberListResponse(
        members=[
            MemberResponse(
                id=member.id,
                user_id=member.user_id,
                email=user.email,
                full_name=user.full_name,
                role=member.role.value,
                invited_at=member.invited_at,
                joined_at=member.joined_at,
            )
            for member, user in members
        ],
        total=len(members),
    )


@router.post(
    "/{org_id}/members",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite member",
    description="Invite a new member to the organization.",
)
async def invite_member(
    org_id: UUID,
    data: MemberInvite,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
) -> InvitationResponse:
    """Invite a new member to the organization."""
    org, _ = await get_org_with_permission(db, org_id, current_user, require_admin=True)

    # Check member limit
    result = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == org_id
        )
    )
    member_count = result.scalar()

    if member_count >= org.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximale Mitgliederzahl erreicht ({org.max_members})",
        )

    # Check if user is already a member
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == existing_user.id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Benutzer ist bereits Mitglied",
            )

    # Check for existing pending invitation
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.email == data.email,
            OrganizationInvitation.accepted_at.is_(None),
        )
    )
    existing_invite = result.scalar_one_or_none()

    if existing_invite and existing_invite.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Es existiert bereits eine Einladung fuer diese E-Mail",
        )

    # Create invitation
    role = OrganizationRole(data.role)
    invitation = OrganizationInvitation(
        organization_id=org_id,
        email=data.email,
        role=role,
        created_by_id=current_user.id,
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=7),
    )

    db.add(invitation)
    await db.flush()
    await db.refresh(invitation)

    # Send invitation email
    base_url = str(request.base_url).rstrip("/")
    invite_url = f"{base_url}/einladung/{invitation.token}"

    try:
        await email_service.send_email(
            to=data.email,
            subject=f"Einladung zu {org.name} - RechnungsChecker",
            html_content=f"""
            <h2>Sie wurden eingeladen!</h2>
            <p>{current_user.full_name or current_user.email} hat Sie eingeladen,
            dem Team <strong>{org.name}</strong> bei RechnungsChecker beizutreten.</p>
            <p>Ihre Rolle: <strong>{role.value.capitalize()}</strong></p>
            <p><a href="{invite_url}" style="background-color: #2563eb; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 5px;">Einladung annehmen</a></p>
            <p>Dieser Link ist 7 Tage gueltig.</p>
            """,
        )
    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")

    logger.info(f"Member invited to {org.name}: {data.email}")

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role.value,
        organization_name=org.name,
        expires_at=invitation.expires_at,
        is_valid=invitation.is_valid(),
    )


@router.patch(
    "/{org_id}/members/{user_id}",
    response_model=MemberResponse,
    summary="Update member role",
    description="Update a member's role. Requires admin role.",
)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    data: MemberUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> MemberResponse:
    """Update member role."""
    org, current_member = await get_org_with_permission(
        db, org_id, current_user, require_admin=True
    )

    # Get target member
    result = await db.execute(
        select(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mitglied nicht gefunden",
        )

    member, user = row

    # Cannot change owner role
    if member.role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Die Rolle des Inhabers kann nicht geaendert werden",
        )

    # Cannot set someone as owner through this endpoint
    if data.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inhaber kann nur ueber Eigentumsuebertragung geaendert werden",
        )

    member.role = OrganizationRole(data.role)
    await db.flush()

    logger.info(f"Member role updated in {org.name}: {user.email} -> {data.role}")

    return MemberResponse(
        id=member.id,
        user_id=member.user_id,
        email=user.email,
        full_name=user.full_name,
        role=member.role.value,
        invited_at=member.invited_at,
        joined_at=member.joined_at,
    )


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove member",
    description="Remove a member from the organization.",
)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Remove member from organization."""
    org, current_member = await get_org_with_permission(
        db, org_id, current_user, require_admin=True
    )

    # Get target member
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mitglied nicht gefunden",
        )

    # Cannot remove owner
    if member.role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Der Inhaber kann nicht entfernt werden",
        )

    await db.delete(member)
    await db.flush()

    logger.info(f"Member removed from {org.name}: user_id={user_id}")

    return {"message": "Mitglied erfolgreich entfernt"}


# Invitation endpoints


@router.get(
    "/invitations/{token}",
    response_model=InvitationResponse,
    summary="Get invitation",
    description="Get invitation details by token.",
)
async def get_invitation(
    token: str,
    db: DbSession,
) -> InvitationResponse:
    """Get invitation details."""
    result = await db.execute(
        select(OrganizationInvitation, Organization)
        .join(Organization, OrganizationInvitation.organization_id == Organization.id)
        .where(OrganizationInvitation.token == token)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Einladung nicht gefunden",
        )

    invitation, org = row

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role.value,
        organization_name=org.name,
        expires_at=invitation.expires_at,
        is_valid=invitation.is_valid(),
    )


@router.post(
    "/invitations/{token}/accept",
    status_code=status.HTTP_200_OK,
    summary="Accept invitation",
    description="Accept an invitation to join an organization.",
)
async def accept_invitation(
    token: str,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Accept invitation and join organization."""
    result = await db.execute(
        select(OrganizationInvitation, Organization)
        .join(Organization, OrganizationInvitation.organization_id == Organization.id)
        .where(OrganizationInvitation.token == token)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Einladung nicht gefunden",
        )

    invitation, org = row

    if not invitation.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Einladung ist abgelaufen oder wurde bereits angenommen",
        )

    # Check if invitation matches user email
    if invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Diese Einladung ist fuer eine andere E-Mail-Adresse",
        )

    # Check if already a member
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie sind bereits Mitglied dieser Organisation",
        )

    # Create membership
    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=invitation.role,
        invited_by_id=invitation.created_by_id,
        invited_at=invitation.created_at,
        joined_at=datetime.now(UTC).replace(tzinfo=None),
    )

    db.add(member)

    # Mark invitation as accepted
    invitation.accepted_at = datetime.now(UTC).replace(tzinfo=None)

    await db.flush()

    logger.info(f"User {current_user.email} joined organization {org.name}")

    return {"message": f"Sie sind jetzt Mitglied von {org.name}"}
