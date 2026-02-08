"""DATEV Buchungsstapel export service."""

import csv
import io
import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.extracted_invoice import ExtractedInvoiceData
from app.models.validation import ValidationLog
from app.schemas.datev import DATEVBuchung, DATEVConfig, Kontenrahmen
from app.services.export.kontenrahmen import (
    get_bu_schluessel,
    get_debitor_account,
    get_revenue_account,
)

logger = logging.getLogger(__name__)

# UTF-8 BOM for Excel/DATEV compatibility
UTF8_BOM = "\ufeff"

# DATEV EXTF format version
DATEV_FORMAT_VERSION = 700
DATEV_FORMAT_CATEGORY = 21  # Buchungsstapel

# DATEV Buchungsstapel column headers (columns 1-116, but we use subset)
BUCHUNGSSTAPEL_HEADERS = [
    "Umsatz (ohne Soll/Haben-Kz)",  # 1
    "Soll/Haben-Kennzeichen",  # 2
    "WKZ Umsatz",  # 3
    "Kurs",  # 4
    "Basis-Umsatz",  # 5
    "WKZ Basis-Umsatz",  # 6
    "Konto",  # 7
    "Gegenkonto (ohne BU-Schluessel)",  # 8
    "BU-Schluessel",  # 9
    "Belegdatum",  # 10
    "Belegfeld 1",  # 11
    "Belegfeld 2",  # 12
    "Skonto",  # 13
    "Buchungstext",  # 14
    "Postensperre",  # 15
    "Diverse Adressnummer",  # 16
    "Geschaeftspartnerbank",  # 17
    "Sachverhalt",  # 18
    "Zinssperre",  # 19
    "Beleglink",  # 20
]


