"""ZUGFeRD PDF validation service.

ZUGFeRD (Zentraler User Guide des Forums elektronische Rechnung Deutschland)
is a hybrid format that embeds structured XML data within a PDF/A-3 document.
"""

import hashlib
import logging
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

import fitz  # PyMuPDF

from app.core.exceptions import FileProcessingError, ValidationError
from app.schemas.validation import (
    ValidationError as ValidationErrorSchema,
    ValidationResponse,
    ValidationSeverity,
)
from app.services.validator.kosit import KoSITValidator
from app.services.validator.error_messages import get_german_message

logger = logging.getLogger(__name__)


class ZUGFeRDProfile(str, Enum):
    """ZUGFeRD/Factur-X profile levels."""

    MINIMUM = "MINIMUM"
    BASIC_WL = "BASIC-WL"
    BASIC = "BASIC"
    EN16931 = "EN16931"  # Also known as COMFORT
    EXTENDED = "EXTENDED"
    XRECHNUNG = "XRECHNUNG"
    UNKNOWN = "UNKNOWN"


@dataclass
class ZUGFeRDExtractionResult:
    """Result of XML extraction from ZUGFeRD PDF."""

    xml_content: bytes
    profile: ZUGFeRDProfile
    version: str | None
    filename: str | None  # Original embedded filename


