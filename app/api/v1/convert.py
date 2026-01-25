"""API endpoints for PDF to e-invoice conversion."""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_current_user, get_current_user_optional as get_optional_user
from app.core.limits import check_user_conversion_limit, increment_user_conversion
from app.core.exceptions import UsageLimitError
from app.models.user import User
from app.schemas.conversion import (
    ConversionRequest,
    ConversionResponse,
    ConversionStatusResponse,
    ExtractedDataSchema,
    OutputFormat,
    PreviewResponse,
    SendInvoiceEmailRequest,
    SendInvoiceEmailResponse,
    ValidationErrorSchema,
    ValidationResultSchema,
    ZUGFeRDProfile,
)

logger = logging.getLogger(__name__)
from app.services.converter.service import (
    ConversionService,
    OutputFormat as ServiceOutputFormat,
    ZUGFeRDProfile as ServiceZUGFeRDProfile,
)
from app.services.converter.extractor import Address, InvoiceData

router = APIRouter(tags=["conversion"])

# Initialize conversion service
conversion_service = ConversionService()

# In-memory storage for converted files (would use Redis/S3 in production)
_conversion_cache: dict[str, tuple[bytes, str, str]] = {}


def _invoice_data_to_schema(data: InvoiceData) -> ExtractedDataSchema:
    """Convert InvoiceData to ExtractedDataSchema."""
    return ExtractedDataSchema(
        invoice_number=data.invoice_number,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        delivery_date=data.delivery_date,
        seller_name=data.seller.name if data.seller else None,
        seller_street=data.seller.street if data.seller else None,
        seller_postal_code=data.seller.postal_code if data.seller else None,
        seller_city=data.seller.city if data.seller else None,
        seller_vat_id=data.seller_vat_id,
        seller_tax_id=data.seller_tax_id,
        buyer_name=data.buyer.name if data.buyer else None,
        buyer_street=data.buyer.street if data.buyer else None,
        buyer_postal_code=data.buyer.postal_code if data.buyer else None,
        buyer_city=data.buyer.city if data.buyer else None,
        buyer_reference=data.buyer_reference,
        net_amount=data.net_amount,
        vat_amount=data.vat_amount,
        gross_amount=data.gross_amount,
        currency=data.currency,
        iban=data.iban,
        bic=data.bic,
        bank_name=data.bank_name,
        payment_reference=data.payment_reference,
        leitweg_id=data.leitweg_id,
        order_reference=data.order_reference,
        confidence=data.confidence,
        warnings=data.warnings,
    )


def _apply_overrides(data: InvoiceData, request: ConversionRequest) -> InvoiceData:
    """Apply user overrides to extracted data."""
    if request.invoice_number:
        data.invoice_number = request.invoice_number
    if request.invoice_date:
        data.invoice_date = request.invoice_date
    if request.due_date:
        data.due_date = request.due_date
    if request.delivery_date:
        data.delivery_date = request.delivery_date

    # Seller overrides
    if request.seller_name or request.seller_street or request.seller_postal_code or request.seller_city:
        if not data.seller:
            data.seller = Address(name="")
        if request.seller_name:
            data.seller.name = request.seller_name
        if request.seller_street:
            data.seller.street = request.seller_street
        if request.seller_postal_code:
            data.seller.postal_code = request.seller_postal_code
        if request.seller_city:
            data.seller.city = request.seller_city

    if request.seller_vat_id:
        data.seller_vat_id = request.seller_vat_id

    # Buyer overrides
    if request.buyer_name or request.buyer_street or request.buyer_postal_code or request.buyer_city:
        if not data.buyer:
            data.buyer = Address(name="")
        if request.buyer_name:
            data.buyer.name = request.buyer_name
        if request.buyer_street:
            data.buyer.street = request.buyer_street
        if request.buyer_postal_code:
            data.buyer.postal_code = request.buyer_postal_code
        if request.buyer_city:
            data.buyer.city = request.buyer_city

    if request.buyer_reference:
        data.buyer_reference = request.buyer_reference

    # Amount overrides
    if request.net_amount is not None:
        data.net_amount = request.net_amount
    if request.vat_amount is not None:
        data.vat_amount = request.vat_amount
    if request.gross_amount is not None:
        data.gross_amount = request.gross_amount

    # Bank details
    if request.iban:
        data.iban = request.iban
    if request.bic:
        data.bic = request.bic
    if request.leitweg_id:
        data.leitweg_id = request.leitweg_id

    return data