class DATEVExportService:
    """Service for exporting invoices to DATEV Buchungsstapel format."""

    def __init__(self, db: AsyncSession):
        """Initialize DATEV export service."""
        self.db = db

    async def export_buchungsstapel(
        self,
        user_id: UUID,
        validation_ids: list[UUID],
        config: DATEVConfig,
    ) -> tuple[str, int, Decimal]:
        """Generate DATEV Buchungsstapel CSV.

        Args:
            user_id: User ID for authorization
            validation_ids: List of validation IDs to export
            config: DATEV export configuration

        Returns:
            Tuple of (CSV content, number of bookings, total amount)
        """
        # Fetch validations
        query = select(ValidationLog).where(
            ValidationLog.user_id == user_id,
            ValidationLog.id.in_(validation_ids),
            ValidationLog.is_valid == True,  # noqa: E712
        )
        result = await self.db.execute(query)
        validations = result.scalars().all()

        if not validations:
            logger.warning(f"No valid validations found for export: {validation_ids}")
            return self._generate_empty_export(config), 0, Decimal("0")

        # Fetch extracted invoice data for all validations
        extracted_query = select(ExtractedInvoiceData).where(
            ExtractedInvoiceData.validation_id.in_(validation_ids)
        )
        extracted_result = await self.db.execute(extracted_query)
        extracted_data = {e.validation_id: e for e in extracted_result.scalars().all()}

        # Convert validations to bookings
        buchungen: list[DATEVBuchung] = []
        for validation in validations:
            extracted = extracted_data.get(validation.id)
            buchung = self._validation_to_buchung(validation, config, extracted)
            if buchung:
                buchungen.append(buchung)

        # Generate CSV
        csv_content = self._generate_csv(buchungen, config)
        total_umsatz = sum(b.umsatz for b in buchungen)

        logger.info(
            f"DATEV export generated: {len(buchungen)} bookings, "
            f"total {total_umsatz} EUR"
        )

        return csv_content, len(buchungen), total_umsatz

    def _validation_to_buchung(
        self,
        validation: ValidationLog,
        config: DATEVConfig,
        extracted: ExtractedInvoiceData | None = None,
    ) -> DATEVBuchung | None:
        """Convert a validation log entry to a DATEV booking.

        Args:
            validation: Validation log entry
            config: DATEV configuration
            extracted: Optional extracted invoice data for real amounts

        Returns:
            DATEV booking or None if conversion fails
        """
        # Use extracted data if available, otherwise use fallback values
        if extracted and extracted.gross_amount:
            # Real invoice data available
            umsatz = extracted.gross_amount
            vat_rate = extracted.vat_rate or Decimal("19")
            invoice_date = extracted.invoice_date or validation.created_at.date()
            belegnummer = extracted.invoice_number or self._generate_belegnummer(validation)
            buchungstext = self._generate_buchungstext_from_extracted(extracted, validation)
            waehrung = extracted.currency or "EUR"
        else:
            # Fallback to placeholder values
            umsatz = Decimal("0")
            vat_rate = Decimal("19")
            invoice_date = validation.created_at.date()
            belegnummer = self._generate_belegnummer(validation)
            buchungstext = self._generate_buchungstext(validation)
            waehrung = "EUR"

        bu_schluessel = get_bu_schluessel(vat_rate)

        # Get accounts based on configuration
        konto = get_debitor_account(config.kontenrahmen, config.debitor_konto)
        gegenkonto = get_revenue_account(config.kontenrahmen, vat_rate).konto

        return DATEVBuchung(
            umsatz=umsatz,
            soll_haben="S",  # Debit for revenue
            waehrung=waehrung,
            konto=konto,
            gegenkonto=gegenkonto,
            bu_schluessel=bu_schluessel,
            belegdatum=invoice_date,
            belegnummer=belegnummer[:36] if belegnummer else "",
            buchungstext=buchungstext,
        )

    def _generate_belegnummer(self, validation: ValidationLog) -> str:
        """Generate document number from validation.

        Args:
            validation: Validation log entry

        Returns:
            Document number string (max 36 chars)
        """
        # Use filename if available, otherwise use validation ID
        if validation.file_name:
            # Remove extension and truncate
            name = validation.file_name.rsplit(".", 1)[0]
            return name[:36]
        return str(validation.id)[:36]

    def _generate_buchungstext(self, validation: ValidationLog) -> str:
        """Generate booking text from validation.

        Args:
            validation: Validation log entry

        Returns:
            Booking text (max 60 chars)
        """
        prefix = "XRechnung" if validation.file_type.value == "xrechnung" else "ZUGFeRD"
        if validation.file_name:
            text = f"{prefix}: {validation.file_name}"
        else:
            text = f"{prefix} Rechnung"
        return text[:60]

    def _generate_buchungstext_from_extracted(
        self,
        extracted: ExtractedInvoiceData,
        validation: ValidationLog,
    ) -> str:
        """Generate booking text from extracted invoice data.

        Args:
            extracted: Extracted invoice data
            validation: Validation log entry

        Returns:
            Booking text (max 60 chars)
        """
        if extracted.seller_name:
            # Use seller name as the primary text
            text = extracted.seller_name
        elif validation.file_name:
            prefix = "XRechnung" if validation.file_type.value == "xrechnung" else "ZUGFeRD"
            text = f"{prefix}: {validation.file_name}"
        else:
            text = "Rechnung"
        return text[:60]

    def _generate_csv(
        self,
        buchungen: list[DATEVBuchung],
        config: DATEVConfig,
    ) -> str:
        """Generate DATEV CSV content.

        Args:
            buchungen: List of bookings
            config: DATEV configuration

        Returns:
            CSV content string with EXTF header
        """
        output = io.StringIO()

        # Write UTF-8 BOM
        output.write(UTF8_BOM)

        # Generate EXTF header row
        header_row = self._generate_extf_header(config)
        output.write(header_row + "\n")

        # Create CSV writer with semicolon delimiter (DATEV standard)
        writer = csv.writer(
            output,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
        )

        # Write column headers
        writer.writerow(BUCHUNGSSTAPEL_HEADERS)

        # Write data rows
        for buchung in buchungen:
            row = self._buchung_to_row(buchung)
            writer.writerow(row)

        return output.getvalue()

    def _generate_extf_header(self, config: DATEVConfig) -> str:
        """Generate DATEV EXTF header row.

        The EXTF header contains metadata about the export file.
        Format: "EXTF";version;category;"Buchungsstapel";...

        Args:
            config: DATEV configuration

        Returns:
            EXTF header string
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S%f")[:17]  # YYYYMMDDHHMMSSmmm

        # Fiscal year start (default to Jan 1 of current year)
        wj_beginn = config.wirtschaftsjahr_beginn or date(now.year, 1, 1)
        wj_beginn_str = wj_beginn.strftime("%Y%m%d")

        # Build header fields
        # See DATEV documentation for full field specification
        header_parts = [
            '"EXTF"',  # Format identifier
            str(DATEV_FORMAT_VERSION),  # Format version
            str(DATEV_FORMAT_CATEGORY),  # Category (21 = Buchungsstapel)
            '"Buchungsstapel"',  # Label
            '""',  # Format version label
            f'"{timestamp}"',  # Creation timestamp
            '""',  # Reserved
            '""',  # Reserved
            '""',  # Reserved
            '""',  # Reserved
            f'"{config.berater_nummer}"',  # Consultant number
            f'"{config.mandanten_nummer}"',  # Client number
            f'"{wj_beginn_str}"',  # Fiscal year start
            '""',  # Reserved
            '""',  # Reserved
            f'"{config.kontenrahmen.value}"',  # Chart of accounts
            '""',  # Booking type
            '""',  # Intent
            '""',  # Fixed flag
            '""',  # WKZ
        ]

        return ";".join(header_parts)

    def _buchung_to_row(self, buchung: DATEVBuchung) -> list[str]:
        """Convert a booking to a CSV row.

        Args:
            buchung: DATEV booking

        Returns:
            List of field values
        """
        # Format amount in German number format (comma as decimal separator)
        umsatz_str = self._format_decimal(buchung.umsatz)

        # Format date as DDMM (DATEV format for Belegdatum)
        belegdatum_str = buchung.belegdatum.strftime("%d%m")

        # Format skonto if present
        skonto_str = self._format_decimal(buchung.skonto) if buchung.skonto else ""

        return [
            umsatz_str,  # 1: Umsatz
            buchung.soll_haben,  # 2: Soll/Haben
            buchung.waehrung,  # 3: WKZ
            "",  # 4: Kurs
            "",  # 5: Basis-Umsatz
            "",  # 6: WKZ Basis-Umsatz
            buchung.konto,  # 7: Konto
            buchung.gegenkonto,  # 8: Gegenkonto
            str(buchung.bu_schluessel) if buchung.bu_schluessel else "",  # 9: BU-Schluessel
            belegdatum_str,  # 10: Belegdatum
            buchung.belegnummer,  # 11: Belegfeld 1
            buchung.belegfeld2,  # 12: Belegfeld 2
            skonto_str,  # 13: Skonto
            buchung.buchungstext,  # 14: Buchungstext
            "",  # 15: Postensperre
            "",  # 16: Diverse Adressnummer
            "",  # 17: Geschaeftspartnerbank
            "",  # 18: Sachverhalt
            "",  # 19: Zinssperre
            "",  # 20: Beleglink
        ]

    def _format_decimal(self, value: Decimal) -> str:
        """Format decimal value in German format (comma as decimal separator).

        Args:
            value: Decimal value

        Returns:
            Formatted string
        """
        # Format with 2 decimal places and replace dot with comma
        return f"{value:.2f}".replace(".", ",")

    def _generate_empty_export(self, config: DATEVConfig) -> str:
        """Generate an empty export file with just headers.

        Args:
            config: DATEV configuration

        Returns:
            CSV content with headers only
        """
        output = io.StringIO()
        output.write(UTF8_BOM)

        header_row = self._generate_extf_header(config)
        output.write(header_row + "\n")

        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(BUCHUNGSSTAPEL_HEADERS)

        return output.getvalue()
