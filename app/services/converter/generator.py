"""Generate XRechnung and ZUGFeRD invoice files."""

import io
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from xml.etree import ElementTree as ET

import fitz  # PyMuPDF

from app.services.converter.extractor import InvoiceData


class XRechnungGenerator:
    """Generate XRechnung (UBL) XML from invoice data."""

    # UBL 2.1 Namespaces
    NS = {
        "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }

    def generate(self, data: InvoiceData) -> bytes:
        """
        Generate XRechnung UBL XML from invoice data.

        Args:
            data: Extracted invoice data

        Returns:
            XML content as bytes
        """
        # Register namespaces (this handles xmlns declarations automatically)
        for prefix, uri in self.NS.items():
            ET.register_namespace(prefix, uri)

        # Create root element (don't add xmlns attributes manually - register_namespace handles it)
        root = ET.Element(f"{{{self.NS['ubl']}}}Invoice")

        # Customization ID for XRechnung 3.0
        self._add_element(
            root,
            "cbc:CustomizationID",
            "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0",
        )

        # Profile ID
        self._add_element(
            root,
            "cbc:ProfileID",
            "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
        )

        # Invoice ID
        self._add_element(
            root,
            "cbc:ID",
            data.invoice_number or f"INV-{uuid.uuid4().hex[:8].upper()}",
        )

        # Issue date
        self._add_element(
            root,
            "cbc:IssueDate",
            (data.invoice_date or date.today()).isoformat(),
        )

        # Due date
        if data.due_date:
            self._add_element(root, "cbc:DueDate", data.due_date.isoformat())

        # Invoice type code (380 = Commercial Invoice)
        self._add_element(root, "cbc:InvoiceTypeCode", "380")

        # Document currency
        self._add_element(root, "cbc:DocumentCurrencyCode", data.currency)

        # Buyer reference (Leitweg-ID for public sector)
        if data.leitweg_id:
            self._add_element(root, "cbc:BuyerReference", data.leitweg_id)

        # Order reference
        if data.order_reference:
            order_ref = ET.SubElement(root, f"{{{self.NS['cac']}}}OrderReference")
            self._add_element(order_ref, "cbc:ID", data.order_reference)

        # Supplier (AccountingSupplierParty)
        self._add_supplier_party(root, data)

        # Customer (AccountingCustomerParty)
        self._add_customer_party(root, data)

        # Delivery
        if data.delivery_date:
            delivery = ET.SubElement(root, f"{{{self.NS['cac']}}}Delivery")
            self._add_element(
                delivery, "cbc:ActualDeliveryDate", data.delivery_date.isoformat()
            )

        # Payment means
        self._add_payment_means(root, data)

        # Tax total
        self._add_tax_total(root, data)

        # Legal monetary total
        self._add_monetary_total(root, data)

        # Invoice lines
        self._add_invoice_lines(root, data)

        # Pretty-print XML
        ET.indent(root, space="    ")

        # Generate XML string
        tree = ET.ElementTree(root)
        buffer = io.BytesIO()
        tree.write(
            buffer,
            encoding="UTF-8",
            xml_declaration=True,
        )
        return buffer.getvalue()

    def _add_element(
        self, parent: ET.Element, tag: str, text: str
    ) -> ET.Element:
        """Add a child element with text content."""
        # Handle namespaced tags
        if ":" in tag:
            prefix, local = tag.split(":", 1)
            full_tag = f"{{{self.NS[prefix]}}}{local}"
        else:
            full_tag = tag

        elem = ET.SubElement(parent, full_tag)
        elem.text = text
        return elem

    def _add_supplier_party(self, root: ET.Element, data: InvoiceData) -> None:
        """Add supplier party information."""
        supplier = ET.SubElement(
            root, f"{{{self.NS['cac']}}}AccountingSupplierParty"
        )
        party = ET.SubElement(supplier, f"{{{self.NS['cac']}}}Party")

        # Endpoint ID - use email scheme with VAT ID as placeholder
        # (PEPPOL requires valid schemeID from CEF code list)
        endpoint = ET.SubElement(party, f"{{{self.NS['cbc']}}}EndpointID")
        endpoint.set("schemeID", "EM")  # Email scheme
        endpoint.text = f"{data.seller_vat_id or 'seller'}@invoice.local"

        # Party name (required by BR-06)
        party_name = ET.SubElement(party, f"{{{self.NS['cac']}}}PartyName")
        name = (data.seller.name if data.seller and data.seller.name else None) or "Lieferant"
        self._add_element(party_name, "cbc:Name", name)

        # Postal address
        if data.seller:
            address = ET.SubElement(party, f"{{{self.NS['cac']}}}PostalAddress")
            if data.seller.street:
                self._add_element(address, "cbc:StreetName", data.seller.street)
            if data.seller.city:
                self._add_element(address, "cbc:CityName", data.seller.city)
            if data.seller.postal_code:
                self._add_element(
                    address, "cbc:PostalZone", data.seller.postal_code
                )
            country = ET.SubElement(
                address, f"{{{self.NS['cac']}}}Country"
            )
            self._add_element(
                country, "cbc:IdentificationCode", data.seller.country_code
            )

        # Tax scheme
        if data.seller_vat_id:
            tax_scheme_party = ET.SubElement(
                party, f"{{{self.NS['cac']}}}PartyTaxScheme"
            )
            self._add_element(
                tax_scheme_party, "cbc:CompanyID", data.seller_vat_id
            )
            tax_scheme = ET.SubElement(
                tax_scheme_party, f"{{{self.NS['cac']}}}TaxScheme"
            )
            self._add_element(tax_scheme, "cbc:ID", "VAT")

        # Legal entity
        legal = ET.SubElement(party, f"{{{self.NS['cac']}}}PartyLegalEntity")
        self._add_element(legal, "cbc:RegistrationName", name)

        # Contact (required for XRechnung BR-DE-2)
        contact = ET.SubElement(party, f"{{{self.NS['cac']}}}Contact")
        self._add_element(contact, "cbc:Name", name or "Kontakt")
        self._add_element(contact, "cbc:Telephone", data.seller_phone or "+49 0 0000000")
        self._add_element(
            contact, "cbc:ElectronicMail",
            data.seller_email or f"{data.seller_vat_id or 'info'}@invoice.local"
        )

    def _add_customer_party(self, root: ET.Element, data: InvoiceData) -> None:
        """Add customer party information."""
        customer = ET.SubElement(
            root, f"{{{self.NS['cac']}}}AccountingCustomerParty"
        )
        party = ET.SubElement(customer, f"{{{self.NS['cac']}}}Party")

        # Endpoint ID - required for PEPPOL
        endpoint = ET.SubElement(party, f"{{{self.NS['cbc']}}}EndpointID")
        endpoint.set("schemeID", "EM")  # Email scheme
        endpoint.text = f"{data.buyer_reference or 'buyer'}@invoice.local"

        # Party name (required by BR-07)
        party_name = ET.SubElement(party, f"{{{self.NS['cac']}}}PartyName")
        name = (data.buyer.name if data.buyer and data.buyer.name else None) or "Kaeufer"
        self._add_element(party_name, "cbc:Name", name)

        # Postal address
        if data.buyer:
            address = ET.SubElement(party, f"{{{self.NS['cac']}}}PostalAddress")
            if data.buyer.street:
                self._add_element(address, "cbc:StreetName", data.buyer.street)
            if data.buyer.city:
                self._add_element(address, "cbc:CityName", data.buyer.city)
            if data.buyer.postal_code:
                self._add_element(
                    address, "cbc:PostalZone", data.buyer.postal_code
                )
            country = ET.SubElement(
                address, f"{{{self.NS['cac']}}}Country"
            )
            self._add_element(
                country,
                "cbc:IdentificationCode",
                data.buyer.country_code if data.buyer else "DE",
            )

        # Legal entity
        legal = ET.SubElement(party, f"{{{self.NS['cac']}}}PartyLegalEntity")
        self._add_element(legal, "cbc:RegistrationName", name)

    def _add_payment_means(self, root: ET.Element, data: InvoiceData) -> None:
        """Add payment means information."""
        payment = ET.SubElement(root, f"{{{self.NS['cac']}}}PaymentMeans")

        # Payment means code (58 = SEPA Credit Transfer)
        self._add_element(payment, "cbc:PaymentMeansCode", "58")

        # Payment reference
        if data.payment_reference:
            self._add_element(
                payment, "cbc:PaymentID", data.payment_reference
            )

        # Bank account
        if data.iban:
            account = ET.SubElement(
                payment, f"{{{self.NS['cac']}}}PayeeFinancialAccount"
            )
            self._add_element(account, "cbc:ID", data.iban)
            if data.bank_name:
                self._add_element(account, "cbc:Name", data.bank_name)
            if data.bic:
                branch = ET.SubElement(
                    account, f"{{{self.NS['cac']}}}FinancialInstitutionBranch"
                )
                self._add_element(branch, "cbc:ID", data.bic)

    def _add_tax_total(self, root: ET.Element, data: InvoiceData) -> None:
        """Add tax total information."""
        tax_total = ET.SubElement(root, f"{{{self.NS['cac']}}}TaxTotal")

        # Tax amount
        vat = data.vat_amount or Decimal("0")
        tax_amount = ET.SubElement(tax_total, f"{{{self.NS['cbc']}}}TaxAmount")
        tax_amount.set("currencyID", data.currency)
        tax_amount.text = f"{vat:.2f}"

        # Tax subtotal
        subtotal = ET.SubElement(tax_total, f"{{{self.NS['cac']}}}TaxSubtotal")

        taxable = ET.SubElement(subtotal, f"{{{self.NS['cbc']}}}TaxableAmount")
        taxable.set("currencyID", data.currency)
        taxable.text = f"{data.net_amount or Decimal('0'):.2f}"

        sub_tax = ET.SubElement(subtotal, f"{{{self.NS['cbc']}}}TaxAmount")
        sub_tax.set("currencyID", data.currency)
        sub_tax.text = f"{vat:.2f}"

        # Tax category
        category = ET.SubElement(subtotal, f"{{{self.NS['cac']}}}TaxCategory")
        self._add_element(category, "cbc:ID", "S")  # Standard rate
        self._add_element(category, "cbc:Percent", "19")

        scheme = ET.SubElement(category, f"{{{self.NS['cac']}}}TaxScheme")
        self._add_element(scheme, "cbc:ID", "VAT")

    def _add_monetary_total(self, root: ET.Element, data: InvoiceData) -> None:
        """Add legal monetary total."""
        total = ET.SubElement(
            root, f"{{{self.NS['cac']}}}LegalMonetaryTotal"
        )

        net = data.net_amount or Decimal("0")
        gross = data.gross_amount or Decimal("0")

        line_ext = ET.SubElement(
            total, f"{{{self.NS['cbc']}}}LineExtensionAmount"
        )
        line_ext.set("currencyID", data.currency)
        line_ext.text = f"{net:.2f}"

        tax_excl = ET.SubElement(
            total, f"{{{self.NS['cbc']}}}TaxExclusiveAmount"
        )
        tax_excl.set("currencyID", data.currency)
        tax_excl.text = f"{net:.2f}"

        tax_incl = ET.SubElement(
            total, f"{{{self.NS['cbc']}}}TaxInclusiveAmount"
        )
        tax_incl.set("currencyID", data.currency)
        tax_incl.text = f"{gross:.2f}"

        payable = ET.SubElement(total, f"{{{self.NS['cbc']}}}PayableAmount")
        payable.set("currencyID", data.currency)
        payable.text = f"{gross:.2f}"

    def _add_invoice_lines(self, root: ET.Element, data: InvoiceData) -> None:
        """Add invoice lines."""
        if data.line_items:
            for idx, item in enumerate(data.line_items, 1):
                self._add_invoice_line(root, item, idx, data.currency)
        else:
            # Add a single line item if no items were extracted
            default_item = type(
                "Item",
                (),
                {
                    "description": "Leistung/Lieferung",
                    "quantity": Decimal("1"),
                    "unit_price": data.net_amount or Decimal("0"),
                    "vat_rate": Decimal("19"),
                    "total": data.net_amount or Decimal("0"),
                },
            )()
            self._add_invoice_line(root, default_item, 1, data.currency)

    def _add_invoice_line(
        self, root: ET.Element, item, line_num: int, currency: str
    ) -> None:
        """Add a single invoice line."""
        line = ET.SubElement(root, f"{{{self.NS['cac']}}}InvoiceLine")

        self._add_element(line, "cbc:ID", str(line_num))

        qty = ET.SubElement(line, f"{{{self.NS['cbc']}}}InvoicedQuantity")
        qty.set("unitCode", item.unit or "C62")
        qty.text = f"{item.quantity:.2f}"

        amount = ET.SubElement(
            line, f"{{{self.NS['cbc']}}}LineExtensionAmount"
        )
        amount.set("currencyID", currency)
        amount.text = f"{item.total:.2f}"

        # Item
        inv_item = ET.SubElement(line, f"{{{self.NS['cac']}}}Item")
        self._add_element(inv_item, "cbc:Name", item.description)

        # Tax category for line item
        tax_cat = ET.SubElement(
            inv_item, f"{{{self.NS['cac']}}}ClassifiedTaxCategory"
        )
        self._add_element(tax_cat, "cbc:ID", "S")
        self._add_element(tax_cat, "cbc:Percent", f"{item.vat_rate:.0f}")
        scheme = ET.SubElement(tax_cat, f"{{{self.NS['cac']}}}TaxScheme")
        self._add_element(scheme, "cbc:ID", "VAT")

        # Price
        price = ET.SubElement(line, f"{{{self.NS['cac']}}}Price")
        price_amt = ET.SubElement(price, f"{{{self.NS['cbc']}}}PriceAmount")
        price_amt.set("currencyID", currency)
        price_amt.text = f"{item.unit_price:.2f}"


class ZUGFeRDGenerator:
    """Generate ZUGFeRD PDF/A-3 with embedded XML."""

    # CII Namespaces for ZUGFeRD
    NS = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
        "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    }

    def __init__(self, profile: str = "EN16931"):
        """
        Initialize ZUGFeRD generator.

        Args:
            profile: ZUGFeRD profile (MINIMUM, BASIC, EN16931, EXTENDED)
        """
        self.profile = profile

    def generate_xml(self, data: InvoiceData) -> bytes:
        """
        Generate ZUGFeRD CII XML from invoice data.

        Args:
            data: Extracted invoice data

        Returns:
            XML content as bytes
        """
        # Register namespaces (do NOT also add as attributes - causes duplicates)
        for prefix, uri in self.NS.items():
            ET.register_namespace(prefix, uri)

        # Create root element - namespaces are added automatically by register_namespace
        root = ET.Element(f"{{{self.NS['rsm']}}}CrossIndustryInvoice")

        # Document context
        context = ET.SubElement(
            root, f"{{{self.NS['rsm']}}}ExchangedDocumentContext"
        )
        guideline = ET.SubElement(
            context, f"{{{self.NS['ram']}}}GuidelineSpecifiedDocumentContextParameter"
        )
        guideline_id = ET.SubElement(guideline, f"{{{self.NS['ram']}}}ID")
        guideline_id.text = (
            "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:extended"
            if self.profile == "EXTENDED"
            else "urn:cen.eu:en16931:2017"
        )

        # Header
        header = ET.SubElement(
            root, f"{{{self.NS['rsm']}}}ExchangedDocument"
        )
        doc_id = ET.SubElement(header, f"{{{self.NS['ram']}}}ID")
        doc_id.text = data.invoice_number or f"INV-{uuid.uuid4().hex[:8].upper()}"

        type_code = ET.SubElement(header, f"{{{self.NS['ram']}}}TypeCode")
        type_code.text = "380"  # Commercial Invoice

        issue_dt = ET.SubElement(
            header, f"{{{self.NS['ram']}}}IssueDateTime"
        )
        date_str = ET.SubElement(issue_dt, f"{{{self.NS['udt']}}}DateTimeString")
        date_str.set("format", "102")
        date_str.text = (data.invoice_date or date.today()).strftime("%Y%m%d")

        # Supply chain trade transaction
        transaction = ET.SubElement(
            root, f"{{{self.NS['rsm']}}}SupplyChainTradeTransaction"
        )

        # Line items (required by BR-09 - must come first in CII)
        self._add_line_items(transaction, data)

        # Trade agreement
        agreement = ET.SubElement(
            transaction, f"{{{self.NS['ram']}}}ApplicableHeaderTradeAgreement"
        )

        # Seller
        seller_party = ET.SubElement(
            agreement, f"{{{self.NS['ram']}}}SellerTradeParty"
        )
        seller_name = ET.SubElement(
            seller_party, f"{{{self.NS['ram']}}}Name"
        )
        seller_name.text = (data.seller.name if data.seller and data.seller.name else "Lieferant")

        # Seller postal address (required for BR-07)
        seller_addr = ET.SubElement(
            seller_party, f"{{{self.NS['ram']}}}PostalTradeAddress"
        )
        if data.seller and data.seller.postal_code:
            seller_pc = ET.SubElement(seller_addr, f"{{{self.NS['ram']}}}PostcodeCode")
            seller_pc.text = data.seller.postal_code
        if data.seller and data.seller.street:
            seller_line = ET.SubElement(seller_addr, f"{{{self.NS['ram']}}}LineOne")
            seller_line.text = data.seller.street
        if data.seller and data.seller.city:
            seller_city = ET.SubElement(seller_addr, f"{{{self.NS['ram']}}}CityName")
            seller_city.text = data.seller.city
        seller_country = ET.SubElement(seller_addr, f"{{{self.NS['ram']}}}CountryID")
        seller_country.text = (data.seller.country_code if data.seller and data.seller.country_code else "DE")

        if data.seller_vat_id:
            tax_reg = ET.SubElement(
                seller_party, f"{{{self.NS['ram']}}}SpecifiedTaxRegistration"
            )
            tax_id = ET.SubElement(tax_reg, f"{{{self.NS['ram']}}}ID")
            tax_id.set("schemeID", "VA")
            tax_id.text = data.seller_vat_id

        # Buyer
        buyer_party = ET.SubElement(
            agreement, f"{{{self.NS['ram']}}}BuyerTradeParty"
        )
        buyer_name = ET.SubElement(buyer_party, f"{{{self.NS['ram']}}}Name")
        buyer_name.text = (data.buyer.name if data.buyer and data.buyer.name else "Kaeufer")

        # Buyer postal address (required for BR-08)
        buyer_addr = ET.SubElement(
            buyer_party, f"{{{self.NS['ram']}}}PostalTradeAddress"
        )
        if data.buyer and data.buyer.postal_code:
            buyer_pc = ET.SubElement(buyer_addr, f"{{{self.NS['ram']}}}PostcodeCode")
            buyer_pc.text = data.buyer.postal_code
        if data.buyer and data.buyer.street:
            buyer_line = ET.SubElement(buyer_addr, f"{{{self.NS['ram']}}}LineOne")
            buyer_line.text = data.buyer.street
        if data.buyer and data.buyer.city:
            buyer_city = ET.SubElement(buyer_addr, f"{{{self.NS['ram']}}}CityName")
            buyer_city.text = data.buyer.city
        buyer_country = ET.SubElement(buyer_addr, f"{{{self.NS['ram']}}}CountryID")
        buyer_country.text = (data.buyer.country_code if data.buyer and data.buyer.country_code else "DE")

        # Trade delivery
        delivery = ET.SubElement(
            transaction, f"{{{self.NS['ram']}}}ApplicableHeaderTradeDelivery"
        )

        if data.delivery_date:
            actual = ET.SubElement(
                delivery,
                f"{{{self.NS['ram']}}}ActualDeliverySupplyChainEvent",
            )
            occ = ET.SubElement(
                actual, f"{{{self.NS['ram']}}}OccurrenceDateTime"
            )
            occ_date = ET.SubElement(occ, f"{{{self.NS['udt']}}}DateTimeString")
            occ_date.set("format", "102")
            occ_date.text = data.delivery_date.strftime("%Y%m%d")

        # Trade settlement
        settlement = ET.SubElement(
            transaction, f"{{{self.NS['ram']}}}ApplicableHeaderTradeSettlement"
        )

        currency = ET.SubElement(
            settlement, f"{{{self.NS['ram']}}}InvoiceCurrencyCode"
        )
        currency.text = data.currency

        # Payment means
        if data.iban:
            payment = ET.SubElement(
                settlement,
                f"{{{self.NS['ram']}}}SpecifiedTradeSettlementPaymentMeans",
            )
            pay_type = ET.SubElement(payment, f"{{{self.NS['ram']}}}TypeCode")
            pay_type.text = "58"  # SEPA

            account = ET.SubElement(
                payment,
                f"{{{self.NS['ram']}}}PayeePartyCreditorFinancialAccount",
            )
            iban_elem = ET.SubElement(account, f"{{{self.NS['ram']}}}IBANID")
            iban_elem.text = data.iban

        # Tax
        tax = ET.SubElement(
            settlement, f"{{{self.NS['ram']}}}ApplicableTradeTax"
        )
        calc_amt = ET.SubElement(
            tax, f"{{{self.NS['ram']}}}CalculatedAmount"
        )
        calc_amt.text = f"{data.vat_amount or Decimal('0'):.2f}"

        type_code_tax = ET.SubElement(tax, f"{{{self.NS['ram']}}}TypeCode")
        type_code_tax.text = "VAT"

        basis_amt = ET.SubElement(
            tax, f"{{{self.NS['ram']}}}BasisAmount"
        )
        basis_amt.text = f"{data.net_amount or Decimal('0'):.2f}"

        cat_code = ET.SubElement(tax, f"{{{self.NS['ram']}}}CategoryCode")
        cat_code.text = "S"

        rate = ET.SubElement(
            tax, f"{{{self.NS['ram']}}}RateApplicablePercent"
        )
        rate.text = "19"

        # Payment terms (required by BR-CO-25)
        payment_terms = ET.SubElement(
            settlement, f"{{{self.NS['ram']}}}SpecifiedTradePaymentTerms"
        )
        if data.due_date:
            due_dt = ET.SubElement(
                payment_terms, f"{{{self.NS['ram']}}}DueDateDateTime"
            )
            due_date_str = ET.SubElement(due_dt, f"{{{self.NS['udt']}}}DateTimeString")
            due_date_str.set("format", "102")
            due_date_str.text = data.due_date.strftime("%Y%m%d")
        else:
            # If no due date, use invoice date + 30 days as default
            default_due = (data.invoice_date or date.today()) + timedelta(days=30)
            due_dt = ET.SubElement(
                payment_terms, f"{{{self.NS['ram']}}}DueDateDateTime"
            )
            due_date_str = ET.SubElement(due_dt, f"{{{self.NS['udt']}}}DateTimeString")
            due_date_str.set("format", "102")
            due_date_str.text = default_due.strftime("%Y%m%d")

        # Monetary summation
        summation = ET.SubElement(
            settlement,
            f"{{{self.NS['ram']}}}SpecifiedTradeSettlementHeaderMonetarySummation",
        )

        line_total = ET.SubElement(
            summation, f"{{{self.NS['ram']}}}LineTotalAmount"
        )
        line_total.text = f"{data.net_amount or Decimal('0'):.2f}"

        tax_basis = ET.SubElement(
            summation, f"{{{self.NS['ram']}}}TaxBasisTotalAmount"
        )
        tax_basis.text = f"{data.net_amount or Decimal('0'):.2f}"

        tax_total = ET.SubElement(
            summation, f"{{{self.NS['ram']}}}TaxTotalAmount"
        )
        tax_total.set("currencyID", data.currency)
        tax_total.text = f"{data.vat_amount or Decimal('0'):.2f}"

        grand_total = ET.SubElement(
            summation, f"{{{self.NS['ram']}}}GrandTotalAmount"
        )
        grand_total.text = f"{data.gross_amount or Decimal('0'):.2f}"

        due_amount = ET.SubElement(
            summation, f"{{{self.NS['ram']}}}DuePayableAmount"
        )
        due_amount.text = f"{data.gross_amount or Decimal('0'):.2f}"

        # Pretty-print XML
        ET.indent(root, space="    ")

        # Generate XML string
        tree = ET.ElementTree(root)
        buffer = io.BytesIO()
        tree.write(buffer, encoding="UTF-8", xml_declaration=True)
        return buffer.getvalue()

    def embed_in_pdf(
        self, pdf_content: bytes, xml_content: bytes, original_filename: str = "factur-x.xml"
    ) -> bytes:
        """
        Embed ZUGFeRD XML into a PDF file.

        Args:
            pdf_content: Original PDF content
            xml_content: ZUGFeRD XML content
            original_filename: Name for the embedded XML file

        Returns:
            PDF/A-3 with embedded XML as bytes
        """
        # Open PDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        # Add XML as embedded file (PyMuPDF uses buffer_ parameter)
        doc.embfile_add(
            name=original_filename,
            buffer_=xml_content,
            filename=original_filename,
            ufilename=original_filename,
            desc="ZUGFeRD Invoice Data",
        )

        # Add XMP metadata for PDF/A-3 compliance
        # This is a simplified version - full PDF/A-3 requires more metadata
        metadata = {
            "format": "PDF 1.7",
            "title": "ZUGFeRD Invoice",
            "subject": "Electronic Invoice with embedded structured data",
            "creator": "RechnungsChecker",
            "producer": "RechnungsChecker",
        }
        doc.set_metadata(metadata)

        # Save to buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()

        return buffer.getvalue()

    def generate_pdf(
        self, data: InvoiceData, source_pdf: Optional[bytes] = None
    ) -> bytes:
        """
        Generate a complete ZUGFeRD PDF.

        Args:
            data: Invoice data
            source_pdf: Optional source PDF to embed XML into.
                        If None, creates a simple invoice PDF.

        Returns:
            ZUGFeRD PDF/A-3 content as bytes
        """
        # Generate XML
        xml_content = self.generate_xml(data)

        if source_pdf:
            # Embed into existing PDF
            return self.embed_in_pdf(source_pdf, xml_content)
        else:
            # Create a simple PDF with invoice data
            pdf_content = self._create_simple_invoice_pdf(data)
            return self.embed_in_pdf(pdf_content, xml_content)

    def _create_simple_invoice_pdf(self, data: InvoiceData) -> bytes:
        """Create a simple invoice PDF from data."""
        doc = fitz.open()
        page = doc.new_page()

        # Add invoice content
        y = 72  # Start position
        margin = 72

        # Title
        page.insert_text(
            (margin, y),
            "RECHNUNG",
            fontsize=24,
            fontname="helv",
        )
        y += 40

        # Invoice number and date
        page.insert_text(
            (margin, y),
            f"Rechnungsnummer: {data.invoice_number or 'N/A'}",
            fontsize=11,
        )
        y += 20
        page.insert_text(
            (margin, y),
            f"Datum: {(data.invoice_date or date.today()).strftime('%d.%m.%Y')}",
            fontsize=11,
        )
        y += 40

        # Seller info
        page.insert_text((margin, y), "Von:", fontsize=11, fontname="helvB")
        y += 15
        if data.seller:
            page.insert_text((margin, y), data.seller.name or "Lieferant", fontsize=11)
            y += 15
            if data.seller.street:
                page.insert_text((margin, y), data.seller.street, fontsize=11)
                y += 15
            if data.seller.postal_code or data.seller.city:
                page.insert_text(
                    (margin, y),
                    f"{data.seller.postal_code or ''} {data.seller.city or ''}",
                    fontsize=11,
                )
                y += 15
        y += 20

        # Buyer info
        page.insert_text((margin, y), "An:", fontsize=11, fontname="helvB")
        y += 15
        if data.buyer:
            page.insert_text((margin, y), data.buyer.name or "Kaeufer", fontsize=11)
            y += 15
            if data.buyer.postal_code or data.buyer.city:
                page.insert_text(
                    (margin, y),
                    f"{data.buyer.postal_code or ''} {data.buyer.city or ''}",
                    fontsize=11,
                )
        y += 40

        # Amounts
        page.insert_text((margin, y), "Betraege:", fontsize=11, fontname="helvB")
        y += 20

        if data.net_amount:
            page.insert_text(
                (margin, y),
                f"Netto: {data.net_amount:.2f} {data.currency}",
                fontsize=11,
            )
            y += 15

        if data.vat_amount:
            page.insert_text(
                (margin, y),
                f"MwSt. (19%): {data.vat_amount:.2f} {data.currency}",
                fontsize=11,
            )
            y += 15

        if data.gross_amount:
            page.insert_text(
                (margin, y),
                f"Gesamt: {data.gross_amount:.2f} {data.currency}",
                fontsize=12,
                fontname="helvB",
            )
            y += 30

        # Bank details
        if data.iban:
            page.insert_text(
                (margin, y), "Bankverbindung:", fontsize=11, fontname="helvB"
            )
            y += 15
            page.insert_text((margin, y), f"IBAN: {data.iban}", fontsize=11)
            y += 15
            if data.bic:
                page.insert_text((margin, y), f"BIC: {data.bic}", fontsize=11)

        # Save to buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()

        return buffer.getvalue()

    def _add_line_items(
        self, transaction: ET.Element, data: InvoiceData
    ) -> None:
        """Add line items to CII transaction (required by BR-09)."""
        if data.line_items:
            for idx, item in enumerate(data.line_items, 1):
                self._add_line_item(transaction, item, idx, data.currency)
        else:
            # Add a single default line item if no items were extracted
            default_item = type(
                "Item",
                (),
                {
                    "description": "Leistung/Lieferung",
                    "quantity": Decimal("1"),
                    "unit": "C62",
                    "unit_price": data.net_amount or Decimal("0"),
                    "vat_rate": Decimal("19"),
                    "total": data.net_amount or Decimal("0"),
                },
            )()
            self._add_line_item(transaction, default_item, 1, data.currency)

    def _add_line_item(
        self, transaction: ET.Element, item, line_num: int, currency: str
    ) -> None:
        """Add a single line item to CII transaction."""
        line = ET.SubElement(
            transaction, f"{{{self.NS['ram']}}}IncludedSupplyChainTradeLineItem"
        )

        # Line document
        line_doc = ET.SubElement(
            line, f"{{{self.NS['ram']}}}AssociatedDocumentLineDocument"
        )
        line_id = ET.SubElement(line_doc, f"{{{self.NS['ram']}}}LineID")
        line_id.text = str(line_num)

        # Product (required by BR-25)
        product = ET.SubElement(
            line, f"{{{self.NS['ram']}}}SpecifiedTradeProduct"
        )
        product_name = ET.SubElement(product, f"{{{self.NS['ram']}}}Name")
        product_name.text = item.description

        # Line trade agreement (price)
        line_agreement = ET.SubElement(
            line, f"{{{self.NS['ram']}}}SpecifiedLineTradeAgreement"
        )
        net_price = ET.SubElement(
            line_agreement, f"{{{self.NS['ram']}}}NetPriceProductTradePrice"
        )
        charge_amount = ET.SubElement(
            net_price, f"{{{self.NS['ram']}}}ChargeAmount"
        )
        charge_amount.text = f"{item.unit_price:.2f}"

        # Line trade delivery (quantity)
        line_delivery = ET.SubElement(
            line, f"{{{self.NS['ram']}}}SpecifiedLineTradeDelivery"
        )
        billed_qty = ET.SubElement(
            line_delivery, f"{{{self.NS['ram']}}}BilledQuantity"
        )
        billed_qty.set("unitCode", getattr(item, 'unit', None) or "C62")
        billed_qty.text = f"{item.quantity:.2f}"

        # Line trade settlement (tax and totals)
        line_settlement = ET.SubElement(
            line, f"{{{self.NS['ram']}}}SpecifiedLineTradeSettlement"
        )

        # Line item tax (required by BR-S-08)
        line_tax = ET.SubElement(
            line_settlement, f"{{{self.NS['ram']}}}ApplicableTradeTax"
        )
        line_tax_type = ET.SubElement(line_tax, f"{{{self.NS['ram']}}}TypeCode")
        line_tax_type.text = "VAT"
        line_tax_cat = ET.SubElement(line_tax, f"{{{self.NS['ram']}}}CategoryCode")
        line_tax_cat.text = "S"
        line_tax_rate = ET.SubElement(
            line_tax, f"{{{self.NS['ram']}}}RateApplicablePercent"
        )
        line_tax_rate.text = f"{item.vat_rate:.0f}"

        # Line total (required by BR-DEC-23)
        line_summation = ET.SubElement(
            line_settlement,
            f"{{{self.NS['ram']}}}SpecifiedTradeSettlementLineMonetarySummation",
        )
        line_total_amount = ET.SubElement(
            line_summation, f"{{{self.NS['ram']}}}LineTotalAmount"
        )
        line_total_amount.text = f"{item.total:.2f}"
