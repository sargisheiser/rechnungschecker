"""Invoice creator API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.invoice_draft import InvoiceDraft
from app.schemas.invoice import (
    GenerateInvoiceResponse,
    InvoiceData,
    InvoiceDraftCreate,
    InvoiceDraftList,
    InvoiceDraftListItem,
    InvoiceDraftResponse,
    InvoiceDraftUpdate,
)
from app.services.invoice_creator import xrechnung_generator
from app.services.validator.xrechnung import XRechnungValidator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/drafts/",
    response_model=InvoiceDraftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice draft",
    description="Create a new invoice draft for the wizard.",
)
async def create_draft(
    data: InvoiceDraftCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> InvoiceDraftResponse:
    """Create a new invoice draft."""
    draft = InvoiceDraft(
        user_id=current_user.id,
        name=data.name,
        output_format=data.output_format,
        client_id=data.client_id,
        invoice_data={},
    )

    db.add(draft)
    await db.flush()
    await db.refresh(draft)

    logger.info(f"Invoice draft created: {draft.id} by {current_user.email}")

    return InvoiceDraftResponse(
        id=draft.id,
        user_id=draft.user_id,
        client_id=draft.client_id,
        name=draft.name,
        output_format=draft.output_format,
        invoice_data=InvoiceData(**draft.invoice_data) if draft.invoice_data else InvoiceData(),
        current_step=draft.current_step,
        is_complete=draft.is_complete,
        generated_xml=draft.generated_xml,
        validation_result_id=draft.validation_result_id,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.get(
    "/drafts/",
    response_model=InvoiceDraftList,
    summary="List invoice drafts",
    description="List all invoice drafts for the current user.",
)
async def list_drafts(
    current_user: CurrentUser,
    db: DbSession,
) -> InvoiceDraftList:
    """List user's invoice drafts."""
    result = await db.execute(
        select(InvoiceDraft)
        .where(InvoiceDraft.user_id == current_user.id)
        .order_by(InvoiceDraft.updated_at.desc())
    )

    drafts = result.scalars().all()

    return InvoiceDraftList(
        drafts=[
            InvoiceDraftListItem(
                id=d.id,
                name=d.name,
                output_format=d.output_format,
                current_step=d.current_step,
                is_complete=d.is_complete,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in drafts
        ],
        total=len(drafts),
    )


@router.get(
    "/drafts/{draft_id}",
    response_model=InvoiceDraftResponse,
    summary="Get invoice draft",
    description="Get a specific invoice draft.",
)
async def get_draft(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> InvoiceDraftResponse:
    """Get invoice draft by ID."""
    result = await db.execute(
        select(InvoiceDraft).where(
            InvoiceDraft.id == draft_id,
            InvoiceDraft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entwurf nicht gefunden",
        )

    return InvoiceDraftResponse(
        id=draft.id,
        user_id=draft.user_id,
        client_id=draft.client_id,
        name=draft.name,
        output_format=draft.output_format,
        invoice_data=InvoiceData(**draft.invoice_data) if draft.invoice_data else InvoiceData(),
        current_step=draft.current_step,
        is_complete=draft.is_complete,
        generated_xml=draft.generated_xml,
        validation_result_id=draft.validation_result_id,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.patch(
    "/drafts/{draft_id}",
    response_model=InvoiceDraftResponse,
    summary="Update invoice draft",
    description="Update an invoice draft (wizard progress).",
)
async def update_draft(
    draft_id: UUID,
    data: InvoiceDraftUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> InvoiceDraftResponse:
    """Update invoice draft."""
    result = await db.execute(
        select(InvoiceDraft).where(
            InvoiceDraft.id == draft_id,
            InvoiceDraft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entwurf nicht gefunden",
        )

    if data.name is not None:
        draft.name = data.name
    if data.output_format is not None:
        draft.output_format = data.output_format
    if data.current_step is not None:
        draft.current_step = data.current_step
    if data.invoice_data is not None:
        draft.invoice_data = data.invoice_data.model_dump(exclude_none=True)

    await db.flush()
    await db.refresh(draft)

    logger.info(f"Invoice draft updated: {draft.id}")

    return InvoiceDraftResponse(
        id=draft.id,
        user_id=draft.user_id,
        client_id=draft.client_id,
        name=draft.name,
        output_format=draft.output_format,
        invoice_data=InvoiceData(**draft.invoice_data) if draft.invoice_data else InvoiceData(),
        current_step=draft.current_step,
        is_complete=draft.is_complete,
        generated_xml=draft.generated_xml,
        validation_result_id=draft.validation_result_id,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


@router.delete(
    "/drafts/{draft_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete invoice draft",
    description="Delete an invoice draft.",
)
async def delete_draft(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Delete invoice draft."""
    result = await db.execute(
        select(InvoiceDraft).where(
            InvoiceDraft.id == draft_id,
            InvoiceDraft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entwurf nicht gefunden",
        )

    await db.delete(draft)
    await db.flush()

    logger.info(f"Invoice draft deleted: {draft_id}")

    return {"message": "Entwurf erfolgreich geloescht"}


@router.post(
    "/drafts/{draft_id}/generate",
    response_model=GenerateInvoiceResponse,
    summary="Generate invoice",
    description="Generate XRechnung XML from the draft.",
)
async def generate_invoice(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> GenerateInvoiceResponse:
    """Generate invoice XML from draft."""
    result = await db.execute(
        select(InvoiceDraft).where(
            InvoiceDraft.id == draft_id,
            InvoiceDraft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entwurf nicht gefunden",
        )

    # Parse invoice data
    try:
        invoice_data = InvoiceData(**draft.invoice_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungueltige Rechnungsdaten: {str(e)}",
        )

    # Validate required fields
    errors = []
    if not invoice_data.seller:
        errors.append("Verkaeufer-Informationen fehlen")
    if not invoice_data.buyer:
        errors.append("Kaeufer-Informationen fehlen")
    if not invoice_data.line_items:
        errors.append("Mindestens eine Rechnungsposition erforderlich")
    if not invoice_data.invoice_number:
        errors.append("Rechnungsnummer fehlt")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors),
        )

    # Generate XML
    try:
        xml = xrechnung_generator.generate(invoice_data)
    except Exception as e:
        logger.error(f"Failed to generate invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der XML-Generierung: {str(e)}",
        )

    # Save generated XML to draft
    draft.generated_xml = xml
    draft.is_complete = True
    await db.flush()

    logger.info(f"Invoice generated from draft: {draft_id}")

    # Validate the generated XML with KoSIT validator
    validator = XRechnungValidator()
    try:
        validation_result = await validator.validate(
            content=xml.encode("utf-8"),
            filename=f"{draft.name}.xml",
            user_id=current_user.id,
        )

        return GenerateInvoiceResponse(
            id=draft.id,
            xml=xml,
            is_valid=validation_result.is_valid,
            validation_errors=[e.message_de or e.code for e in validation_result.errors],
            validation_warnings=[w.message_de or w.code for w in validation_result.warnings],
        )
    except Exception as e:
        logger.warning(f"Validation of generated invoice failed: {e}")
        # Return as unvalidated if validation service fails
        return GenerateInvoiceResponse(
            id=draft.id,
            xml=xml,
            is_valid=False,
            validation_errors=[f"Validierung fehlgeschlagen: {str(e)}"],
            validation_warnings=[],
        )


@router.get(
    "/drafts/{draft_id}/preview",
    summary="Preview invoice XML",
    description="Get a preview of the generated XML.",
)
async def preview_invoice(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    """Preview the generated invoice XML."""
    result = await db.execute(
        select(InvoiceDraft).where(
            InvoiceDraft.id == draft_id,
            InvoiceDraft.user_id == current_user.id,
        )
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entwurf nicht gefunden",
        )

    # Generate preview (even if not complete)
    invoice_data = InvoiceData(**draft.invoice_data) if draft.invoice_data else InvoiceData()

    try:
        xml = xrechnung_generator.generate(invoice_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vorschau konnte nicht erstellt werden: {str(e)}",
        )

    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": f'inline; filename="{draft.name}.xml"'},
    )
