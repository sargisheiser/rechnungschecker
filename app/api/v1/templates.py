"""Template management API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.template import Template, TemplateType
from app.schemas.template import (
    TemplateCreate,
    TemplateList,
    TemplateListItem,
    TemplateResponse,
    TemplateUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=TemplateList,
    summary="List templates",
    description="Get all templates for the current user.",
)
async def list_templates(
    current_user: CurrentUser,
    db: DbSession,
    page: int = 1,
    page_size: int = 50,
    template_type: TemplateType | None = None,
) -> TemplateList:
    """List all templates for the current user."""
    # Build query
    query = select(Template).where(Template.user_id == current_user.id)

    if template_type:
        query = query.where(Template.template_type == template_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate and order (defaults first, then by name)
    query = (
        query.order_by(Template.is_default.desc(), Template.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    templates = result.scalars().all()

    return TemplateList(
        items=[
            TemplateListItem(
                id=template.id,
                name=template.name,
                template_type=template.template_type,
                company_name=template.company_name,
                city=template.city,
                is_default=template.is_default,
                created_at=template.created_at,
            )
            for template in templates
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    description="Create a new template.",
)
async def create_template(
    data: TemplateCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TemplateResponse:
    """Create a new template."""
    # If is_default is True, unset other defaults of same type
    if data.is_default:
        await _unset_defaults(current_user.id, data.template_type, db)

    # Create template
    template = Template(
        user_id=current_user.id,
        name=data.name,
        template_type=data.template_type,
        company_name=data.company_name,
        street=data.street,
        postal_code=data.postal_code,
        city=data.city,
        country_code=data.country_code,
        vat_id=data.vat_id,
        tax_id=data.tax_id,
        email=data.email,
        phone=data.phone,
        iban=data.iban,
        bic=data.bic,
        is_default=data.is_default,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    logger.info(f"Template created: user={current_user.email}, template={template.name}")

    return TemplateResponse.model_validate(template)


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get template",
    description="Get details for a specific template.",
)
async def get_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> TemplateResponse:
    """Get details for a specific template."""
    template = await _get_template_or_404(template_id, current_user.id, db)
    return TemplateResponse.model_validate(template)


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Update template",
    description="Update a template's information.",
)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TemplateResponse:
    """Update a template."""
    template = await _get_template_or_404(template_id, current_user.id, db)

    # Handle default flag change
    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_default") is True:
        # Determine template type to use
        new_type = update_data.get("template_type", template.template_type)
        await _unset_defaults(current_user.id, new_type, db, exclude_id=template.id)

    # Update fields
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    logger.info(f"Template updated: user={current_user.email}, template={template.name}")

    return TemplateResponse.model_validate(template)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    description="Delete a template.",
)
async def delete_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a template."""
    template = await _get_template_or_404(template_id, current_user.id, db)
    template_name = template.name

    await db.delete(template)
    await db.commit()

    logger.info(f"Template deleted: user={current_user.email}, template={template_name}")


@router.post(
    "/{template_id}/set-default",
    response_model=TemplateResponse,
    summary="Set as default",
    description="Set a template as the default for its type.",
)
async def set_default_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> TemplateResponse:
    """Set a template as the default for its type."""
    template = await _get_template_or_404(template_id, current_user.id, db)

    # Unset other defaults of same type
    await _unset_defaults(current_user.id, template.template_type, db, exclude_id=template.id)

    # Set this template as default
    template.is_default = True
    await db.commit()
    await db.refresh(template)

    logger.info(
        f"Template set as default: user={current_user.email}, "
        f"template={template.name}, type={template.template_type.value}"
    )

    return TemplateResponse.model_validate(template)


async def _get_template_or_404(template_id: UUID, user_id: UUID, db: DbSession) -> Template:
    """Get a template by ID or raise 404."""
    result = await db.execute(
        select(Template).where(
            Template.id == template_id,
            Template.user_id == user_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vorlage nicht gefunden.",
        )

    return template


async def _unset_defaults(
    user_id: UUID,
    template_type: TemplateType,
    db: DbSession,
    exclude_id: UUID | None = None,
) -> None:
    """Unset default flag for all templates of given type."""
    query = select(Template).where(
        Template.user_id == user_id,
        Template.template_type == template_type,
        Template.is_default == True,
    )

    if exclude_id:
        query = query.where(Template.id != exclude_id)

    result = await db.execute(query)
    templates = result.scalars().all()

    for template in templates:
        template.is_default = False
