"""Invoice data extraction from text using pattern matching and AI."""

import io
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from app.services.converter.ocr import OCRService

# Import rate limit error for re-raising
try:
    from app.services.ai.openai_service import AIRateLimitError
except ImportError:
    AIRateLimitError = None  # type: ignore

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
    unit: str = "C62"  # Default unit code (piece)
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("19")  # Default German VAT
    total: Decimal = Decimal("0")


# German VAT rates and their EU tax category codes
VAT_CATEGORY_MAP = {
    Decimal("19"): "S",   # Standard rate
    Decimal("7"): "AA",   # Reduced rate (food, books, etc.)
    Decimal("0"): "Z",    # Zero rate
}


def get_vat_category(vat_rate: Decimal) -> str:
    """Get EU tax category code for a VAT rate."""
    # Normalize to integer for lookup
    rate_int = Decimal(str(int(vat_rate)))
    return VAT_CATEGORY_MAP.get(rate_int, "S")  # Default to Standard


@dataclass
class TaxBreakdown:
    """Tax breakdown for a specific VAT rate."""

    vat_rate: Decimal  # e.g., 19, 7, 0
    category_code: str = "S"  # S=Standard, AA=Reduced, Z=Zero
    taxable_amount: Decimal = Decimal("0")  # Net amount for this rate
    tax_amount: Decimal = Decimal("0")  # VAT amount for this rate

    def __post_init__(self):
        """Set category code based on VAT rate if not provided."""
        if self.category_code == "S" and self.vat_rate != Decimal("19"):
            self.category_code = get_vat_category(self.vat_rate)


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
    seller_email: Optional[str] = None
    seller_phone: Optional[str] = None
    buyer_reference: Optional[str] = None
    leitweg_id: Optional[str] = None
    order_reference: Optional[str] = None
    delivery_date: Optional[date] = None
    vat_rate: Decimal = Decimal("19")  # Main VAT rate

    # Bank details
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None

    # Line items
    line_items: list[LineItem] = field(default_factory=list)

    # Tax breakdowns (for multiple VAT rates)
    tax_breakdowns: list[TaxBreakdown] = field(default_factory=list)

    # Extraction confidence
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def get_tax_breakdowns(self) -> list[TaxBreakdown]:
        """Get tax breakdowns, computing from line items if not set."""
        if self.tax_breakdowns:
            return self.tax_breakdowns

        # Compute from line items if available
        if self.line_items:
            breakdowns_by_rate: dict[Decimal, TaxBreakdown] = {}
            for item in self.line_items:
                rate = item.vat_rate
                if rate not in breakdowns_by_rate:
                    breakdowns_by_rate[rate] = TaxBreakdown(
                        vat_rate=rate,
                        category_code=get_vat_category(rate),
                        taxable_amount=Decimal("0"),
                        tax_amount=Decimal("0"),
                    )
                breakdowns_by_rate[rate].taxable_amount += item.total
                breakdowns_by_rate[rate].tax_amount += (
                    item.total * rate / Decimal("100")
                )
            return list(breakdowns_by_rate.values())

        # Fallback: single breakdown from totals
        if self.net_amount or self.vat_amount:
            return [
                TaxBreakdown(
                    vat_rate=self.vat_rate,
                    category_code=get_vat_category(self.vat_rate),
                    taxable_amount=self.net_amount or Decimal("0"),
                    tax_amount=self.vat_amount or Decimal("0"),
                )
            ]

        return []

    def validate_line_items(self) -> list[str]:
        """
        Validate that line items are consistent with totals.

        Returns:
            List of validation warnings
        """
        warnings = []

        if not self.line_items:
            return warnings

        # Calculate sum of line item totals
        line_items_total = sum(item.total for item in self.line_items)

        # Compare with net amount if available
        if self.net_amount:
            diff = abs(line_items_total - self.net_amount)
            tolerance = self.net_amount * Decimal("0.02")  # 2% tolerance

            if diff > tolerance:
                warnings.append(
                    f"Summe der Positionen ({line_items_total:.2f}) weicht vom "
                    f"Nettobetrag ({self.net_amount:.2f}) ab"
                )

        # Check individual items
        for i, item in enumerate(self.line_items, 1):
            # Verify quantity × unit_price ≈ total
            expected_total = item.quantity * item.unit_price
            if abs(expected_total - item.total) > Decimal("0.01"):
                warnings.append(
                    f"Position {i}: Berechneter Betrag ({expected_total:.2f}) "
                    f"weicht von Gesamt ({item.total:.2f}) ab"
                )

            # Check for suspicious values
            if item.total <= Decimal("0"):
                warnings.append(f"Position {i}: Ungültiger Betrag ({item.total:.2f})")

            if item.quantity <= Decimal("0"):
                warnings.append(f"Position {i}: Ungültige Menge ({item.quantity})")

        return warnings


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
                # Re-raise rate limit errors so they can be handled by the API layer
                if AIRateLimitError and isinstance(e, AIRateLimitError):
                    raise
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
        data = self.extract_from_text(text)

        # Try to extract tables using pdfplumber for better line item detection
        if PDFPLUMBER_AVAILABLE and not data.line_items:
            table_items = self._extract_tables_from_pdf(pdf_content)
            if table_items:
                data.line_items = table_items
                logger.info(f"Extracted {len(table_items)} line items from PDF tables")

        return data

    def _extract_tables_from_pdf(self, pdf_content: bytes) -> list[LineItem]:
        """
        Extract line items from PDF tables using pdfplumber.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            List of extracted line items
        """
        if not PDFPLUMBER_AVAILABLE:
            return []

        items: list[LineItem] = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        # Try to identify column indices
                        header = table[0] if table[0] else []
                        col_indices = self._identify_table_columns(header)

                        if not col_indices:
                            # Try without header (use position-based detection)
                            col_indices = self._guess_column_indices(table)

                        if col_indices:
                            # Extract items from data rows
                            for row in table[1:]:
                                item = self._extract_item_from_row(row, col_indices)
                                if item:
                                    items.append(item)

        except Exception as e:
            logger.warning(f"Failed to extract tables from PDF: {e}")

        return self._deduplicate_line_items(items)

    def _identify_table_columns(self, header: list) -> Optional[dict]:
        """
        Identify column indices from table header.

        Returns dict with keys: 'desc', 'qty', 'unit', 'price', 'total'
        """
        if not header:
            return None

        indices = {}
        header_lower = [str(h).lower() if h else "" for h in header]

        # Description column
        for i, h in enumerate(header_lower):
            if any(w in h for w in ["beschreibung", "bezeichnung", "artikel", "leistung", "position", "description"]):
                indices["desc"] = i
                break

        # Quantity column
        for i, h in enumerate(header_lower):
            if any(w in h for w in ["menge", "anzahl", "qty", "quantity", "anz"]):
                indices["qty"] = i
                break

        # Unit column
        for i, h in enumerate(header_lower):
            if any(w in h for w in ["einheit", "unit", "eh", "me"]):
                indices["unit"] = i
                break

        # Unit price column
        for i, h in enumerate(header_lower):
            if any(w in h for w in ["einzelpreis", "preis", "e-preis", "ep", "price", "stückpreis"]):
                indices["price"] = i
                break

        # Total column
        for i, h in enumerate(header_lower):
            if any(w in h for w in ["gesamt", "betrag", "summe", "total", "netto", "gesamtpreis"]):
                indices["total"] = i
                break

        # Need at least description and one amount column
        if "desc" in indices and ("price" in indices or "total" in indices):
            return indices

        return None

    def _guess_column_indices(self, table: list) -> Optional[dict]:
        """
        Guess column indices based on data patterns when no clear header exists.
        """
        if len(table) < 2 or not table[1]:
            return None

        # Assume common format: Pos | Description | Qty | Unit | Price | Total
        num_cols = len(table[1])

        if num_cols >= 5:
            # Likely format with position number
            return {
                "desc": 1,
                "qty": 2,
                "unit": 3 if num_cols >= 6 else None,
                "price": -2,  # Second to last
                "total": -1,  # Last column
            }
        elif num_cols >= 3:
            # Minimal format: Description | Price | Total
            return {
                "desc": 0,
                "price": -2 if num_cols > 3 else None,
                "total": -1,
            }

        return None

    def _extract_item_from_row(self, row: list, col_indices: dict) -> Optional[LineItem]:
        """
        Extract a LineItem from a table row using identified column indices.
        """
        if not row:
            return None

        try:
            # Get description
            desc_idx = col_indices.get("desc", 0)
            desc = str(row[desc_idx]).strip() if desc_idx < len(row) and row[desc_idx] else None

            if not desc or len(desc) < 3:
                return None

            # Skip summary/total rows
            skip_words = ["gesamt", "summe", "netto", "brutto", "mwst", "ust", "total", "zwischensumme"]
            if any(w in desc.lower() for w in skip_words):
                return None

            # Get quantity
            qty = Decimal("1")
            if "qty" in col_indices:
                qty_idx = col_indices["qty"]
                if qty_idx < len(row) and row[qty_idx]:
                    try:
                        qty_str = str(row[qty_idx]).replace(",", ".").strip()
                        qty = Decimal(re.sub(r"[^\d.]", "", qty_str) or "1")
                    except Exception:
                        qty = Decimal("1")

            # Get unit
            unit = "C62"
            if col_indices.get("unit") is not None:
                unit_idx = col_indices["unit"]
                if unit_idx < len(row) and row[unit_idx]:
                    unit = self._normalize_unit(str(row[unit_idx]))

            # Get unit price
            unit_price = None
            if "price" in col_indices:
                price_idx = col_indices["price"]
                if price_idx < len(row) and row[price_idx]:
                    unit_price = self._parse_amount(str(row[price_idx]))

            # Get total
            total = None
            if "total" in col_indices:
                total_idx = col_indices["total"]
                if total_idx < len(row) and row[total_idx]:
                    total = self._parse_amount(str(row[total_idx]))

            # Need at least one amount
            if not unit_price and not total:
                return None

            # Calculate missing values
            if total and not unit_price and qty:
                unit_price = total / qty
            elif unit_price and not total and qty:
                total = unit_price * qty
            elif not total:
                total = unit_price or Decimal("0")

            return LineItem(
                description=desc[:100],  # Limit length
                quantity=qty,
                unit=unit,
                unit_price=unit_price or total,
                vat_rate=Decimal("19"),
                total=total,
            )

        except Exception as e:
            logger.debug(f"Failed to extract item from row: {e}")
            return None

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

        # Extract line items from text
        data.line_items = self._extract_line_items(text)
        if data.line_items:
            confidence_scores.append(0.8)  # Line items found adds confidence

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
            iban = match.group(1).replace(" ", "").strip().upper()
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

    def _extract_line_items(self, text: str) -> list[LineItem]:
        """
        Extract line items from invoice text using pattern matching.

        Looks for patterns like:
        - "1 x Product Name 100,00 EUR"
        - "Product Description  10  Stk  50,00  500,00"
        - Tabular data with quantity, description, price columns
        """
        items: list[LineItem] = []

        # Amount pattern for prices
        amount_pattern = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))"

        # Pattern 1: "Qty x Description Price" or "Qty Description @ Price"
        # e.g., "2 x Beratungsstunde 150,00 EUR"
        qty_x_pattern = rf"(\d+(?:[.,]\d+)?)\s*[xX×]\s+(.+?)\s+{amount_pattern}"

        for match in re.finditer(qty_x_pattern, text):
            try:
                qty = Decimal(match.group(1).replace(",", "."))
                desc = match.group(2).strip()[:100]  # Limit description length
                price = self._parse_amount(match.group(3))
                if price and desc and len(desc) > 2:
                    items.append(LineItem(
                        description=desc,
                        quantity=qty,
                        unit_price=price,
                        vat_rate=Decimal("19"),
                        total=qty * price,
                    ))
            except Exception:
                continue

        # Pattern 2: Tabular line items with Pos/Nr, Description, Qty, Unit, Price, Total
        # Common German invoice format
        # e.g., "1  Softwareentwicklung  10  Std  85,00  850,00"
        table_pattern = rf"^\s*(\d+)\s+(.{{10,80}}?)\s+(\d+(?:[.,]\d+)?)\s+(Stk|Std|h|kg|m|l|Stück|Stunden|Pauschal|psch)\.?\s+{amount_pattern}\s+{amount_pattern}"

        for match in re.finditer(table_pattern, text, re.MULTILINE | re.IGNORECASE):
            try:
                desc = match.group(2).strip()
                qty = Decimal(match.group(3).replace(",", "."))
                unit = self._normalize_unit(match.group(4))
                unit_price = self._parse_amount(match.group(5))
                total = self._parse_amount(match.group(6))

                if desc and unit_price and total and len(desc) > 2:
                    items.append(LineItem(
                        description=desc,
                        quantity=qty,
                        unit=unit,
                        unit_price=unit_price,
                        vat_rate=Decimal("19"),
                        total=total,
                    ))
            except Exception:
                continue

        # Pattern 3: Simple "Description: Amount" or "Description Amount EUR"
        # e.g., "Beratungsleistung: 500,00 EUR"
        simple_pattern = rf"^([A-Za-zäöüÄÖÜß][A-Za-zäöüÄÖÜß\s\-]{5,50}):\s*{amount_pattern}\s*(?:EUR|€)?"

        for match in re.finditer(simple_pattern, text, re.MULTILINE):
            try:
                desc = match.group(1).strip()
                total = self._parse_amount(match.group(2))

                # Skip if it looks like a summary line
                skip_words = ["gesamt", "summe", "netto", "brutto", "mwst", "ust", "total"]
                if total and desc and not any(w in desc.lower() for w in skip_words):
                    items.append(LineItem(
                        description=desc,
                        quantity=Decimal("1"),
                        unit_price=total,
                        vat_rate=Decimal("19"),
                        total=total,
                    ))
            except Exception:
                continue

        # Pattern 4: Line items with VAT rate specified
        # e.g., "Bücher (7%): 50,00 EUR" or "Export (0%): 1.000,00"
        # Use [^\n\r] instead of \s to avoid matching across lines
        vat_pattern = rf"^([A-Za-zäöüÄÖÜß][A-Za-zäöüÄÖÜß \-]{{2,40}})\s*\((\d+)\s*%\)\s*:?\s*{amount_pattern}"

        for match in re.finditer(vat_pattern, text, re.MULTILINE):
            try:
                desc = match.group(1).strip()
                vat_rate = Decimal(match.group(2))
                total = self._parse_amount(match.group(3))

                if total and desc:
                    items.append(LineItem(
                        description=desc,
                        quantity=Decimal("1"),
                        unit_price=total,
                        vat_rate=vat_rate,
                        total=total,
                    ))
            except Exception:
                continue

        # Remove duplicates based on description similarity
        unique_items = self._deduplicate_line_items(items)

        return unique_items

    def _normalize_unit(self, unit_str: str) -> str:
        """Convert German unit names to UN/ECE codes."""
        unit_map = {
            "stk": "C62",    # Piece
            "stück": "C62",
            "std": "HUR",    # Hour
            "stunden": "HUR",
            "h": "HUR",
            "kg": "KGM",     # Kilogram
            "m": "MTR",      # Meter
            "l": "LTR",      # Liter
            "pauschal": "C62",
            "psch": "C62",
        }
        return unit_map.get(unit_str.lower().strip("."), "C62")

    def _deduplicate_line_items(self, items: list[LineItem]) -> list[LineItem]:
        """Remove duplicate line items based on description and total."""
        seen = set()
        unique = []

        for item in items:
            # Create a key from description (first 30 chars) and total
            key = (item.description[:30].lower(), float(item.total))
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique
