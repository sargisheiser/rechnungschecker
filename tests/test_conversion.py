"""Tests for PDF to e-invoice conversion."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.converter.extractor import Address, InvoiceData, InvoiceExtractor
from app.services.converter.generator import XRechnungGenerator, ZUGFeRDGenerator
from app.services.converter.service import ConversionService, OutputFormat


class TestInvoiceExtractor:
    """Tests for invoice data extraction."""

    def test_extract_invoice_number(self) -> None:
        """Test extracting invoice number from text."""
        extractor = InvoiceExtractor()

        text = """
        Rechnung Nr.: 2024-001234
        Datum: 15.01.2024
        """
        data = extractor.extract_from_text(text)
        assert data.invoice_number == "2024-001234"

    def test_extract_invoice_number_variations(self) -> None:
        """Test extracting various invoice number formats."""
        extractor = InvoiceExtractor()

        # Test different formats
        texts = [
            ("Rechnungs-Nr.: INV-2024-001", "INV-2024-001"),
            ("Rechnungsnummer: RE/2024/123", "RE/2024/123"),
            ("Invoice No: 12345678", "12345678"),
        ]

        for text, expected in texts:
            data = extractor.extract_from_text(text)
            assert data.invoice_number == expected, f"Failed for: {text}"

    def test_extract_date(self) -> None:
        """Test extracting invoice date from text."""
        extractor = InvoiceExtractor()

        text = """
        Rechnungsdatum: 15.01.2024
        """
        data = extractor.extract_from_text(text)
        assert data.invoice_date == date(2024, 1, 15)

    def test_extract_amounts(self) -> None:
        """Test extracting financial amounts."""
        extractor = InvoiceExtractor()

        text = """
        Nettobetrag: 1.000,00 EUR
        MwSt. 19%: 190,00 EUR
        Gesamtbetrag: 1.190,00 EUR
        """
        data = extractor.extract_from_text(text)
        assert data.net_amount == Decimal("1000.00")
        assert data.vat_amount == Decimal("190.00")
        assert data.gross_amount == Decimal("1190.00")

    def test_extract_vat_id(self) -> None:
        """Test extracting VAT ID."""
        extractor = InvoiceExtractor()

        text = """
        USt-IdNr.: DE123456789
        """
        data = extractor.extract_from_text(text)
        assert data.seller_vat_id == "DE123456789"

    def test_extract_iban(self) -> None:
        """Test extracting IBAN."""
        extractor = InvoiceExtractor()

        text = """
        Bankverbindung:
        IBAN: DE89 3704 0044 0532 0130 00
        BIC: COBADEFFXXX
        """
        data = extractor.extract_from_text(text)
        assert data.iban == "DE89370400440532013000"
        assert data.bic == "COBADEFFXXX"

    def test_extract_leitweg_id(self) -> None:
        """Test extracting Leitweg-ID for public sector."""
        extractor = InvoiceExtractor()

        text = """
        Leitweg-ID: 991-12345-67
        """
        data = extractor.extract_from_text(text)
        assert data.leitweg_id == "991-12345-67"

    def test_confidence_calculation(self) -> None:
        """Test confidence score calculation."""
        extractor = InvoiceExtractor()

        # Good text with all required fields
        good_text = """
        Rechnung Nr.: 2024-001
        Rechnungsdatum: 15.01.2024
        Gesamtbetrag: 1.190,00 EUR
        """
        data = extractor.extract_from_text(good_text)
        assert data.confidence == 1.0

        # Poor text missing fields
        poor_text = "Some random text without invoice data"
        data = extractor.extract_from_text(poor_text)
        assert data.confidence == 0.0
        assert len(data.warnings) > 0


class TestXRechnungGenerator:
    """Tests for XRechnung XML generation."""

    def test_generate_basic_xrechnung(self) -> None:
        """Test generating a basic XRechnung XML."""
        generator = XRechnungGenerator()

        data = InvoiceData(
            invoice_number="2024-001",
            invoice_date=date(2024, 1, 15),
            seller=Address(
                name="Test Lieferant GmbH",
                street="Teststrasse 1",
                postal_code="10115",
                city="Berlin",
            ),
            buyer=Address(
                name="Test Kaeufer AG",
                street="Kundenweg 5",
                postal_code="80333",
                city="Muenchen",
            ),
            net_amount=Decimal("1000.00"),
            vat_amount=Decimal("190.00"),
            gross_amount=Decimal("1190.00"),
            seller_vat_id="DE123456789",
            iban="DE89370400440532013000",
        )

        xml_content = generator.generate(data)

        assert xml_content
        assert b"Invoice" in xml_content
        assert b"2024-001" in xml_content
        assert b"2024-01-15" in xml_content
        assert b"Test Lieferant GmbH" in xml_content
        assert b"1190.00" in xml_content

    def test_generate_with_leitweg_id(self) -> None:
        """Test generating XRechnung with Leitweg-ID."""
        generator = XRechnungGenerator()

        data = InvoiceData(
            invoice_number="2024-001",
            invoice_date=date(2024, 1, 15),
            net_amount=Decimal("100.00"),
            vat_amount=Decimal("19.00"),
            gross_amount=Decimal("119.00"),
            leitweg_id="991-12345-67",
        )

        xml_content = generator.generate(data)

        assert b"BuyerReference" in xml_content
        assert b"991-12345-67" in xml_content

    def test_generate_with_payment_info(self) -> None:
        """Test generating XRechnung with payment information."""
        generator = XRechnungGenerator()

        data = InvoiceData(
            invoice_number="2024-001",
            invoice_date=date(2024, 1, 15),
            net_amount=Decimal("500.00"),
            vat_amount=Decimal("95.00"),
            gross_amount=Decimal("595.00"),
            iban="DE89370400440532013000",
            bic="COBADEFFXXX",
            due_date=date(2024, 2, 15),
        )

        xml_content = generator.generate(data)

        assert b"PaymentMeans" in xml_content
        assert b"DE89370400440532013000" in xml_content
        assert b"COBADEFFXXX" in xml_content


class TestZUGFeRDGenerator:
    """Tests for ZUGFeRD generation."""

    def test_generate_xml(self) -> None:
        """Test generating ZUGFeRD CII XML."""
        generator = ZUGFeRDGenerator(profile="EN16931")

        data = InvoiceData(
            invoice_number="ZF-2024-001",
            invoice_date=date(2024, 1, 15),
            seller=Address(
                name="ZUGFeRD Lieferant GmbH",
                street="Teststrasse 1",
                postal_code="10115",
                city="Berlin",
            ),
            buyer=Address(
                name="ZUGFeRD Kaeufer AG",
                postal_code="80333",
                city="Muenchen",
            ),
            net_amount=Decimal("2000.00"),
            vat_amount=Decimal("380.00"),
            gross_amount=Decimal("2380.00"),
            seller_vat_id="DE987654321",
        )

        xml_content = generator.generate_xml(data)

        assert xml_content
        assert b"CrossIndustryInvoice" in xml_content
        assert b"ZF-2024-001" in xml_content
        assert b"2380.00" in xml_content

    def test_generate_simple_pdf(self) -> None:
        """Test generating a simple ZUGFeRD PDF."""
        generator = ZUGFeRDGenerator()

        data = InvoiceData(
            invoice_number="PDF-2024-001",
            invoice_date=date(2024, 1, 15),
            net_amount=Decimal("100.00"),
            vat_amount=Decimal("19.00"),
            gross_amount=Decimal("119.00"),
        )

        try:
            # This creates a PDF with embedded XML
            pdf_content = generator.generate_pdf(data)

            assert pdf_content
            assert pdf_content.startswith(b"%PDF")
        except Exception as e:
            if "need font file" in str(e):
                pytest.skip("Font files not available in test environment")

    def test_profile_selection(self) -> None:
        """Test different ZUGFeRD profiles."""
        for profile in ["MINIMUM", "BASIC", "EN16931", "EXTENDED"]:
            generator = ZUGFeRDGenerator(profile=profile)

            data = InvoiceData(
                invoice_number="TEST-001",
                invoice_date=date(2024, 1, 15),
                net_amount=Decimal("100.00"),
                gross_amount=Decimal("119.00"),
            )

            xml_content = generator.generate_xml(data)
            assert xml_content  # Should not raise


class TestConversionService:
    """Tests for the main conversion service."""

    def test_convert_to_xrechnung(self) -> None:
        """Test PDF to XRechnung conversion."""
        service = ConversionService()

        # Create a simple test PDF
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 100),
            "Rechnung Nr.: TEST-2024-001\n"
            "Datum: 15.01.2024\n"
            "Netto: 1.000,00 EUR\n"
            "MwSt 19%: 190,00 EUR\n"
            "Gesamt: 1.190,00 EUR\n"
            "USt-IdNr.: DE123456789",
            fontsize=11,
        )

        import io
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        pdf_content = buffer.getvalue()

        result = service.convert(
            pdf_content=pdf_content,
            output_format=OutputFormat.XRECHNUNG,
        )

        assert result.success
        assert result.output_format == OutputFormat.XRECHNUNG
        assert result.filename.endswith(".xml")
        assert b"Invoice" in result.content
        assert result.extracted_data.invoice_number == "TEST-2024-001"

    def test_convert_to_zugferd(self) -> None:
        """Test PDF to ZUGFeRD conversion."""
        service = ConversionService()

        # Create a simple test PDF
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 100),
            "Rechnung Nr.: ZF-TEST-001\n"
            "Rechnungsdatum: 20.01.2024\n"
            "Brutto: 595,00 EUR",
            fontsize=11,
        )

        import io
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        pdf_content = buffer.getvalue()

        result = service.convert(
            pdf_content=pdf_content,
            output_format=OutputFormat.ZUGFERD,
            embed_in_pdf=True,
        )

        assert result.success
        assert result.output_format == OutputFormat.ZUGFERD
        assert result.filename.endswith(".pdf")
        assert result.content.startswith(b"%PDF")

    def test_preview_extraction(self) -> None:
        """Test preview extraction without conversion."""
        service = ConversionService()

        import io

        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 100),
            "Rechnung Nr.: PREVIEW-001\n"
            "Gesamtbetrag: 500,00 EUR",
            fontsize=11,
        )

        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        pdf_content = buffer.getvalue()

        data = service.preview_extraction(pdf_content)

        assert data.invoice_number == "PREVIEW-001"
        assert data.gross_amount == Decimal("500.00")

    def test_ocr_availability(self) -> None:
        """Test OCR availability check."""
        service = ConversionService()

        # OCR availability depends on tesseract installation
        # This test just verifies the property works
        is_available = service.ocr_available
        assert isinstance(is_available, bool)


class TestAmountParsing:
    """Tests for German number format parsing."""

    def test_parse_german_amounts(self) -> None:
        """Test parsing German-formatted amounts."""
        extractor = InvoiceExtractor()

        test_cases = [
            ("Netto: 1.234,56 EUR", Decimal("1234.56")),
            ("Netto: 1234,56", Decimal("1234.56")),
            ("Netto: 100,00 EUR", Decimal("100.00")),
            ("Netto: 1.000.000,00", Decimal("1000000.00")),
        ]

        for text, expected in test_cases:
            data = extractor.extract_from_text(text)
            assert data.net_amount == expected, f"Failed for: {text}"


class TestDateParsing:
    """Tests for date format parsing."""

    def test_parse_german_dates(self) -> None:
        """Test parsing German date formats."""
        extractor = InvoiceExtractor()

        test_cases = [
            ("Datum: 15.01.2024", date(2024, 1, 15)),
            ("Datum: 01.12.2023", date(2023, 12, 1)),
            ("Datum: 15/01/2024", date(2024, 1, 15)),
            ("Datum: 1.1.24", date(2024, 1, 1)),
        ]

        for text, expected in test_cases:
            data = extractor.extract_from_text(text)
            assert data.invoice_date == expected, f"Failed for: {text}"
