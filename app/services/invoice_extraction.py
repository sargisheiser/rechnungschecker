"""Invoice data extraction service for DATEV export."""

import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID
from xml.etree import ElementTree as ET

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extracted_invoice import ExtractedInvoiceData
from app.schemas.extracted_invoice import ExtractedInvoiceDataCreate

logger = logging.getLogger(__name__)

# XML namespaces for XRechnung/UBL
NAMESPACES = {
    "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    # CII (Cross Industry Invoice) namespaces for ZUGFeRD
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}


class InvoiceExtractionService:
    """Service for extracting invoice data from XML files."""

    def __init__(self, db: AsyncSession):
        """Initialize extraction service."""
        self.db = db

    async def extract_and_store(
        self,
        validation_id: UUID,
        content: bytes,
        is_pdf: bool = False,
    ) -> ExtractedInvoiceData | None:
        """Extract invoice data from content and store in database.

        Args:
            validation_id: ID of the validation log entry
            content: File content (XML or PDF bytes)
            is_pdf: True if content is a PDF file

        Returns:
            ExtractedInvoiceData if extraction succeeded, None otherwise
        """
        try:
            if is_pdf:
                # Extract XML from PDF
                xml_content = self._extract_xml_from_pdf(content)
                if not xml_content:
                    logger.warning(f"No XML found in PDF for validation {validation_id}")
                    return None
            else:
                xml_content = content

            # Parse and extract data
            extracted = self._extract_from_xml(xml_content)
            if not extracted:
                logger.warning(f"Failed to extract data from XML for validation {validation_id}")
                return None

            # Store in database
            invoice_data = ExtractedInvoiceData(
                validation_id=validation_id,
                invoice_number=extracted.invoice_number,
                invoice_date=extracted.invoice_date,
                net_amount=extracted.net_amount,
                vat_amount=extracted.vat_amount,
                gross_amount=extracted.gross_amount,
                currency=extracted.currency,
                vat_rate=extracted.vat_rate,
                seller_name=extracted.seller_name,
                confidence=extracted.confidence,
            )

            self.db.add(invoice_data)
            await self.db.flush()

            logger.info(
                f"Extracted invoice data for validation {validation_id}: "
                f"invoice_number={extracted.invoice_number}, gross={extracted.gross_amount}"
            )

            return invoice_data

        except Exception as e:
            logger.exception(f"Error extracting invoice data: {e}")
            return None

    def _extract_xml_from_pdf(self, pdf_content: bytes) -> bytes | None:
        """Extract embedded XML from a ZUGFeRD/Factur-X PDF.

        Args:
            pdf_content: PDF file content

        Returns:
            Embedded XML content or None if not found
        """
        try:
            import pikepdf

            with pikepdf.Pdf.open(pdf_content) as pdf:
                # Look for embedded files
                if "/Names" not in pdf.Root:
                    return None

                names = pdf.Root.Names
                if "/EmbeddedFiles" not in names:
                    return None

                embedded_files = names.EmbeddedFiles
                if "/Names" not in embedded_files:
                    return None

                names_array = embedded_files.Names
                for i in range(0, len(names_array), 2):
                    name = str(names_array[i])
                    # ZUGFeRD/Factur-X XML filenames
                    if name.lower() in [
                        "zugferd-invoice.xml",
                        "factur-x.xml",
                        "xrechnung.xml",
                        "invoice.xml",
                    ]:
                        file_spec = names_array[i + 1]
                        if "/EF" in file_spec and "/F" in file_spec.EF:
                            stream = file_spec.EF.F
                            return bytes(stream.read_bytes())

        except ImportError:
            logger.warning("pikepdf not installed, cannot extract XML from PDF")
        except Exception as e:
            logger.warning(f"Error extracting XML from PDF: {e}")

        return None

    def _extract_from_xml(self, xml_content: bytes) -> ExtractedInvoiceDataCreate | None:
        """Extract invoice data from XML content.

        Supports both UBL (XRechnung) and CII (ZUGFeRD) formats.

        Args:
            xml_content: XML file content

        Returns:
            ExtractedInvoiceDataCreate or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.warning(f"XML parse error: {e}")
            return None

        # Detect format based on root element
        root_tag = root.tag.lower()

        if "invoice" in root_tag and "crossindustry" not in root_tag:
            # UBL format (XRechnung)
            return self._extract_ubl(root)
        elif "crossindustry" in root_tag:
            # CII format (ZUGFeRD)
            return self._extract_cii(root)
        else:
            logger.warning(f"Unknown XML format: {root.tag}")
            return None

    def _extract_ubl(self, root: ET.Element) -> ExtractedInvoiceDataCreate | None:
        """Extract data from UBL (XRechnung) XML.

        Args:
            root: XML root element

        Returns:
            ExtractedInvoiceDataCreate or None
        """
        try:
            # Invoice number
            invoice_number = self._get_text(root, ".//cbc:ID", NAMESPACES)

            # Invoice date
            invoice_date_str = self._get_text(root, ".//cbc:IssueDate", NAMESPACES)
            invoice_date = self._parse_date(invoice_date_str)

            # Amounts from LegalMonetaryTotal
            monetary_total = root.find(".//cac:LegalMonetaryTotal", NAMESPACES)

            net_amount = None
            gross_amount = None
            vat_amount = None

            if monetary_total is not None:
                net_amount = self._parse_decimal(
                    self._get_text(monetary_total, "cbc:TaxExclusiveAmount", NAMESPACES)
                )
                gross_amount = self._parse_decimal(
                    self._get_text(monetary_total, "cbc:TaxInclusiveAmount", NAMESPACES)
                )
                # Try PayableAmount if TaxInclusiveAmount not found
                if gross_amount is None:
                    gross_amount = self._parse_decimal(
                        self._get_text(monetary_total, "cbc:PayableAmount", NAMESPACES)
                    )

            # VAT amount from TaxTotal
            tax_total = root.find(".//cac:TaxTotal", NAMESPACES)
            if tax_total is not None:
                vat_amount = self._parse_decimal(
                    self._get_text(tax_total, "cbc:TaxAmount", NAMESPACES)
                )

            # VAT rate from TaxSubtotal
            vat_rate = None
            tax_subtotal = root.find(".//cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory", NAMESPACES)
            if tax_subtotal is not None:
                vat_rate = self._parse_decimal(
                    self._get_text(tax_subtotal, "cbc:Percent", NAMESPACES)
                )

            # Currency
            currency = self._get_text(root, ".//cbc:DocumentCurrencyCode", NAMESPACES) or "EUR"

            # Seller name
            seller_name = self._get_text(
                root, ".//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", NAMESPACES
            )
            if not seller_name:
                xpath = ".//cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName"
                seller_name = self._get_text(root, xpath, NAMESPACES)

            return ExtractedInvoiceDataCreate(
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                net_amount=net_amount,
                vat_amount=vat_amount,
                gross_amount=gross_amount,
                currency=currency[:3] if currency else "EUR",
                vat_rate=vat_rate,
                seller_name=seller_name[:200] if seller_name else None,
                confidence=Decimal("0.95") if gross_amount else Decimal("0.5"),
            )

        except Exception as e:
            logger.warning(f"Error extracting UBL data: {e}")
            return None

    def _extract_cii(self, root: ET.Element) -> ExtractedInvoiceDataCreate | None:
        """Extract data from CII (ZUGFeRD) XML.

        Args:
            root: XML root element

        Returns:
            ExtractedInvoiceDataCreate or None
        """
        try:
            # Find SupplyChainTradeTransaction
            transaction = root.find(".//rsm:SupplyChainTradeTransaction", NAMESPACES)
            if transaction is None:
                # Try without namespace prefix
                transaction = root.find(".//{*}SupplyChainTradeTransaction")

            if transaction is None:
                return None

            # Find HeaderExchangedDocument for invoice number and date
            header = root.find(".//rsm:ExchangedDocument", NAMESPACES)
            if header is None:
                header = root.find(".//{*}ExchangedDocument")

            invoice_number = None
            invoice_date = None

            if header is not None:
                invoice_number = self._get_text(header, "ram:ID", NAMESPACES)
                if not invoice_number:
                    invoice_number = self._get_text(header, "{*}ID")

                date_elem = header.find(".//ram:IssueDateTime/udt:DateTimeString", NAMESPACES)
                if date_elem is None:
                    date_elem = header.find(".//{*}IssueDateTime/{*}DateTimeString")
                if date_elem is not None and date_elem.text:
                    invoice_date = self._parse_date(date_elem.text)

            # Find trade settlement for amounts
            settlement = transaction.find(".//ram:ApplicableHeaderTradeSettlement", NAMESPACES)
            if settlement is None:
                settlement = transaction.find(".//{*}ApplicableHeaderTradeSettlement")

            net_amount = None
            vat_amount = None
            gross_amount = None
            vat_rate = None
            currency = "EUR"

            if settlement is not None:
                # Currency
                currency_elem = self._get_text(settlement, "ram:InvoiceCurrencyCode", NAMESPACES)
                if currency_elem:
                    currency = currency_elem

                # Monetary summation
                summation = settlement.find(".//ram:SpecifiedTradeSettlementHeaderMonetarySummation", NAMESPACES)
                if summation is None:
                    summation = settlement.find(".//{*}SpecifiedTradeSettlementHeaderMonetarySummation")

                if summation is not None:
                    net_amount = self._parse_decimal(
                        self._get_text(summation, "ram:TaxBasisTotalAmount", NAMESPACES) or
                        self._get_text(summation, "{*}TaxBasisTotalAmount")
                    )
                    vat_amount = self._parse_decimal(
                        self._get_text(summation, "ram:TaxTotalAmount", NAMESPACES) or
                        self._get_text(summation, "{*}TaxTotalAmount")
                    )
                    gross_amount = self._parse_decimal(
                        self._get_text(summation, "ram:GrandTotalAmount", NAMESPACES) or
                        self._get_text(summation, "{*}GrandTotalAmount")
                    )
                    if gross_amount is None:
                        gross_amount = self._parse_decimal(
                            self._get_text(summation, "ram:DuePayableAmount", NAMESPACES) or
                            self._get_text(summation, "{*}DuePayableAmount")
                        )

                # VAT rate from applicable trade tax
                tax = settlement.find(".//ram:ApplicableTradeTax", NAMESPACES)
                if tax is None:
                    tax = settlement.find(".//{*}ApplicableTradeTax")
                if tax is not None:
                    vat_rate = self._parse_decimal(
                        self._get_text(tax, "ram:RateApplicablePercent", NAMESPACES) or
                        self._get_text(tax, "{*}RateApplicablePercent")
                    )

            # Seller name
            seller_party = transaction.find(".//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty", NAMESPACES)
            if seller_party is None:
                seller_party = transaction.find(".//{*}SellerTradeParty")

            seller_name = None
            if seller_party is not None:
                seller_name = self._get_text(seller_party, "ram:Name", NAMESPACES)
                if not seller_name:
                    seller_name = self._get_text(seller_party, "{*}Name")

            return ExtractedInvoiceDataCreate(
                invoice_number=invoice_number[:100] if invoice_number else None,
                invoice_date=invoice_date,
                net_amount=net_amount,
                vat_amount=vat_amount,
                gross_amount=gross_amount,
                currency=currency[:3] if currency else "EUR",
                vat_rate=vat_rate,
                seller_name=seller_name[:200] if seller_name else None,
                confidence=Decimal("0.9") if gross_amount else Decimal("0.4"),
            )

        except Exception as e:
            logger.warning(f"Error extracting CII data: {e}")
            return None

    def _get_text(
        self,
        elem: ET.Element,
        path: str,
        namespaces: dict | None = None,
    ) -> str | None:
        """Get text content from an element by path.

        Args:
            elem: Parent element
            path: XPath expression
            namespaces: Optional namespace dict

        Returns:
            Text content or None
        """
        found = elem.find(path, namespaces) if namespaces else elem.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return None

    def _parse_decimal(self, value: str | None) -> Decimal | None:
        """Parse a decimal value from string.

        Args:
            value: String value to parse

        Returns:
            Decimal or None
        """
        if not value:
            return None
        try:
            # Handle both . and , as decimal separator
            cleaned = value.replace(",", ".").replace(" ", "")
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _parse_date(self, value: str | None) -> date | None:
        """Parse a date from string.

        Supports formats:
        - YYYY-MM-DD (ISO)
        - YYYYMMDD (compact)
        - DD.MM.YYYY (German)

        Args:
            value: String value to parse

        Returns:
            date or None
        """
        if not value:
            return None

        value = value.strip()

        # ISO format: YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass

        # Compact format: YYYYMMDD
        if re.match(r"^\d{8}$", value):
            try:
                return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
            except ValueError:
                pass

        # German format: DD.MM.YYYY
        match = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", value)
        if match:
            try:
                return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            except ValueError:
                pass

        return None
