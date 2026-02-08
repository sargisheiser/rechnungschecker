"""Tests for invoice data extraction service."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.invoice_extraction import InvoiceExtractionService


# Sample UBL (XRechnung) XML
SAMPLE_UBL_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ID>RE-2024-00123</cbc:ID>
    <cbc:IssueDate>2024-03-15</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>Test Lieferant GmbH</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="EUR">190.00</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cac:TaxCategory>
                <cbc:Percent>19</cbc:Percent>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:TaxExclusiveAmount currencyID="EUR">1000.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="EUR">1190.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="EUR">1190.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>
"""

# Sample CII (ZUGFeRD) XML
SAMPLE_CII_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice
    xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
    xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
    xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocument>
        <ram:ID>ZF-2024-456</ram:ID>
        <ram:IssueDateTime>
            <udt:DateTimeString>20240420</udt:DateTimeString>
        </ram:IssueDateTime>
    </rsm:ExchangedDocument>
    <rsm:SupplyChainTradeTransaction>
        <ram:ApplicableHeaderTradeAgreement>
            <ram:SellerTradeParty>
                <ram:Name>ZUGFeRD Verkaufer AG</ram:Name>
            </ram:SellerTradeParty>
        </ram:ApplicableHeaderTradeAgreement>
        <ram:ApplicableHeaderTradeSettlement>
            <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
            <ram:ApplicableTradeTax>
                <ram:RateApplicablePercent>7</ram:RateApplicablePercent>
            </ram:ApplicableTradeTax>
            <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                <ram:TaxBasisTotalAmount>500.00</ram:TaxBasisTotalAmount>
                <ram:TaxTotalAmount>35.00</ram:TaxTotalAmount>
                <ram:GrandTotalAmount>535.00</ram:GrandTotalAmount>
            </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        </ram:ApplicableHeaderTradeSettlement>
    </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""


class TestInvoiceExtractionUBL:
    """Test UBL (XRechnung) extraction."""

    def test_extract_ubl_invoice_number(self):
        """Test extracting invoice number from UBL XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        assert result.invoice_number == "RE-2024-00123"

    def test_extract_ubl_invoice_date(self):
        """Test extracting invoice date from UBL XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        assert result.invoice_date == date(2024, 3, 15)

    def test_extract_ubl_amounts(self):
        """Test extracting amounts from UBL XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        assert result.net_amount == Decimal("1000.00")
        assert result.vat_amount == Decimal("190.00")
        assert result.gross_amount == Decimal("1190.00")

    def test_extract_ubl_currency(self):
        """Test extracting currency from UBL XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        assert result.currency == "EUR"

    def test_extract_ubl_vat_rate(self):
        """Test extracting VAT rate from UBL XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        assert result.vat_rate == Decimal("19")

    def test_extract_ubl_seller_name(self):
        """Test extracting seller name from UBL XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        assert result.seller_name == "Test Lieferant GmbH"

    def test_extract_ubl_confidence(self):
        """Test confidence score for UBL extraction."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_UBL_XML)

        assert result is not None
        # High confidence when gross_amount is available
        assert result.confidence == Decimal("0.95")


class TestInvoiceExtractionCII:
    """Test CII (ZUGFeRD) extraction."""

    def test_extract_cii_invoice_number(self):
        """Test extracting invoice number from CII XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_CII_XML)

        assert result is not None
        assert result.invoice_number == "ZF-2024-456"

    def test_extract_cii_invoice_date(self):
        """Test extracting invoice date from CII XML (compact format)."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_CII_XML)

        assert result is not None
        assert result.invoice_date == date(2024, 4, 20)

    def test_extract_cii_amounts(self):
        """Test extracting amounts from CII XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_CII_XML)

        assert result is not None
        assert result.net_amount == Decimal("500.00")
        assert result.vat_amount == Decimal("35.00")
        assert result.gross_amount == Decimal("535.00")

    def test_extract_cii_vat_rate(self):
        """Test extracting VAT rate from CII XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_CII_XML)

        assert result is not None
        assert result.vat_rate == Decimal("7")

    def test_extract_cii_seller_name(self):
        """Test extracting seller name from CII XML."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_CII_XML)

        assert result is not None
        assert result.seller_name == "ZUGFeRD Verkaufer AG"

    def test_extract_cii_confidence(self):
        """Test confidence score for CII extraction."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)
        result = service._extract_from_xml(SAMPLE_CII_XML)

        assert result is not None
        # Slightly lower confidence for CII when gross_amount is available
        assert result.confidence == Decimal("0.9")


class TestDateParsing:
    """Test date parsing helper."""

    def test_parse_iso_date(self):
        """Test parsing ISO date format."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_date("2024-03-15") == date(2024, 3, 15)
        assert service._parse_date("2023-12-01") == date(2023, 12, 1)

    def test_parse_compact_date(self):
        """Test parsing compact date format (YYYYMMDD)."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_date("20240315") == date(2024, 3, 15)
        assert service._parse_date("20231201") == date(2023, 12, 1)

    def test_parse_german_date(self):
        """Test parsing German date format (DD.MM.YYYY)."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_date("15.03.2024") == date(2024, 3, 15)
        assert service._parse_date("01.12.2023") == date(2023, 12, 1)

    def test_parse_invalid_date(self):
        """Test parsing invalid date returns None."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_date("invalid") is None
        assert service._parse_date("") is None
        assert service._parse_date(None) is None

    def test_parse_date_with_whitespace(self):
        """Test parsing date with whitespace."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_date("  2024-03-15  ") == date(2024, 3, 15)


class TestDecimalParsing:
    """Test decimal parsing helper."""

    def test_parse_standard_decimal(self):
        """Test parsing standard decimal format."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_decimal("1000.00") == Decimal("1000.00")
        assert service._parse_decimal("19.99") == Decimal("19.99")

    def test_parse_german_decimal(self):
        """Test parsing German decimal format (comma)."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_decimal("1000,00") == Decimal("1000.00")
        assert service._parse_decimal("19,99") == Decimal("19.99")

    def test_parse_decimal_with_spaces(self):
        """Test parsing decimal with spaces."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_decimal(" 1000.00 ") == Decimal("1000.00")

    def test_parse_invalid_decimal(self):
        """Test parsing invalid decimal returns None."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        assert service._parse_decimal("invalid") is None
        assert service._parse_decimal("") is None
        assert service._parse_decimal(None) is None


class TestInvalidXML:
    """Test handling of invalid XML."""

    def test_invalid_xml_syntax(self):
        """Test handling of invalid XML syntax."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        result = service._extract_from_xml(b"<not valid xml")
        assert result is None

    def test_unknown_xml_format(self):
        """Test handling of unknown XML format."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        unknown_xml = b"""<?xml version="1.0"?>
        <SomeOtherDocument>
            <Data>value</Data>
        </SomeOtherDocument>
        """
        result = service._extract_from_xml(unknown_xml)
        assert result is None


class TestMinimalXML:
    """Test extraction from minimal XML."""

    def test_minimal_ubl_no_amounts(self):
        """Test UBL extraction without amounts."""
        mock_db = MagicMock(spec=AsyncSession)
        service = InvoiceExtractionService(mock_db)

        minimal_xml = b"""<?xml version="1.0"?>
        <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:ID>MIN-001</cbc:ID>
        </Invoice>
        """
        result = service._extract_from_xml(minimal_xml)

        assert result is not None
        assert result.invoice_number == "MIN-001"
        assert result.gross_amount is None
        # Low confidence when no gross amount
        assert result.confidence == Decimal("0.5")


class TestDATEVExportWithExtractedData:
    """Test DATEV export using extracted invoice data."""

    @pytest.mark.asyncio
    async def test_export_uses_extracted_amounts(self, db_session: AsyncSession):
        """Test that DATEV export uses real extracted amounts."""
        from app.models.extracted_invoice import ExtractedInvoiceData
        from app.models.validation import ValidationLog
        from app.schemas.datev import DATEVConfig, Kontenrahmen
        from app.services.export.datev import DATEVExportService

        # Create a test user
        from app.models.user import User, PlanType
        user = User(
            email="datev_test@test.com",
            password_hash="hashed",
            plan=PlanType.STEUERBERATER,
        )
        db_session.add(user)
        await db_session.flush()

        # Create a validation log
        from app.models.validation import FileType
        validation = ValidationLog(
            user_id=user.id,
            file_name="test-invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="abc123",
            file_size_bytes=1024,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.flush()

        # Create extracted invoice data
        extracted = ExtractedInvoiceData(
            validation_id=validation.id,
            invoice_number="REAL-2024-001",
            invoice_date=date(2024, 5, 15),
            net_amount=Decimal("1000.00"),
            vat_amount=Decimal("190.00"),
            gross_amount=Decimal("1190.00"),
            currency="EUR",
            vat_rate=Decimal("19.00"),
            seller_name="Real Supplier GmbH",
            confidence=Decimal("0.95"),
        )
        db_session.add(extracted)
        await db_session.commit()

        # Export to DATEV
        service = DATEVExportService(db_session)
        config = DATEVConfig(
            kontenrahmen=Kontenrahmen.SKR03,
            berater_nummer="12345",
            mandanten_nummer="67890",
        )

        csv_content, count, total = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        assert count == 1
        assert total == Decimal("1190.00")

        # Verify CSV contains real data
        assert "1190,00" in csv_content  # Gross amount
        assert "Real Supplier GmbH" in csv_content  # Seller name
        assert "1505" in csv_content  # Date as DDMM
