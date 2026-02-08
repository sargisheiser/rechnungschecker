"""Pydantic schemas for DATEV Buchungsstapel export."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Kontenrahmen(StrEnum):
    """German standard chart of accounts (Kontenrahmen)."""

    SKR03 = "SKR03"  # Most common for small businesses
    SKR04 = "SKR04"  # Alternative standard


class DATEVConfig(BaseModel):
    """Configuration for DATEV export."""

    kontenrahmen: Kontenrahmen = Kontenrahmen.SKR03
    debitor_konto: str = Field(default="1400", description="Default debtor account")
    kreditor_konto: str = Field(default="1600", description="Default creditor account")
    berater_nummer: str = Field(default="", description="DATEV consultant number")
    mandanten_nummer: str = Field(default="", description="DATEV client number")
    wirtschaftsjahr_beginn: date | None = Field(
        default=None, description="Fiscal year start date"
    )
    buchungstyp: Literal["Einnahme", "Ausgabe"] = Field(
        default="Einnahme", description="Booking type (revenue or expense)"
    )


class DATEVBuchung(BaseModel):
    """Single DATEV booking entry (Buchungssatz)."""

    # Column 1: Amount (Umsatz)
    umsatz: Decimal = Field(..., description="Amount (net or gross depending on BU)")

    # Column 2: Debit/Credit indicator (Soll/Haben-Kennzeichen)
    soll_haben: Literal["S", "H"] = Field(
        ..., description="S=Debit (Soll), H=Credit (Haben)"
    )

    # Column 3: Currency code (WKZ)
    waehrung: str = Field(default="EUR", description="Currency code (ISO 4217)")

    # Column 4: Account (Konto)
    konto: str = Field(..., description="Debtor/creditor account number")

    # Column 5: Counter account (Gegenkonto)
    gegenkonto: str = Field(..., description="Revenue/expense account number")

    # Column 6: Tax key (BU-Schluessel)
    bu_schluessel: int = Field(
        default=0,
        description="Tax code: 0=no tax, 8=7% reduced, 9=19% standard",
    )

    # Column 9: Document date (Belegdatum) - format DDMM
    belegdatum: date = Field(..., description="Invoice/document date")

    # Column 10: Document number (Belegfeld1)
    belegnummer: str = Field(..., description="Invoice number", max_length=36)

    # Column 14: Booking text (Buchungstext)
    buchungstext: str = Field(default="", description="Description", max_length=60)

    # Additional optional fields
    belegfeld2: str = Field(default="", description="Additional reference", max_length=12)
    skonto: Decimal | None = Field(default=None, description="Cash discount amount")
    kost1: str = Field(default="", description="Cost center 1", max_length=36)
    kost2: str = Field(default="", description="Cost center 2", max_length=36)


class DATEVExportRequest(BaseModel):
    """Request schema for DATEV Buchungsstapel export."""

    validation_ids: list[UUID] = Field(
        ..., description="List of validation IDs to export", min_length=1
    )
    config: DATEVConfig = Field(default_factory=DATEVConfig)


class DATEVExportResponse(BaseModel):
    """Response schema for DATEV export."""

    filename: str
    buchungen_count: int
    total_umsatz: Decimal
    export_timestamp: datetime