@router.get("/status", response_model=ConversionStatusResponse)
async def get_conversion_status() -> ConversionStatusResponse:
    """
    Get conversion service status and capabilities.

    Returns available features and supported formats.
    """
    return ConversionStatusResponse(
        ocr_available=conversion_service.ocr_available,
        ai_available=conversion_service.ai_available,
        supported_formats=list(OutputFormat),
        supported_profiles=list(ZUGFeRDProfile),
    )


@router.post("/preview", response_model=PreviewResponse)
async def preview_extraction(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
) -> PreviewResponse:
    """
    Preview extracted data from a PDF without converting.

    Allows users to see what data was extracted before conversion.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nur PDF-Dateien werden unterstuetzt",
        )

    # Read file
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Datei zu gross. Maximum: 10 MB",
        )

    # Check if scanned
    is_scanned = conversion_service.ocr_service.is_scanned_pdf(content)

    # Extract data (using AI if available)
    try:
        data = await conversion_service.preview_extraction_async(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Fehler bei der Datenextraktion: {str(e)}",
        )

    return PreviewResponse(
        extracted_data=_invoice_data_to_schema(data),
        ocr_used=is_scanned,
        ocr_available=conversion_service.ocr_available,
        ai_used=conversion_service.ai_available,
    )


@router.post("/", response_model=ConversionResponse)
async def convert_pdf(
    file: UploadFile = File(...),
    output_format: OutputFormat = Form(OutputFormat.XRECHNUNG),
    zugferd_profile: ZUGFeRDProfile = Form(ZUGFeRDProfile.EN16931),
    embed_in_pdf: bool = Form(True),
    # Optional overrides
    invoice_number: Optional[str] = Form(None),
    seller_vat_id: Optional[str] = Form(None),
    buyer_reference: Optional[str] = Form(None),
    leitweg_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
) -> ConversionResponse:
    """
    Convert a PDF invoice to XRechnung or ZUGFeRD format.

    Requires authentication. Usage is counted against plan limits.
    """
    # Check conversion limits
    try:
        await check_user_conversion_limit(current_user)
    except UsageLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nur PDF-Dateien werden unterstuetzt",
        )

    # Read file
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Datei zu gross. Maximum: 10 MB",
        )

    # Build conversion request
    request = ConversionRequest(
        output_format=output_format,
        zugferd_profile=zugferd_profile,
        embed_in_pdf=embed_in_pdf,
        invoice_number=invoice_number,
        seller_vat_id=seller_vat_id,
        buyer_reference=buyer_reference,
        leitweg_id=leitweg_id,
    )

    # Perform conversion (using AI-enhanced extraction if available)
    result = await conversion_service.convert_async(
        pdf_content=content,
        output_format=ServiceOutputFormat(output_format.value),
        zugferd_profile=ServiceZUGFeRDProfile(zugferd_profile.value),
        embed_in_pdf=embed_in_pdf,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.error or "Konvertierung fehlgeschlagen",
        )

    # Store result for download
    conversion_id = str(uuid.uuid4())
    content_type = (
        "application/pdf"
        if output_format == OutputFormat.ZUGFERD and embed_in_pdf
        else "application/xml"
    )
    _conversion_cache[conversion_id] = (result.content, result.filename, content_type, result.xml_content)

    # Auto-validate the generated XML
    validation_result = None
    if result.xml_content:
        try:
            from app.services.validator.xrechnung import XRechnungValidator

            validator = XRechnungValidator()
            val_response = await validator.validate(
                content=result.xml_content,
                filename=result.filename,
                user_id=current_user.id if current_user else None,
            )

            # Convert ValidationResponse to ValidationResultSchema
            validation_result = ValidationResultSchema(
                is_valid=val_response.is_valid,
                error_count=val_response.error_count,
                warning_count=val_response.warning_count,
                info_count=val_response.info_count,
                errors=[
                    ValidationErrorSchema(
                        severity=e.severity.value,
                        code=e.code,
                        message_de=e.message_de,
                        message_en=e.message_en,
                        location=e.location,
                        suggestion=e.suggestion,
                    )
                    for e in val_response.errors
                ],
                warnings=[
                    ValidationErrorSchema(
                        severity=w.severity.value,
                        code=w.code,
                        message_de=w.message_de,
                        message_en=w.message_en,
                        location=w.location,
                        suggestion=w.suggestion,
                    )
                    for w in val_response.warnings
                ],
                infos=[
                    ValidationErrorSchema(
                        severity=i.severity.value,
                        code=i.code,
                        message_de=i.message_de,
                        message_en=i.message_en,
                        location=i.location,
                        suggestion=i.suggestion,
                    )
                    for i in val_response.infos
                ],
                validator_version=val_response.validator_version,
                processing_time_ms=val_response.processing_time_ms,
            )
        except Exception as e:
            logger.warning(f"Auto-validation failed: {e}")
            # Don't fail conversion if validation fails

    return ConversionResponse(
        success=True,
        conversion_id=conversion_id,
        filename=result.filename,
        output_format=output_format,
        extracted_data=_invoice_data_to_schema(result.extracted_data),
        warnings=result.warnings,
        validation_result=validation_result,
    )


@router.get("/{conversion_id}/download")
async def download_converted_file(
    conversion_id: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Download a converted file.

    The conversion_id is returned from the convert endpoint.
    """
    if conversion_id not in _conversion_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Konvertierung nicht gefunden oder abgelaufen",
        )

    content, filename, content_type, _ = _conversion_cache[conversion_id]

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{conversion_id}/preview-xml")
async def preview_xml(
    conversion_id: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Preview the XML content of a conversion.

    Returns the raw XML for XRechnung, or the XML that was embedded for ZUGFeRD.
    """
    if conversion_id not in _conversion_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Konvertierung nicht gefunden oder abgelaufen",
        )

    _, _, _, xml_content = _conversion_cache[conversion_id]

    if not xml_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine XML-Daten verfuegbar",
        )

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Type": "application/xml; charset=utf-8",
        },
    )


@router.post("/batch", response_model=list[ConversionResponse])
async def convert_batch(
    files: list[UploadFile] = File(...),
    output_format: OutputFormat = Form(OutputFormat.XRECHNUNG),
    zugferd_profile: ZUGFeRDProfile = Form(ZUGFeRDProfile.EN16931),
    current_user: User = Depends(get_current_user),
) -> list[ConversionResponse]:
    """
    Convert multiple PDF invoices in batch.

    Requires Starter plan or higher.
    """
    # Check batch limit (max 10 files)
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximal 10 Dateien pro Batch",
        )

    # Check plan allows batch
    if current_user.plan.value == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Batch-Upload erfordert Starter-Plan oder hoeher",
        )

    results = []
    for file in files:
        try:
            # Check limits for each file
            await check_user_conversion_limit(current_user)

            if not file.filename or not file.filename.lower().endswith(".pdf"):
                results.append(
                    ConversionResponse(
                        success=False,
                        conversion_id="",
                        filename=file.filename or "unknown",
                        output_format=output_format,
                        extracted_data=ExtractedDataSchema(),
                        error="Nur PDF-Dateien werden unterstuetzt",
                    )
                )
                continue

            content = await file.read()
            result = conversion_service.convert(
                pdf_content=content,
                output_format=ServiceOutputFormat(output_format.value),
                zugferd_profile=ServiceZUGFeRDProfile(zugferd_profile.value),
            )

            if result.success:
                conversion_id = str(uuid.uuid4())
                content_type = (
                    "application/pdf"
                    if output_format == OutputFormat.ZUGFERD
                    else "application/xml"
                )
                _conversion_cache[conversion_id] = (
                    result.content,
                    result.filename,
                    content_type,
                    result.xml_content,
                )

                results.append(
                    ConversionResponse(
                        success=True,
                        conversion_id=conversion_id,
                        filename=result.filename,
                        output_format=output_format,
                        extracted_data=_invoice_data_to_schema(result.extracted_data),
                        warnings=result.warnings,
                    )
                )
            else:
                results.append(
                    ConversionResponse(
                        success=False,
                        conversion_id="",
                        filename=file.filename or "unknown",
                        output_format=output_format,
                        extracted_data=_invoice_data_to_schema(result.extracted_data),
                        warnings=result.warnings,
                        error=result.error,
                    )
                )

        except UsageLimitError as e:
            results.append(
                ConversionResponse(
                    success=False,
                    conversion_id="",
                    filename=file.filename or "unknown",
                    output_format=output_format,
                    extracted_data=ExtractedDataSchema(),
                    error=str(e),
                )
            )
            break  # Stop processing if limit reached

    return results


@router.post("/{conversion_id}/send-email", response_model=SendInvoiceEmailResponse)
async def send_invoice_email(
    conversion_id: str,
    request: SendInvoiceEmailRequest,
    current_user: User = Depends(get_current_user),
) -> SendInvoiceEmailResponse:
    """
    Send converted invoice via email.

    Sends the converted file to the specified recipient and/or user's own email.
    """
    from app.services.email.service import email_service

    # Check if conversion exists
    if conversion_id not in _conversion_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Konvertierung nicht gefunden oder abgelaufen",
        )

    # Get cached conversion data
    content, filename, content_type, xml_content = _conversion_cache[conversion_id]

    # Need at least one recipient
    if not request.recipient_email and not request.send_copy_to_self:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitte geben Sie eine Empfaenger-E-Mail an oder waehlen Sie 'Kopie an mich senden'",
        )

    # Extract invoice details from XML for email
    invoice_number = "Unbekannt"
    invoice_date = "Unbekannt"
    gross_amount = "0.00"
    currency = "EUR"
    output_format = "XRechnung" if filename.endswith(".xml") else "ZUGFeRD"

    # Try to parse invoice data from XML
    if xml_content:
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            ns = {
                'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
                'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
            }

            # Try UBL (XRechnung)
            inv_id = root.find('.//cbc:ID', ns)
            if inv_id is not None and inv_id.text:
                invoice_number = inv_id.text

            issue_date = root.find('.//cbc:IssueDate', ns)
            if issue_date is not None and issue_date.text:
                invoice_date = issue_date.text

            payable = root.find('.//cbc:PayableAmount', ns)
            if payable is not None and payable.text:
                gross_amount = payable.text
                if payable.get('currencyID'):
                    currency = payable.get('currencyID')

            # Try CII (ZUGFeRD) if UBL didn't work
            if invoice_number == "Unbekannt":
                inv_id = root.find('.//ram:ID', ns)
                if inv_id is not None and inv_id.text:
                    invoice_number = inv_id.text

        except Exception as e:
            logger.warning(f"Could not parse invoice XML for email: {e}")

    # Prepare recipients list
    recipients = []
    if request.recipient_email:
        recipients.append(request.recipient_email)
    if request.send_copy_to_self and current_user.email:
        if current_user.email not in recipients:
            recipients.append(current_user.email)

    # Send emails
    emails_sent = 0
    sender_name = current_user.full_name or current_user.company_name or "RechnungsChecker Benutzer"

    for recipient in recipients:
        success = await email_service.send_invoice_email(
            to=recipient,
            sender_name=sender_name,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            gross_amount=gross_amount,
            currency=currency,
            output_format=output_format,
            file_content=content,
            filename=filename,
        )
        if success:
            emails_sent += 1

    if emails_sent == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="E-Mail konnte nicht gesendet werden. Bitte versuchen Sie es erneut.",
        )

    message = (
        f"E-Mail erfolgreich an {emails_sent} Empfaenger gesendet"
        if emails_sent > 1
        else "E-Mail erfolgreich gesendet"
    )

    return SendInvoiceEmailResponse(
        success=True,
        message=message,
        emails_sent=emails_sent,
    )
