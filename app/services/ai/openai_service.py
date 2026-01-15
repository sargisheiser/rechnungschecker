"""OpenAI service for enhanced invoice data extraction."""

import base64
import json
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.converter.extractor import Address, InvoiceData, LineItem

logger = logging.getLogger(__name__)

# Initialize Langfuse if configured
_langfuse_client = None


def _get_openai_client() -> AsyncOpenAI:
    """Get OpenAI client with Langfuse tracing if configured."""
    global _langfuse_client

    settings = get_settings()

    # If Langfuse is configured, use it for tracing
    if settings.langfuse_secret_key and settings.langfuse_public_key:
        try:
            from langfuse import Langfuse
            from langfuse.openai import AsyncOpenAI as LangfuseAsyncOpenAI

            # Initialize Langfuse client once
            if _langfuse_client is None:
                _langfuse_client = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host,
                )
                logger.info("Langfuse tracing enabled")

            # Return Langfuse-wrapped OpenAI client
            return LangfuseAsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            logger.warning("Langfuse not installed, using standard OpenAI client")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse: {e}")

    # Fall back to standard OpenAI client
    return AsyncOpenAI(api_key=settings.openai_api_key)


@dataclass
class ExtractionResult:
    """Result from OpenAI extraction."""

    data: InvoiceData
    raw_response: dict[str, Any]
    tokens_used: int


