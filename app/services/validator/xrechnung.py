"""XRechnung validation service."""

import hashlib
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.core.exceptions import FileProcessingError, ValidationError
from app.schemas.validation import (
    ValidationError as ValidationErrorSchema,
    ValidationResponse,
    ValidationSeverity,
)
from app.services.validator.kosit import KoSITValidator, KoSITResult
from app.services.validator.error_messages import get_german_message

logger = logging.getLogger(__name__)


class XRechnungValidator:
    """Service for validating XRechnung XML files."""

    def __init__(self) -> None:
        """Initialize the XRechnung validator."""
        self.kosit = KoSITValidator()

    async def validate(
        self,
        content: bytes,
        filename: str,
        user_id: UUID | None = None,
    ) -> ValidationResponse:
        """Validate an XRechnung XML file.

        Args:
            content: Raw XML file content
            filename: Original filename
            user_id: Optional user ID for logging

        Returns:
            ValidationResponse with validation results

        Raises:
            ValidationError: If validation cannot be performed
            FileProcessingError: If file cannot be processed
        """
        validation_id = uuid4()
        file_hash = hashlib.sha256(content).hexdigest()

        # Validate it's actually XML
        if not self._is_valid_xml(content):
            raise FileProcessingError(
                "Die Datei ist kein gültiges XML.",
                details={"filename": filename},
            )

        # Write to temp file for KoSIT
        with tempfile.NamedTemporaryFile(
            suffix=".xml", delete=False, mode="wb"
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # Run validation
            result = await self.kosit.validate_file(tmp_path)

            # Convert to response
            return self._build_response(
                validation_id=validation_id,
                file_hash=file_hash,
                file_size=len(content),
                result=result,
            )
        finally:
            # Clean up temp file
            try:
                tmp_path.unlink()
                # Also clean up report file if created
                report_path = tmp_path.parent / f"{tmp_path.stem}-report.xml"
                if report_path.exists():
                    report_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to clean up temp files: {e}")

    def _is_valid_xml(self, content: bytes) -> bool:
        """Check if content is valid XML."""
        import xml.etree.ElementTree as ET

        try:
            ET.fromstring(content)
            return True
        except ET.ParseError:
            return False

    def _build_response(
        self,
        validation_id: UUID,
        file_hash: str,
        file_size: int,
        result: KoSITResult,
    ) -> ValidationResponse:
        """Build validation response from KoSIT result."""
        errors: list[ValidationErrorSchema] = []
        warnings: list[ValidationErrorSchema] = []
        infos: list[ValidationErrorSchema] = []

        for msg in result.messages:
            error_schema = ValidationErrorSchema(
                severity=ValidationSeverity(msg.severity),
                code=msg.code,
                message_de=get_german_message(msg.code, msg.text),
                message_en=msg.text if msg.text else None,
                location=msg.location,
                suggestion=self._get_suggestion(msg.code),
            )

            if msg.severity == "error":
                errors.append(error_schema)
            elif msg.severity == "warning":
                warnings.append(error_schema)
            else:
                infos.append(error_schema)

        return ValidationResponse(
            id=validation_id,
            is_valid=result.is_valid,
            file_type="xrechnung",
            file_hash=file_hash,
            error_count=len(errors),
            warning_count=len(warnings),
            info_count=len(infos),
            errors=errors,
            warnings=warnings,
            infos=infos,
            xrechnung_version=result.xrechnung_version,
            validator_version=KoSITValidator.VALIDATOR_VERSION,
            processing_time_ms=result.processing_time_ms,
            validated_at=datetime.utcnow(),
            report_url=None,  # Will be set by API layer
        )

    def _get_suggestion(self, code: str) -> str | None:
        """Get fix suggestion for an error code."""
        suggestions = {
            "BR-DE-01": "Fügen Sie eine Leitweg-ID hinzu.",
            "BR-DE-02": "Geben Sie die Bankverbindung des Verkäufers an.",
            "BR-DE-03": "Ergänzen Sie die Zahlungsbedingungen.",
            "BR-DE-04": "Fügen Sie eine gültige Umsatzsteuer-ID hinzu.",
            "BR-DE-05": "Geben Sie den Kontakt des Verkäufers an.",
            "BR-DE-06": "Ergänzen Sie die E-Mail-Adresse des Verkäufers.",
            "BR-DE-07": "Fügen Sie die Telefonnummer des Verkäufers hinzu.",
            "BR-DE-08": "Geben Sie ein gültiges IBAN-Format an.",
            "BR-DE-09": "Das Fälligkeitsdatum ist erforderlich.",
            "BR-DE-10": "Fügen Sie die Bankleitzahl (BIC) hinzu.",
            "BR-DE-11": "Geben Sie den Verwendungszweck an.",
            "BR-DE-13": "Überprüfen Sie den Umsatzsteuerbetrag.",
            "BR-DE-14": "Die Rechnungsnummer darf nicht leer sein.",
            "BR-DE-15": "Das Rechnungsdatum ist erforderlich.",
            "BR-DE-16": "Mindestens eine Rechnungsposition ist erforderlich.",
            "BR-DE-17": "Die Positionsmenge muss angegeben werden.",
            "BR-DE-18": "Der Einzelpreis muss angegeben werden.",
            "BR-DE-19": "Die Positionsbeschreibung ist erforderlich.",
            "BR-DE-21": "Überprüfen Sie das Format der Leitweg-ID.",
        }
        return suggestions.get(code)
