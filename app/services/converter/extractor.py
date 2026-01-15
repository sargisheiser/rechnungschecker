"""Invoice data extraction from text using pattern matching and AI."""

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.services.converter.ocr import OCRService

logger = logging.getLogger(__name__)


@dataclass
class Address:
    """Address data structure."""

    name: str
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country_code: str = "DE"


@dataclass
class LineItem:
    """Invoice line item."""

    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("19")  # Default German VAT
    total: Decimal = Decimal("0")


@dataclass
class InvoiceData:
    """Extracted invoice data."""

    # Required fields
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    seller: Optional[Address] = None
    buyer: Optional[Address] = None

    # Financial data
    net_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    currency: str = "EUR"

    # Optional fields
    due_date: Optional[date] = None
    payment_reference: Optional[str] = None
    seller_tax_id: Optional[str] = None
    seller_vat_id: Optional[str] = None
    buyer_reference: Optional[str] = None
    leitweg_id: Optional[str] = None
    order_reference: Optional[str] = None
    delivery_date: Optional[date] = None

    # Bank details
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None

    # Line items
    line_items: list[LineItem] = field(default_factory=list)

    # Extraction confidence
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)


class InvoiceExtractor:
    """Extract invoice data from text using pattern matching and AI."""

    def __init__(self, ocr_service: Optional[OCRService] = None, use_ai: bool = True):
        """Initialize extractor with optional OCR service and AI enhancement."""
        self.ocr_service = ocr_service or OCRService()
        self.use_ai = use_ai
        self._ai_extractor = None

    @property
    def ai_extractor(self):
        """Lazy-load AI extractor."""
        if self._ai_extractor is None:
            try:
                from app.services.ai.openai_service import OpenAIExtractor
                self._ai_extractor = OpenAIExtractor()
            except ImportError:
                self._ai_extractor = None
        return self._ai_extractor

    @property
    def ai_available(self) -> bool:
        """Check if AI extraction is available."""
        return self.use_ai and self.ai_extractor and self.ai_extractor.is_available

    async def extract_from_pdf_async(self, pdf_content: bytes) -> InvoiceData:
        """
        Extract invoice data from a PDF file using AI if available.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Extracted invoice data
        """
        # Try AI extraction first if available
        if self.ai_available:
            try:
                # Convert PDF pages to images for vision model
                page_images = self.ocr_service.convert_pdf_to_images(pdf_content)
                if page_images:
                    logger.info(f"Using AI extraction for {len(page_images)} page(s)")
                    result = await self.ai_extractor.extract_from_pdf_pages(page_images)
                    if result.data.confidence > 0.5:
                        logger.info(f"AI extraction successful with confidence {result.data.confidence:.2f}")
                        return result.data
                    logger.info(f"AI extraction low confidence ({result.data.confidence:.2f}), falling back to pattern matching")
            except Exception as e:
                logger.warning(f"AI extraction failed, falling back to pattern matching: {e}")

        # Fall back to pattern matching
        return self.extract_from_pdf(pdf_content)

    def extract_from_pdf(self, pdf_content: bytes) -> InvoiceData:
        """
        Extract invoice data from a PDF file.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Extracted invoice data
        """
        text = self.ocr_service.extract_text_from_pdf(pdf_content)
        return self.extract_from_text(text)

    def extract_from_text(self, text: str) -> InvoiceData:
        """
        Extract invoice data from text.

        Args:
            text: Text content to extract from

        Returns:
            Extracted invoice data
        """
        data = InvoiceData()
        confidence_scores = []

        # Extract invoice number
        data.invoice_number = self._extract_invoice_number(text)
        if data.invoice_number:
            confidence_scores.append(1.0)
        else:
            data.warnings.append("Rechnungsnummer nicht gefunden")

        # Extract dates
        data.invoice_date = self._extract_invoice_date(text)
        if data.invoice_date:
            confidence_scores.append(1.0)
        else:
            data.warnings.append("Rechnungsdatum nicht gefunden")

        data.due_date = self._extract_due_date(text)
        data.delivery_date = self._extract_delivery_date(text)

        # Extract amounts
        amounts = self._extract_amounts(text)
        data.net_amount = amounts.get("net")
        data.vat_amount = amounts.get("vat")
        data.gross_amount = amounts.get("gross")

        if data.gross_amount:
            confidence_scores.append(1.0)
        else:
            data.warnings.append("Gesamtbetrag nicht gefunden")

        # Extract tax IDs
        data.seller_vat_id = self._extract_vat_id(text)
        data.seller_tax_id = self._extract_tax_id(text)

        # Extract bank details
        data.iban = self._extract_iban(text)
        data.bic = self._extract_bic(text)

        # Extract Leitweg-ID (for public sector invoices)
        data.leitweg_id = self._extract_leitweg_id(text)

        # Extract addresses (basic extraction)
        data.seller, data.buyer = self._extract_addresses(text)

        # Calculate confidence
        if confidence_scores:
            data.confidence = sum(confidence_scores) / len(confidence_scores)

        return data

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number from text."""
        patterns = [
            r"Rechnungs?\.?\s*-?\s*Nr\.?\s*:?\s*([A-Za-z0-9\-/]+)",
            r"Rechnung\s+Nr\.?\s*:?\s*([A-Za-z0-9\-/]+)",
            r"Invoice\s+No\.?\s*:?\s*([A-Za-z0-9\-/]+)",
            r"Rechnungsnummer\s*:?\s*([A-Za-z0-9\-/]+)",
            r"RE\s*-?\s*Nr\.?\s*:?\s*([A-Za-z0-9\-/]+)",
            r"Nr\.?\s*:?\s*(\d{4,}[A-Za-z0-9\-/]*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_invoice_date(self, text: str) -> Optional[date]:
        """Extract invoice date from text."""
        patterns = [
            r"Rechnungsdatum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Datum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Invoice\s+Date\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"vom\s+(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date(match.group(1))

        # Try to find any date in common German format
        date_match = re.search(r"\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b", text)
        if date_match:
            return self._parse_date(date_match.group(1))

        return None

    def _extract_due_date(self, text: str) -> Optional[date]:
        """Extract payment due date from text."""
        patterns = [
            r"Zahlbar\s+bis\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Faellig\s+am\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Zahlungsziel\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Due\s+Date\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date(match.group(1))

        return None

    def _extract_delivery_date(self, text: str) -> Optional[date]:
        """Extract delivery/service date from text."""
        patterns = [
            r"Lieferdatum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Leistungsdatum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            r"Leistungszeitraum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date(match.group(1))

        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string in German format."""
        # Normalize separators
        date_str = date_str.replace("/", ".")

        formats = ["%d.%m.%Y", "%d.%m.%y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def _extract_amounts(self, text: str) -> dict[str, Optional[Decimal]]:
        """Extract financial amounts from text."""
        amounts: dict[str, Optional[Decimal]] = {
            "net": None,
            "vat": None,
            "gross": None,
        }

        # Patterns for German number format
        amount_pattern = r"([\d.,]+)\s*(?:EUR|€)?"

        # Net amount
        net_patterns = [
            rf"Nettobetrag\s*:?\s*{amount_pattern}",
            rf"Netto\s*:?\s*{amount_pattern}",
            rf"Zwischensumme\s*:?\s*{amount_pattern}",
            rf"Subtotal\s*:?\s*{amount_pattern}",
        ]

        for pattern in net_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amounts["net"] = self._parse_amount(match.group(1))
                break

        # VAT amount
        vat_patterns = [
            rf"MwSt\.?\s*\d*\s*%?\s*:?\s*{amount_pattern}",
            rf"USt\.?\s*\d*\s*%?\s*:?\s*{amount_pattern}",
            rf"Mehrwertsteuer\s*:?\s*{amount_pattern}",
            rf"VAT\s*:?\s*{amount_pattern}",
        ]

        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amounts["vat"] = self._parse_amount(match.group(1))
                break

        # Gross amount
        gross_patterns = [
            rf"Gesamtbetrag\s*:?\s*{amount_pattern}",
            rf"Gesamt\s*:?\s*{amount_pattern}",
            rf"Rechnungsbetrag\s*:?\s*{amount_pattern}",
            rf"Endbetrag\s*:?\s*{amount_pattern}",
            rf"Total\s*:?\s*{amount_pattern}",
            rf"Summe\s*:?\s*{amount_pattern}",
            rf"Brutto\s*:?\s*{amount_pattern}",
        ]

        for pattern in gross_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amounts["gross"] = self._parse_amount(match.group(1))
                break

        # Calculate missing values if possible
        if amounts["net"] and amounts["vat"] and not amounts["gross"]:
            amounts["gross"] = amounts["net"] + amounts["vat"]
        elif amounts["gross"] and amounts["vat"] and not amounts["net"]:
            amounts["net"] = amounts["gross"] - amounts["vat"]
        elif amounts["gross"] and amounts["net"] and not amounts["vat"]:
            amounts["vat"] = amounts["gross"] - amounts["net"]

        return amounts

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Parse a German-formatted amount string."""
        try:
            # Remove spaces and currency symbols
            cleaned = amount_str.strip().replace(" ", "")

            # German format: 1.234,56 -> 1234.56
            if "," in cleaned and "." in cleaned:
                # Both separators present
                if cleaned.rfind(",") > cleaned.rfind("."):
                    # German format: dot is thousand sep, comma is decimal
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                # else: US format, leave as is
            elif "," in cleaned:
                # Only comma: could be decimal separator
                cleaned = cleaned.replace(",", ".")

            return Decimal(cleaned)
        except Exception:
            return None

    def _extract_vat_id(self, text: str) -> Optional[str]:
        """Extract VAT ID (USt-IdNr.) from text."""
        patterns = [
            r"USt\.?\s*-?\s*Id\.?\s*-?\s*Nr\.?\s*:?\s*(DE\s*\d{9})",
            r"VAT\s*ID\s*:?\s*(DE\s*\d{9})",
            r"(DE\s*\d{9})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_id = match.group(1).replace(" ", "")
                if re.match(r"DE\d{9}$", vat_id):
                    return vat_id

        return None

    def _extract_tax_id(self, text: str) -> Optional[str]:
        """Extract tax ID (Steuernummer) from text."""
        patterns = [
            r"Steuer\.?\s*-?\s*Nr\.?\s*:?\s*(\d{2,3}[/\s]\d{3}[/\s]\d{4,5})",
            r"St\.?\s*-?\s*Nr\.?\s*:?\s*(\d{2,3}[/\s]\d{3}[/\s]\d{4,5})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_iban(self, text: str) -> Optional[str]:
        """Extract IBAN from text."""
        pattern = r"IBAN\s*:?\s*([A-Z]{2}\s*\d{2}[\s\d]{12,30})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            iban = match.group(1).replace(" ", "").upper()
            # Basic IBAN validation (length and format)
            if re.match(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}$", iban):
                return iban
        return None

    def _extract_bic(self, text: str) -> Optional[str]:
        """Extract BIC/SWIFT from text."""
        pattern = r"BIC\s*:?\s*([A-Z]{6}[A-Z0-9]{2,5})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def _extract_leitweg_id(self, text: str) -> Optional[str]:
        """Extract Leitweg-ID for public sector invoices."""
        pattern = r"Leitweg\s*-?\s*ID\s*:?\s*([\d\-]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_addresses(
        self, text: str
    ) -> tuple[Optional[Address], Optional[Address]]:
        """
        Extract seller and buyer addresses from text.
        This is a simplified extraction - real implementation would be more sophisticated.
        """
        # Try to find address blocks
        seller = None
        buyer = None

        # Look for postal codes and cities
        address_pattern = r"(\d{5})\s+([A-Za-zäöüÄÖÜß\s]+)"

        matches = re.findall(address_pattern, text)
        if matches:
            # First address is typically seller
            if len(matches) >= 1:
                seller = Address(
                    name="",  # Would need more sophisticated extraction
                    postal_code=matches[0][0],
                    city=matches[0][1].strip(),
                )
            if len(matches) >= 2:
                buyer = Address(
                    name="",
                    postal_code=matches[1][0],
                    city=matches[1][1].strip(),
                )

        return seller, buyer