class OpenAIExtractor:
    """Extract invoice data using OpenAI GPT models."""

    EXTRACTION_PROMPT = """Analyze this invoice image/text and extract all relevant data in JSON format.

Extract the following fields (use null if not found):
{
  "invoice_number": "string - The invoice/receipt number",
  "invoice_date": "YYYY-MM-DD - The invoice date",
  "due_date": "YYYY-MM-DD - Payment due date",
  "delivery_date": "YYYY-MM-DD - Delivery/service date",

  "seller": {
    "name": "Company name of the seller",
    "street": "Street address",
    "postal_code": "Postal/ZIP code",
    "city": "City name",
    "country_code": "ISO country code (e.g., DE)"
  },

  "buyer": {
    "name": "Company/person name of the buyer",
    "street": "Street address",
    "postal_code": "Postal/ZIP code",
    "city": "City name",
    "country_code": "ISO country code (e.g., DE)"
  },

  "net_amount": "number - Net amount without VAT",
  "vat_amount": "number - VAT/tax amount",
  "gross_amount": "number - Total amount including VAT",
  "currency": "string - Currency code (e.g., EUR)",

  "seller_vat_id": "VAT ID (e.g., DE123456789)",
  "seller_tax_id": "Tax number (Steuernummer)",
  "iban": "Bank IBAN",
  "bic": "Bank BIC/SWIFT",
  "bank_name": "Name of the bank",

  "leitweg_id": "Leitweg-ID for public sector invoices",
  "buyer_reference": "Buyer reference number",
  "order_reference": "Purchase order reference",
  "payment_reference": "Payment reference",

  "line_items": [
    {
      "description": "Item description",
      "quantity": "number",
      "unit_price": "number - Price per unit",
      "vat_rate": "number - VAT percentage (e.g., 19)",
      "total": "number - Line total"
    }
  ]
}

Important:
- All amounts should be numbers (not strings)
- Dates should be in YYYY-MM-DD format
- For German invoices, parse German date formats (DD.MM.YYYY)
- Parse German number formats (1.234,56 = 1234.56)
- Extract ALL line items if present
- Be thorough and extract as much data as possible

Respond ONLY with the JSON object, no additional text."""

    def __init__(self):
        """Initialize OpenAI extractor."""
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self._client = None  # Lazy initialization

    @property
    def client(self) -> AsyncOpenAI:
        """Get or create OpenAI client with Langfuse tracing."""
        if self._client is None:
            self._client = _get_openai_client()
        return self._client

    @property
    def is_available(self) -> bool:
        """Check if OpenAI service is configured."""
        return bool(self.api_key)

    async def extract_from_text(self, text: str) -> ExtractionResult:
        """
        Extract invoice data from text using OpenAI.

        Args:
            text: The invoice text content

        Returns:
            ExtractionResult with extracted data
        """
        if not self.is_available:
            raise ValueError("OpenAI API key not configured")

        messages = [
            {"role": "system", "content": "You are an expert invoice data extraction assistant. Extract structured data from invoices accurately."},
            {"role": "user", "content": f"{self.EXTRACTION_PROMPT}\n\nInvoice text:\n{text}"}
        ]

        response = await self._call_api(messages)
        return self._parse_response(response)

    async def extract_from_image(self, image_data: bytes, mime_type: str = "image/png") -> ExtractionResult:
        """
        Extract invoice data from an image using OpenAI Vision.

        Args:
            image_data: The image bytes
            mime_type: MIME type of the image

        Returns:
            ExtractionResult with extracted data
        """
        if not self.is_available:
            raise ValueError("OpenAI API key not configured")

        # Encode image as base64
        base64_image = base64.b64encode(image_data).decode("utf-8")

        messages = [
            {"role": "system", "content": "You are an expert invoice data extraction assistant. Extract structured data from invoice images accurately."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        response = await self._call_api(messages)
        return self._parse_response(response)

    async def extract_from_pdf_pages(self, page_images: list[bytes]) -> ExtractionResult:
        """
        Extract invoice data from PDF page images.

        Args:
            page_images: List of page images as PNG bytes

        Returns:
            ExtractionResult with extracted data
        """
        if not self.is_available:
            raise ValueError("OpenAI API key not configured")

        # Build content with all pages
        content: list[dict] = [{"type": "text", "text": self.EXTRACTION_PROMPT}]

        for i, image_data in enumerate(page_images[:5]):  # Limit to 5 pages
            base64_image = base64.b64encode(image_data).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"
                }
            })

        messages = [
            {"role": "system", "content": "You are an expert invoice data extraction assistant. Extract structured data from invoice images accurately."},
            {"role": "user", "content": content}
        ]

        response = await self._call_api(messages)
        return self._parse_response(response)

    async def _call_api(self, messages: list[dict]) -> dict[str, Any]:
        """Make API call to OpenAI using SDK with Langfuse tracing."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=0.1,  # Low temperature for consistent extraction
        )

        # Convert to dict format for compatibility
        return {
            "choices": [{"message": {"content": response.choices[0].message.content}}],
            "usage": {
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }

    def _parse_response(self, response: dict[str, Any]) -> ExtractionResult:
        """Parse OpenAI response into InvoiceData."""
        content = response["choices"][0]["message"]["content"]
        tokens_used = response.get("usage", {}).get("total_tokens", 0)

        # Parse JSON from response
        try:
            # Clean the response (remove markdown code blocks if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            raw_data = json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.error(f"Response content: {content}")
            return ExtractionResult(
                data=InvoiceData(warnings=["Failed to parse AI response"]),
                raw_response=response,
                tokens_used=tokens_used
            )

        # Convert to InvoiceData
        data = self._convert_to_invoice_data(raw_data)

        return ExtractionResult(
            data=data,
            raw_response=raw_data,
            tokens_used=tokens_used
        )

    def _convert_to_invoice_data(self, raw: dict[str, Any]) -> InvoiceData:
        """Convert raw JSON to InvoiceData object."""
        data = InvoiceData()

        # Basic fields
        data.invoice_number = raw.get("invoice_number")
        data.currency = raw.get("currency", "EUR")
        data.payment_reference = raw.get("payment_reference")
        data.buyer_reference = raw.get("buyer_reference")
        data.leitweg_id = raw.get("leitweg_id")
        data.order_reference = raw.get("order_reference")

        # Tax IDs
        data.seller_vat_id = raw.get("seller_vat_id")
        data.seller_tax_id = raw.get("seller_tax_id")

        # Bank details
        data.iban = raw.get("iban")
        data.bic = raw.get("bic")
        data.bank_name = raw.get("bank_name")

        # Dates
        data.invoice_date = self._parse_date(raw.get("invoice_date"))
        data.due_date = self._parse_date(raw.get("due_date"))
        data.delivery_date = self._parse_date(raw.get("delivery_date"))

        # Amounts
        data.net_amount = self._parse_decimal(raw.get("net_amount"))
        data.vat_amount = self._parse_decimal(raw.get("vat_amount"))
        data.gross_amount = self._parse_decimal(raw.get("gross_amount"))

        # Addresses
        if raw.get("seller"):
            data.seller = self._parse_address(raw["seller"])
        if raw.get("buyer"):
            data.buyer = self._parse_address(raw["buyer"])

        # Line items
        for item in raw.get("line_items", []):
            if item and item.get("description"):
                data.line_items.append(LineItem(
                    description=item.get("description", ""),
                    quantity=self._parse_decimal(item.get("quantity")) or Decimal("1"),
                    unit_price=self._parse_decimal(item.get("unit_price")) or Decimal("0"),
                    vat_rate=self._parse_decimal(item.get("vat_rate")) or Decimal("19"),
                    total=self._parse_decimal(item.get("total")) or Decimal("0"),
                ))

        # Calculate confidence based on extracted fields
        confidence_fields = [
            data.invoice_number, data.invoice_date, data.gross_amount,
            data.seller, data.buyer
        ]
        data.confidence = sum(1 for f in confidence_fields if f) / len(confidence_fields)

        # Add warnings for missing required fields
        if not data.invoice_number:
            data.warnings.append("Rechnungsnummer nicht gefunden")
        if not data.invoice_date:
            data.warnings.append("Rechnungsdatum nicht gefunden")
        if not data.gross_amount:
            data.warnings.append("Gesamtbetrag nicht gefunden")
        if not data.seller or not data.seller.name:
            data.warnings.append("Verkäufer nicht vollständig erkannt")
        if not data.buyer or not data.buyer.name:
            data.warnings.append("Käufer nicht vollständig erkannt")

        return data

    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not value:
            return None
        try:
            from datetime import datetime
            # Try ISO format first
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            try:
                # Try German format
                return datetime.strptime(value, "%d.%m.%Y").date()
            except ValueError:
                return None

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse value to Decimal."""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                # Handle German format
                cleaned = value.replace(" ", "").replace("€", "").replace("EUR", "")
                if "," in cleaned and "." in cleaned:
                    if cleaned.rfind(",") > cleaned.rfind("."):
                        cleaned = cleaned.replace(".", "").replace(",", ".")
                elif "," in cleaned:
                    cleaned = cleaned.replace(",", ".")
                return Decimal(cleaned)
        except Exception:
            return None
        return None

    def _parse_address(self, raw: dict[str, Any]) -> Address:
        """Parse address dictionary to Address object."""
        return Address(
            name=raw.get("name", ""),
            street=raw.get("street"),
            postal_code=raw.get("postal_code"),
            city=raw.get("city"),
            country_code=raw.get("country_code", "DE"),
        )
