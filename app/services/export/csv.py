"""CSV export service for DATEV and Excel compatibility."""

import csv
import io
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.validation import ValidationLog, FileType
from app.schemas.export import ExportFormat, ValidationStatus


class ExportService:
    """Service for exporting data to CSV format."""

    # UTF-8 BOM for Excel/DATEV compatibility
    UTF8_BOM = "\ufeff"

    # German headers for validations export
    VALIDATION_HEADERS = [
        "Validierungs-ID",
        "Mandanten-Nr.",
        "Mandantenname",
        "Dateiname",
        "Dateityp",
        "Gueltig",
        "Fehleranzahl",
        "Warnungsanzahl",
        "Hinweisanzahl",
        "XRechnung-Version",
        "ZUGFeRD-Profil",
        "Verarbeitungszeit (ms)",
        "Validator-Version",
        "Notizen",
        "Validiert am",
    ]

    # German headers for clients export
    CLIENT_HEADERS = [
        "Mandanten-ID",
        "Mandanten-Nr.",
        "Name",
        "Steuernummer",
        "USt-IdNr.",
        "Ansprechpartner",
        "E-Mail",
        "Telefon",
        "Strasse",
        "PLZ",
        "Stadt",
        "Land",
        "Aktiv",
        "Validierungen gesamt",
        "Validierungen gueltig",
        "Validierungen ungueltig",
        "Letzte Validierung",
        "Erstellt am",
    ]

    def __init__(self, db: AsyncSession):
        """Initialize export service."""
        self.db = db

    @staticmethod
    def _get_delimiter(format: ExportFormat) -> str:
        """Get CSV delimiter based on format."""
        return ";" if format == ExportFormat.CSV_DATEV else ","

    @staticmethod
    def _format_bool(value: bool) -> str:
        """Format boolean as German Ja/Nein."""
        return "Ja" if value else "Nein"

    @staticmethod
    def _format_datetime(dt: datetime | None) -> str:
        """Format datetime in German format."""
        if dt is None:
            return ""
        return dt.strftime("%d.%m.%Y %H:%M:%S")

    @staticmethod
    def _format_date(d: date | None) -> str:
        """Format date in German format."""
        if d is None:
            return ""
        return d.strftime("%d.%m.%Y")

    @staticmethod
    def _format_file_type(file_type: FileType) -> str:
        """Format file type for display."""
        return "XRechnung" if file_type == FileType.XRECHNUNG else "ZUGFeRD"

    @staticmethod
    def _safe_str(value: str | None) -> str:
        """Convert value to safe string."""
        return value if value is not None else ""

    async def export_validations(
        self,
        user_id: UUID,
        client_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: ValidationStatus = ValidationStatus.ALL,
        format: ExportFormat = ExportFormat.CSV_DATEV,
    ) -> str:
        """Export validations as CSV.

        Args:
            user_id: User ID to export validations for
            client_id: Optional client filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            status: Validation status filter
            format: Export format (DATEV or Excel)

        Returns:
            CSV string with UTF-8 BOM
        """
        # Build query
        query = (
            select(ValidationLog)
            .options(selectinload(ValidationLog.client))
            .where(ValidationLog.user_id == user_id)
            .order_by(ValidationLog.created_at.desc())
        )

        # Apply filters
        if client_id is not None:
            query = query.where(ValidationLog.client_id == client_id)

        if date_from is not None:
            query = query.where(
                ValidationLog.created_at >= datetime.combine(date_from, datetime.min.time())
            )

        if date_to is not None:
            query = query.where(
                ValidationLog.created_at <= datetime.combine(date_to, datetime.max.time())
            )

        if status == ValidationStatus.VALID:
            query = query.where(ValidationLog.is_valid == True)  # noqa: E712
        elif status == ValidationStatus.INVALID:
            query = query.where(ValidationLog.is_valid == False)  # noqa: E712

        result = await self.db.execute(query)
        validations = result.scalars().all()

        # Generate CSV
        output = io.StringIO()
        delimiter = self._get_delimiter(format)
        writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

        # Write BOM and headers
        output.write(self.UTF8_BOM)
        writer.writerow(self.VALIDATION_HEADERS)

        # Write data rows
        for v in validations:
            client_number = ""
            client_name = ""
            if v.client:
                client_number = self._safe_str(v.client.client_number)
                client_name = v.client.name

            row = [
                str(v.id),
                client_number,
                client_name,
                self._safe_str(v.file_name),
                self._format_file_type(v.file_type),
                self._format_bool(v.is_valid),
                v.error_count,
                v.warning_count,
                v.info_count,
                self._safe_str(v.xrechnung_version),
                self._safe_str(v.zugferd_profile),
                v.processing_time_ms,
                v.validator_version,
                self._safe_str(v.notes),
                self._format_datetime(v.created_at),
            ]
            writer.writerow(row)

        return output.getvalue()

    async def export_clients(
        self,
        user_id: UUID,
        include_inactive: bool = False,
        date_from: date | None = None,
        date_to: date | None = None,
        format: ExportFormat = ExportFormat.CSV_DATEV,
    ) -> str:
        """Export clients as CSV with validation statistics.

        Args:
            user_id: User ID to export clients for
            include_inactive: Include inactive clients
            date_from: Optional date filter for validation stats
            date_to: Optional date filter for validation stats
            format: Export format (DATEV or Excel)

        Returns:
            CSV string with UTF-8 BOM
        """
        # Build query for clients
        query = select(Client).where(Client.user_id == user_id).order_by(Client.name)

        if not include_inactive:
            query = query.where(Client.is_active == True)  # noqa: E712

        result = await self.db.execute(query)
        clients = result.scalars().all()

        # Build date filter conditions for validation stats
        date_conditions = []
        if date_from is not None:
            date_conditions.append(
                ValidationLog.created_at >= datetime.combine(date_from, datetime.min.time())
            )
        if date_to is not None:
            date_conditions.append(
                ValidationLog.created_at <= datetime.combine(date_to, datetime.max.time())
            )

        # Get validation statistics for each client
        client_stats = {}
        for client in clients:
            # Count total validations
            total_query = select(func.count(ValidationLog.id)).where(
                ValidationLog.client_id == client.id
            )
            if date_conditions:
                total_query = total_query.where(and_(*date_conditions))

            total_result = await self.db.execute(total_query)
            total = total_result.scalar() or 0

            # Count valid validations
            valid_query = select(func.count(ValidationLog.id)).where(
                ValidationLog.client_id == client.id,
                ValidationLog.is_valid == True,  # noqa: E712
            )
            if date_conditions:
                valid_query = valid_query.where(and_(*date_conditions))

            valid_result = await self.db.execute(valid_query)
            valid = valid_result.scalar() or 0

            client_stats[client.id] = {
                "total": total,
                "valid": valid,
                "invalid": total - valid,
            }

        # Generate CSV
        output = io.StringIO()
        delimiter = self._get_delimiter(format)
        writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

        # Write BOM and headers
        output.write(self.UTF8_BOM)
        writer.writerow(self.CLIENT_HEADERS)

        # Write data rows
        for c in clients:
            stats = client_stats.get(c.id, {"total": 0, "valid": 0, "invalid": 0})

            row = [
                str(c.id),
                self._safe_str(c.client_number),
                c.name,
                self._safe_str(c.tax_number),
                self._safe_str(c.vat_id),
                self._safe_str(c.contact_name),
                self._safe_str(c.contact_email),
                self._safe_str(c.contact_phone),
                self._safe_str(c.street),
                self._safe_str(c.postal_code),
                self._safe_str(c.city),
                c.country,
                self._format_bool(c.is_active),
                stats["total"],
                stats["valid"],
                stats["invalid"],
                self._format_datetime(c.last_validation_at),
                self._format_datetime(c.created_at),
            ]
            writer.writerow(row)

        return output.getvalue()
