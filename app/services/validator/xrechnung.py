"""XRechnung validation service."""

import hashlib
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.schemas.validation import (
    ValidationError as ValidationErrorSchema,
)
from app.schemas.validation import (
    ValidationResponse,
    ValidationSeverity,
)
from app.services.validator.error_messages import get_german_message
from app.services.validator.kosit import KoSITResult, KoSITValidator

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
        is_valid_xml, xml_error = self._is_valid_xml(content)
        if not is_valid_xml:
            # Return validation result with XML parsing error
            return ValidationResponse(
                id=validation_id,
                is_valid=False,
                file_type="xrechnung",
                file_hash=file_hash,
                error_count=1,
                warning_count=0,
                info_count=0,
                errors=[
                    ValidationErrorSchema(
                        severity=ValidationSeverity.ERROR,
                        code="XML-PARSE-ERROR",
                        message_de=f"Die Datei ist kein gültiges XML: {xml_error}",
                        message_en=f"The file is not valid XML: {xml_error}",
                        location=None,
                        suggestion="Überprüfen Sie die XML-Struktur auf fehlende oder falsch geschlossene Tags.",
                    )
                ],
                warnings=[],
                infos=[],
                xrechnung_version=None,
                validator_version=KoSITValidator.VALIDATOR_VERSION,
                processing_time_ms=0,
                validated_at=datetime.now(UTC).replace(tzinfo=None),
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

    def _is_valid_xml(self, content: bytes) -> tuple[bool, str | None]:
        """Check if content is valid XML.

        Returns:
            Tuple of (is_valid, error_message)
        """
        import xml.etree.ElementTree as ET

        try:
            ET.fromstring(content)
            return True, None
        except ET.ParseError as e:
            return False, str(e)

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
            validated_at=datetime.now(UTC).replace(tzinfo=None),
            report_url=None,  # Will be set by API layer
        )

    def _get_suggestion(self, code: str) -> str | None:
        """Get fix suggestion for an error code."""
        suggestions = {
            # BR-DE German-specific rules
            "BR-DE-01": (
                "Fuegen Sie eine Leitweg-ID im Format XX-XXXX-XXXX-XX hinzu "
                "(z.B. 04011000-1234512345-06)."
            ),
            "BR-DE-02": "Geben Sie IBAN und optional BIC des Verkaeufers an.",
            "BR-DE-03": "Ergaenzen Sie die Zahlungsbedingungen oder das Faelligkeitsdatum.",
            "BR-DE-04": "Tragen Sie eine gueltige USt-IdNr. ein (DE + 9 Ziffern, z.B. DE123456789).",
            "BR-DE-05": "Geben Sie einen Ansprechpartner beim Verkaeufer an.",
            "BR-DE-06": "Ergaenzen Sie Telefon oder E-Mail des Verkaeufers.",
            "BR-DE-07": "Fuegen Sie die Telefonnummer des Verkaeufers hinzu.",
            "BR-DE-08": "Pruefen Sie das IBAN-Format (DE + 20 Zeichen, z.B. DE89370400440532013000).",
            "BR-DE-09": "Geben Sie ein Faelligkeitsdatum oder Zahlungsziel an.",
            "BR-DE-10": "Fuegen Sie den BIC der Bank hinzu (8 oder 11 Zeichen).",
            "BR-DE-11": "Geben Sie einen Verwendungszweck fuer die Zahlung an.",
            "BR-DE-13": "Pruefen Sie die Berechnung: MwSt-Betrag = Netto × MwSt-Satz.",
            "BR-DE-14": "Tragen Sie eine eindeutige Rechnungsnummer ein.",
            "BR-DE-15": "Fuegen Sie das Rechnungsdatum hinzu.",
            "BR-DE-16": "Fuegen Sie mindestens eine Rechnungsposition hinzu.",
            "BR-DE-17": "Geben Sie die Menge fuer jede Position an.",
            "BR-DE-18": "Geben Sie den Einzelpreis fuer jede Position an.",
            "BR-DE-19": "Fuegen Sie eine Beschreibung fuer jede Position hinzu.",
            "BR-DE-21": "Pruefen Sie das Leitweg-ID Format: XX-XXXX-XXXX-XX (Pruefziffer am Ende).",
            "BR-DE-22": "Die Einheit muss aus der UN/ECE Rec 20 Liste stammen.",
            "BR-DE-23": "Geben Sie die Steuerkategorie fuer jede Position an.",
            # BR Core rules - Invoice basics
            "BR-01": "Tragen Sie eine eindeutige Rechnungsnummer ein.",
            "BR-02": "Fuegen Sie das Rechnungsdatum im Format JJJJ-MM-TT hinzu.",
            "BR-03": "Waehlen Sie einen gueltigen Rechnungstyp (380=Rechnung, 381=Gutschrift, 384=Korrektur).",
            "BR-04": "Geben Sie die Rechnungswaehrung an (z.B. EUR).",
            "BR-05": "Die Rechnungswaehrung muss als ISO 4217 Code angegeben werden (z.B. EUR).",
            "BR-06": "Tragen Sie den vollstaendigen Namen des Verkaeufers ein.",
            "BR-07": "Tragen Sie den vollstaendigen Namen des Kaeufers ein.",
            "BR-08": "Geben Sie die Postanschrift des Verkaeufers an.",
            "BR-09": "Fuegen Sie das Land des Verkaeufers als ISO-Code hinzu (z.B. DE).",
            "BR-10": "Geben Sie die Postanschrift des Kaeufers an.",
            "BR-11": "Fuegen Sie das Land des Kaeufers als ISO-Code hinzu (z.B. DE).",
            "BR-12": "Der Rechnungs-Bruttobetrag muss angegeben werden.",
            "BR-13": "Der zu zahlende Betrag muss angegeben werden.",
            "BR-14": "Fuegen Sie mindestens eine Rechnungsposition hinzu.",
            "BR-15": "Jede Position benoetigt eine eindeutige Positionsnummer.",
            "BR-16": "Geben Sie die Menge fuer die Position an.",
            "BR-17": "Der Nettopreis der Position muss angegeben werden.",
            "BR-18": "Der Positionsname ist erforderlich.",
            "BR-19": "Der Gesamtpreis der Position muss korrekt berechnet sein.",
            "BR-20": "Die MwSt-Kategorie muss fuer jede Position angegeben werden.",
            "BR-21": "Geben Sie den MwSt-Satz fuer die Position an.",
            # BR-CO Calculation rules
            "BR-CO-03": "Pruefen Sie: MwSt-Betrag pro Kategorie = Summe Netto × MwSt-Satz.",
            "BR-CO-04": "Pruefen Sie die Rundung des MwSt-Betrags auf 2 Dezimalstellen.",
            "BR-CO-10": "Pruefen Sie: Nettosumme + MwSt-Summe = Bruttosumme.",
            "BR-CO-11": "Pruefen Sie: Bruttosumme - Vorauszahlungen = Zahlbetrag.",
            "BR-CO-12": "Die Summe der Positionsbetraege muss der Nettosumme entsprechen.",
            "BR-CO-13": "Pruefen Sie: Positionsnetto = Menge × Einzelpreis.",
            "BR-CO-14": "Abzuege/Zuschlage muessen korrekt berechnet sein.",
            "BR-CO-15": "Die Nettosumme muss die Summe aller Positionen sein.",
            "BR-CO-16": "Die MwSt-Summe muss die Summe aller MwSt-Betraege sein.",
            "BR-CO-17": "Pruefen Sie die Berechnung des Bruttobetrags.",
            "BR-CO-18": "Der Zahlbetrag muss korrekt berechnet sein.",
            "BR-CO-19": "Die Summe der Vorauszahlungen muss stimmen.",
            "BR-CO-20": "Pruefen Sie die Rundung aller Betraege.",
            "BR-CO-21": "Der Positionsbetrag muss korrekt gerundet sein.",
            "BR-CO-25": (
                "Bei positivem Zahlbetrag muss entweder das Faelligkeitsdatum "
                "oder Zahlungsbedingungen angegeben werden."
            ),
            "BR-CO-26": "Der Einzelpreis muss korrekt angegeben sein.",
            # BR-S Standard rate VAT rules
            "BR-S-01": "Steuerkategorie S erfordert MwSt-Satz > 0% (z.B. 19% oder 7%).",
            "BR-S-02": "Geben Sie den MwSt-Satz fuer Steuerkategorie S an.",
            "BR-S-03": "Der MwSt-Satz muss fuer alle S-Positionen gleich sein.",
            "BR-S-04": "Die MwSt-Kategorie S muss mit dem Steuersatz uebereinstimmen.",
            "BR-S-05": "Verwenden Sie S fuer steuerpflichtige Umsaetze mit Normalsteuersatz.",
            "BR-S-08": "Pruefen Sie die Berechnung des MwSt-Betrags fuer Kategorie S.",
            "BR-S-09": "Der Nettobetrag fuer Kategorie S muss korrekt summiert sein.",
            # BR-AE Reverse charge rules
            "BR-AE-01": "Steuerkategorie AE (Reverse Charge) erfordert MwSt-Satz = 0%.",
            "BR-AE-02": "Bei Reverse Charge muss der Grund angegeben werden.",
            "BR-AE-03": "Geben Sie den Hinweis 'Steuerschuldnerschaft des Leistungsempfaengers' an.",
            "BR-AE-04": "Die USt-IdNr. des Kaeufers ist bei Reverse Charge erforderlich.",
            "BR-AE-05": "Verwenden Sie AE nur fuer innergemeinschaftliche Lieferungen.",
            # BR-E Exempt VAT rules
            "BR-E-01": "Steuerkategorie E (steuerbefreit) erfordert MwSt-Satz = 0%.",
            "BR-E-02": "Geben Sie den Grund fuer die Steuerbefreiung an.",
            "BR-E-03": "Verweisen Sie auf die gesetzliche Grundlage (z.B. § 4 UStG).",
            "BR-E-04": "Bei Steuerbefreiung darf kein MwSt-Betrag ausgewiesen werden.",
            "BR-E-05": "Verwenden Sie E nur fuer steuerfreie Umsaetze.",
            # BR-Z Zero rate rules
            "BR-Z-01": "Steuerkategorie Z (Nullsatz) erfordert MwSt-Satz = 0%.",
            "BR-Z-02": "Geben Sie den Grund fuer den Nullsteuersatz an.",
            "BR-Z-05": "Verwenden Sie Z nur fuer Umsaetze mit 0% MwSt.",
            # BR-G Export rules
            "BR-G-01": "Steuerkategorie G (Export) erfordert MwSt-Satz = 0%.",
            "BR-G-02": "Geben Sie den Grund fuer die Ausfuhrlieferung an.",
            "BR-G-03": "Verweisen Sie auf § 4 Nr. 1a UStG bei Exporten.",
            # BR-IC Intra-community supply
            "BR-IC-01": "Steuerkategorie IC erfordert MwSt-Satz = 0%.",
            "BR-IC-02": "Die USt-IdNr. des Kaeufers ist bei IC erforderlich.",
            "BR-IC-03": "Geben Sie den Hinweis auf innergemeinschaftliche Lieferung an.",
            # BR-K und weitere
            "BR-K-01": "Steuerkategorie K erfordert MwSt-Satz = 0%.",
            "BR-K-02": "Geben Sie den Grund fuer Kategorie K an.",
            # UBL specific rules
            "UBL-CR-001": "Pruefen Sie die UBL-Namensraeume im XML.",
            "UBL-CR-002": "Das Invoice-Element muss vorhanden sein.",
            "UBL-CR-003": "Entfernen Sie nicht erlaubte XML-Erweiterungen.",
            "UBL-SR-001": "Verwenden Sie nur erlaubte UBL-Elemente.",
            "UBL-SR-002": "Pruefen Sie die Reihenfolge der UBL-Elemente.",
            # CII specific rules
            "CII-SR-001": "Pruefen Sie die CII-Namensraeume im XML.",
            "CII-SR-002": "Das CrossIndustryInvoice-Element muss vorhanden sein.",
            "CII-SR-003": "Entfernen Sie nicht erlaubte XML-Erweiterungen.",
            # Peppol rules
            "PEPPOL-EN16931-R001": "Pruefen Sie die Peppol-Identifier.",
            "PEPPOL-EN16931-R002": "Die Peppol-Participant-ID muss gueltig sein.",
            "PEPPOL-EN16931-R003": "Verwenden Sie gueltige EAS-Codes.",
            "PEPPOL-EN16931-R004": "Die Peppol-Dokumenttyp-ID muss korrekt sein.",
            "PEPPOL-EN16931-R120": (
                "Pruefen Sie: Positionsnetto = Menge × (Einzelpreis / Preisbasis) "
                "+ Zuschlage - Abzuege."
            ),
            "PEPPOL-EN16931-R121": "Die Summe der Positionsnettobetraege muss dem Gesamtnetto entsprechen.",
            # Additional BR rules
            "BR-52": "Geben Sie die Zahlungsmethode an (z.B. Ueberweisung, Lastschrift).",
            "BR-53": "Die Zahlungsreferenz sollte angegeben werden.",
            "BR-54": "Geben Sie die Bankdaten fuer die Zahlung an.",
            "BR-55": "Die Kaeuferreferenz (Purchase Order) sollte angegeben werden.",
            "BR-56": "Geben Sie die Vertragsreferenz an, falls vorhanden.",
            "BR-57": "Die Lieferadresse sollte angegeben werden.",
            "BR-61": "Die Zahlungsbedingungen muessen verstaendlich sein.",
            "BR-62": "Das Lieferdatum oder die Lieferperiode sollte angegeben werden.",
            "BR-63": "Geben Sie die Bestell-ID an, falls vorhanden.",
            "BR-64": "Die Verkaufsreferenz sollte angegeben werden.",
            "BR-65": "Geben Sie das Lieferdatum im Format JJJJ-MM-TT an.",
            # Generic fallback suggestions
            "RULE-MISSING": "Pruefen Sie das Pflichtfeld im entsprechenden Abschnitt.",
        }
        return suggestions.get(code)