class ZUGFeRDExtractor:
    """Extracts embedded XML from ZUGFeRD/Factur-X PDFs."""

    # Known attachment names for ZUGFeRD/Factur-X XML
    KNOWN_XML_NAMES = [
        "factur-x.xml",
        "zugferd-invoice.xml",
        "xrechnung.xml",
        "ZUGFeRD-invoice.xml",
    ]

    def extract_xml(self, pdf_content: bytes) -> ZUGFeRDExtractionResult:
        """Extract embedded XML from a ZUGFeRD PDF.

        Args:
            pdf_content: Raw PDF file content

        Returns:
            ZUGFeRDExtractionResult with extracted XML and metadata

        Raises:
            FileProcessingError: If PDF cannot be read or has no embedded XML
        """
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            raise FileProcessingError(
                "Die PDF-Datei konnte nicht geöffnet werden.",
                details={"error": str(e)},
            )

        try:
            # Get embedded files
            embedded_files = self._get_embedded_files(doc)

            if not embedded_files:
                raise FileProcessingError(
                    "Keine eingebettete XML-Datei gefunden. "
                    "Dies ist möglicherweise keine ZUGFeRD/Factur-X-Rechnung.",
                )

            # Find the invoice XML
            xml_content, filename = self._find_invoice_xml(embedded_files)

            if xml_content is None:
                raise FileProcessingError(
                    "Keine ZUGFeRD/Factur-X XML-Rechnung in der PDF gefunden. "
                    f"Gefundene Anhänge: {list(embedded_files.keys())}",
                )

            # Detect profile and version
            profile, version = self._detect_profile(xml_content)

            return ZUGFeRDExtractionResult(
                xml_content=xml_content,
                profile=profile,
                version=version,
                filename=filename,
            )
        finally:
            doc.close()

    def _get_embedded_files(self, doc: fitz.Document) -> dict[str, bytes]:
        """Get all embedded files from PDF."""
        embedded = {}

        # Method 1: Check PDF embedded files (EmbeddedFiles)
        try:
            if doc.embfile_count() > 0:
                for i in range(doc.embfile_count()):
                    info = doc.embfile_info(i)
                    name = info.get("name", f"attachment_{i}")
                    content = doc.embfile_get(i)
                    embedded[name] = content
                    logger.debug(f"Found embedded file: {name} ({len(content)} bytes)")
        except Exception as e:
            logger.warning(f"Error reading embedded files: {e}")

        # Method 2: Check for XML in associated files (PDF 2.0 AF)
        try:
            # PyMuPDF may store these differently
            catalog = doc.pdf_catalog()
            if catalog:
                # Additional extraction logic if needed
                pass
        except Exception as e:
            logger.debug(f"No catalog AF entries: {e}")

        return embedded

    def _find_invoice_xml(
        self, embedded_files: dict[str, bytes]
    ) -> tuple[bytes | None, str | None]:
        """Find the invoice XML among embedded files."""
        # First, try known filenames
        for name in self.KNOWN_XML_NAMES:
            for filename, content in embedded_files.items():
                if filename.lower() == name.lower():
                    return content, filename

        # Then, try any XML file
        for filename, content in embedded_files.items():
            if filename.lower().endswith(".xml"):
                # Verify it looks like an invoice XML
                if self._is_invoice_xml(content):
                    return content, filename

        return None, None

    def _is_invoice_xml(self, content: bytes) -> bool:
        """Check if content appears to be an invoice XML."""
        try:
            # Check for common invoice XML markers
            content_str = content.decode("utf-8", errors="ignore").lower()
            invoice_markers = [
                "crossindustryinvoice",
                "invoice",
                "factur",
                "zugferd",
                "cii:",
                "rsm:",
                "ram:",
            ]
            return any(marker in content_str for marker in invoice_markers)
        except Exception:
            return False

    def _detect_profile(self, xml_content: bytes) -> tuple[ZUGFeRDProfile, str | None]:
        """Detect ZUGFeRD profile and version from XML content."""
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return ZUGFeRDProfile.UNKNOWN, None

        # Look for GuidelineSpecifiedDocumentContextParameter
        # which contains the profile information
        namespaces = {
            "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
            "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        }

        # Try to find the guideline ID
        guideline_id = None
        for elem in root.iter():
            if "GuidelineSpecifiedDocumentContextParameter" in elem.tag:
                for child in elem:
                    if "ID" in child.tag and child.text:
                        guideline_id = child.text
                        break

        if not guideline_id:
            # Try alternative path
            for elem in root.iter():
                if "ID" in elem.tag and elem.text:
                    text = elem.text.lower()
                    if "factur-x" in text or "zugferd" in text or "xrechnung" in text:
                        guideline_id = elem.text
                        break

        if not guideline_id:
            return ZUGFeRDProfile.UNKNOWN, None

        # Detect profile from guideline ID
        guideline_lower = guideline_id.lower()
        version = None

        # Extract version
        if "2.1" in guideline_id:
            version = "2.1"
        elif "2.2" in guideline_id:
            version = "2.2"
        elif "2.0" in guideline_id:
            version = "2.0"
        elif "1.0" in guideline_id:
            version = "1.0"

        # Detect profile
        if "xrechnung" in guideline_lower:
            return ZUGFeRDProfile.XRECHNUNG, version
        elif "extended" in guideline_lower:
            return ZUGFeRDProfile.EXTENDED, version
        elif "en16931" in guideline_lower or "comfort" in guideline_lower:
            return ZUGFeRDProfile.EN16931, version
        elif "basic-wl" in guideline_lower or "basicwl" in guideline_lower:
            return ZUGFeRDProfile.BASIC_WL, version
        elif "basic" in guideline_lower:
            return ZUGFeRDProfile.BASIC, version
        elif "minimum" in guideline_lower:
            return ZUGFeRDProfile.MINIMUM, version

        return ZUGFeRDProfile.UNKNOWN, version


class ZUGFeRDValidator:
    """Service for validating ZUGFeRD/Factur-X PDF invoices."""

    # Profiles that are considered deprecated or insufficient
    DEPRECATED_PROFILES = [ZUGFeRDProfile.MINIMUM, ZUGFeRDProfile.BASIC_WL]

    def __init__(self) -> None:
        """Initialize the ZUGFeRD validator."""
        self.extractor = ZUGFeRDExtractor()
        self.kosit = KoSITValidator()

    async def validate(
        self,
        content: bytes,
        filename: str,
        user_id: UUID | None = None,
    ) -> ValidationResponse:
        """Validate a ZUGFeRD/Factur-X PDF file.

        Args:
            content: Raw PDF file content
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

        # Extract embedded XML
        extraction = self.extractor.extract_xml(content)

        logger.info(
            f"Extracted ZUGFeRD XML: profile={extraction.profile}, "
            f"version={extraction.version}, filename={extraction.filename}"
        )

        # Write XML to temp file for KoSIT validation
        with tempfile.NamedTemporaryFile(
            suffix=".xml", delete=False, mode="wb"
        ) as tmp:
            tmp.write(extraction.xml_content)
            tmp_path = Path(tmp.name)

        try:
            # Run KoSIT validation on extracted XML
            result = await self.kosit.validate_file(tmp_path)

            # Build response
            response = self._build_response(
                validation_id=validation_id,
                file_hash=file_hash,
                file_size=len(content),
                extraction=extraction,
                kosit_result=result,
            )

            # Add profile-specific warnings
            self._add_profile_warnings(response, extraction.profile)

            return response
        finally:
            # Clean up temp files
            try:
                tmp_path.unlink()
                report_path = tmp_path.parent / f"{tmp_path.stem}-report.xml"
                if report_path.exists():
                    report_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to clean up temp files: {e}")

    def _build_response(
        self,
        validation_id: UUID,
        file_hash: str,
        file_size: int,
        extraction: ZUGFeRDExtractionResult,
        kosit_result,
    ) -> ValidationResponse:
        """Build validation response from extraction and KoSIT result."""
        from app.services.validator.kosit import KoSITResult

        errors: list[ValidationErrorSchema] = []
        warnings: list[ValidationErrorSchema] = []
        infos: list[ValidationErrorSchema] = []

        for msg in kosit_result.messages:
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
            is_valid=kosit_result.is_valid and len(errors) == 0,
            file_type="zugferd",
            file_hash=file_hash,
            error_count=len(errors),
            warning_count=len(warnings),
            info_count=len(infos),
            errors=errors,
            warnings=warnings,
            infos=infos,
            zugferd_profile=extraction.profile.value,
            xrechnung_version=kosit_result.xrechnung_version,
            validator_version=KoSITValidator.VALIDATOR_VERSION,
            processing_time_ms=kosit_result.processing_time_ms,
            validated_at=datetime.utcnow(),
            report_url=None,
        )

    def _add_profile_warnings(
        self, response: ValidationResponse, profile: ZUGFeRDProfile
    ) -> None:
        """Add warnings for deprecated or limited profiles."""
        if profile in self.DEPRECATED_PROFILES:
            warning = ValidationErrorSchema(
                severity=ValidationSeverity.WARNING,
                code="ZUGFERD-PROFILE-DEPRECATED",
                message_de=(
                    f"Das Profil {profile.value} ist veraltet und bietet "
                    "eingeschränkte Funktionalität. Empfohlen wird mindestens "
                    "das Profil BASIC oder EN16931."
                ),
                message_en=(
                    f"Profile {profile.value} is deprecated and provides "
                    "limited functionality."
                ),
                location=None,
                suggestion="Verwenden Sie mindestens das Profil BASIC oder EN16931.",
            )
            response.warnings.append(warning)
            response.warning_count += 1

        if profile == ZUGFeRDProfile.UNKNOWN:
            warning = ValidationErrorSchema(
                severity=ValidationSeverity.WARNING,
                code="ZUGFERD-PROFILE-UNKNOWN",
                message_de=(
                    "Das ZUGFeRD-Profil konnte nicht erkannt werden. "
                    "Die Validierung erfolgt nach allgemeinen Regeln."
                ),
                message_en="ZUGFeRD profile could not be detected.",
                location=None,
                suggestion=None,
            )
            response.warnings.append(warning)
            response.warning_count += 1

    def _get_suggestion(self, code: str) -> str | None:
        """Get fix suggestion for an error code."""
        suggestions = {
            # ZUGFeRD-specific rules
            "ZF-001": "Das eingebettete XML ist kein gueltiges ZUGFeRD/Factur-X Format.",
            "ZF-002": "Die PDF/A-3 Konformitaet ist fuer ZUGFeRD erforderlich.",
            "ZF-003": "Das XML muss als 'Alternative' eingebettet sein (AF-Beziehung).",
            "ZUGFERD-PROFILE-DEPRECATED": "Verwenden Sie mindestens das Profil BASIC oder EN16931.",
            "ZUGFERD-PROFILE-UNKNOWN": "Stellen Sie sicher, dass das Profil korrekt angegeben ist.",
            # CII specific rules
            "CII-SR-001": "Pruefen Sie die CII-Namensraeume im XML.",
            "CII-SR-002": "Das CrossIndustryInvoice-Element muss vorhanden sein.",
            "CII-SR-003": "Entfernen Sie nicht erlaubte XML-Erweiterungen.",
            "CII-SR-004": "Pruefen Sie die CII-Elementreihenfolge.",
            "CII-SR-005": "Verwenden Sie nur erlaubte CII-Elemente.",
            # BR-DE German-specific rules
            "BR-DE-01": "Fuegen Sie eine Leitweg-ID im Format XX-XXXX-XXXX-XX hinzu.",
            "BR-DE-02": "Geben Sie IBAN und optional BIC des Verkaeufers an.",
            "BR-DE-03": "Ergaenzen Sie die Zahlungsbedingungen oder das Faelligkeitsdatum.",
            "BR-DE-04": "Tragen Sie eine gueltige USt-IdNr. ein (DE + 9 Ziffern).",
            "BR-DE-05": "Geben Sie einen Ansprechpartner beim Verkaeufer an.",
            "BR-DE-06": "Ergaenzen Sie Telefon oder E-Mail des Verkaeufers.",
            "BR-DE-07": "Fuegen Sie die Telefonnummer des Verkaeufers hinzu.",
            "BR-DE-08": "Pruefen Sie das IBAN-Format (DE + 20 Zeichen).",
            "BR-DE-09": "Geben Sie ein Faelligkeitsdatum oder Zahlungsziel an.",
            "BR-DE-10": "Fuegen Sie den BIC der Bank hinzu (8 oder 11 Zeichen).",
            "BR-DE-13": "Pruefen Sie die Berechnung: MwSt-Betrag = Netto x MwSt-Satz.",
            "BR-DE-14": "Tragen Sie eine eindeutige Rechnungsnummer ein.",
            "BR-DE-15": "Fuegen Sie das Rechnungsdatum hinzu.",
            "BR-DE-16": "Fuegen Sie mindestens eine Rechnungsposition hinzu.",
            "BR-DE-17": "Geben Sie die Menge fuer jede Position an.",
            "BR-DE-18": "Geben Sie den Einzelpreis fuer jede Position an.",
            "BR-DE-19": "Fuegen Sie eine Beschreibung fuer jede Position hinzu.",
            "BR-DE-21": "Pruefen Sie das Leitweg-ID Format: XX-XXXX-XXXX-XX.",
            # BR Core rules
            "BR-01": "Tragen Sie eine eindeutige Rechnungsnummer ein.",
            "BR-02": "Fuegen Sie das Rechnungsdatum im Format JJJJ-MM-TT hinzu.",
            "BR-03": "Waehlen Sie einen gueltigen Rechnungstyp (380, 381, 384).",
            "BR-04": "Geben Sie die Rechnungswaehrung an (z.B. EUR).",
            "BR-05": "Die Waehrung muss als ISO 4217 Code angegeben werden.",
            "BR-06": "Tragen Sie den Namen des Verkaeufers ein.",
            "BR-07": "Tragen Sie den Namen des Kaeufers ein.",
            "BR-08": "Geben Sie die Postanschrift des Verkaeufers an.",
            "BR-09": "Fuegen Sie das Land des Verkaeufers als ISO-Code hinzu.",
            "BR-10": "Geben Sie die Postanschrift des Kaeufers an.",
            "BR-11": "Fuegen Sie das Land des Kaeufers als ISO-Code hinzu.",
            "BR-12": "Der Bruttobetrag muss angegeben werden.",
            "BR-13": "Der zu zahlende Betrag muss angegeben werden.",
            "BR-14": "Fuegen Sie mindestens eine Rechnungsposition hinzu.",
            "BR-16": "Geben Sie die Menge fuer die Position an.",
            "BR-17": "Der Nettopreis der Position muss angegeben werden.",
            # BR-CO Calculation rules
            "BR-CO-03": "Pruefen Sie: MwSt-Betrag pro Kategorie = Netto x MwSt-Satz.",
            "BR-CO-10": "Pruefen Sie: Nettosumme + MwSt-Summe = Bruttosumme.",
            "BR-CO-13": "Pruefen Sie: Positionsnetto = Menge x Einzelpreis.",
            "BR-CO-15": "Die Nettosumme muss die Summe aller Positionen sein.",
            "BR-CO-16": "Die MwSt-Summe muss die Summe aller MwSt-Betraege sein.",
            "BR-CO-25": "Bei positivem Zahlbetrag muss entweder das Faelligkeitsdatum oder Zahlungsbedingungen angegeben werden.",
            # PEPPOL rules
            "PEPPOL-EN16931-R120": "Pruefen Sie: Positionsnetto = Menge × (Einzelpreis / Preisbasis) + Zuschlage - Abzuege.",
            "PEPPOL-EN16931-R121": "Die Summe der Positionsnettobetraege muss dem Gesamtnetto entsprechen.",
            # BR-S Standard rate VAT rules
            "BR-S-01": "Steuerkategorie S erfordert MwSt-Satz > 0%.",
            "BR-S-02": "Geben Sie den MwSt-Satz fuer Steuerkategorie S an.",
            # BR-AE Reverse charge rules
            "BR-AE-01": "Steuerkategorie AE (Reverse Charge) erfordert MwSt = 0%.",
            "BR-AE-02": "Bei Reverse Charge muss der Grund angegeben werden.",
            # BR-E Exempt VAT rules
            "BR-E-01": "Steuerkategorie E (steuerbefreit) erfordert MwSt = 0%.",
            "BR-E-02": "Geben Sie den Grund fuer die Steuerbefreiung an.",
            # BR-Z Zero rate rules
            "BR-Z-01": "Steuerkategorie Z (Nullsatz) erfordert MwSt = 0%.",
            # BR-G Export rules
            "BR-G-01": "Steuerkategorie G (Export) erfordert MwSt = 0%.",
        }
        return suggestions.get(code)
