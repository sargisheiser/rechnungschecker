"""XRechnung XML generator."""

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from app.schemas.invoice import InvoiceData, LineItem, PartyInfo

logger = logging.getLogger(__name__)

# XRechnung UBL namespaces
NAMESPACES = {
    "": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}

# Tax category codes
TAX_CATEGORIES = {
    "S": "Standard rate",
    "Z": "Zero rated goods",
    "E": "Exempt from tax",
    "AE": "VAT Reverse Charge",
    "K": "Intra-Community supply",
}


class XRechnungGenerator:
    """Generator for XRechnung-compliant UBL invoices."""

    def __init__(self) -> None:
        """Initialize the generator."""
        self.customization_id = (
            "urn:cen.eu:en16931:2017#compliant#"
            "urn:xoev-de:kosit:standard:xrechnung_3.0"
        )
        self.profile_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

    def generate(self, data: InvoiceData) -> str:
        """Generate XRechnung XML from invoice data.

        Args:
            data: The invoice data structure.

        Returns:
            The XRechnung XML as a formatted string.
        """
        # Create root element with namespaces
        root = Element("Invoice")
        root.set("xmlns", NAMESPACES[""])
        root.set("xmlns:cac", NAMESPACES["cac"])
        root.set("xmlns:cbc", NAMESPACES["cbc"])

        # Add customization and profile IDs
        self._add_text_element(root, "cbc:CustomizationID", self.customization_id)
        self._add_text_element(root, "cbc:ProfileID", self.profile_id)

        # Invoice identification
        self._add_text_element(
            root, "cbc:ID", data.invoice_number or f"INV-{uuid4().hex[:8].upper()}"
        )
        self._add_text_element(
            root,
            "cbc:IssueDate",
            (data.invoice_date or date.today()).isoformat(),
        )

        # Due date
        if data.due_date:
            self._add_text_element(root, "cbc:DueDate", data.due_date.isoformat())

        # Invoice type code (380 = Commercial invoice)
        self._add_text_element(root, "cbc:InvoiceTypeCode", "380")

        # Note
        if data.note:
            self._add_text_element(root, "cbc:Note", data.note)

        # Document currency
        self._add_text_element(root, "cbc:DocumentCurrencyCode", data.currency)

        # Buyer reference (Leitweg-ID)
        if data.references and data.references.buyer_reference:
            self._add_text_element(
                root, "cbc:BuyerReference", data.references.buyer_reference
            )

        # Order reference
        if data.references and data.references.order_reference:
            order_ref = SubElement(root, "cac:OrderReference")
            self._add_text_element(order_ref, "cbc:ID", data.references.order_reference)

        # Contract reference
        if data.references and data.references.contract_reference:
            contract_ref = SubElement(root, "cac:ContractDocumentReference")
            self._add_text_element(
                contract_ref, "cbc:ID", data.references.contract_reference
            )

        # Seller (AccountingSupplierParty)
        if data.seller:
            self._add_party(root, "cac:AccountingSupplierParty", data.seller)

        # Buyer (AccountingCustomerParty)
        if data.buyer:
            self._add_party(root, "cac:AccountingCustomerParty", data.buyer)

        # Payment means
        if data.payment:
            payment_means = SubElement(root, "cac:PaymentMeans")
            self._add_text_element(
                payment_means,
                "cbc:PaymentMeansCode",
                data.payment.payment_means_code,
            )

            if data.payment.iban:
                payee_account = SubElement(payment_means, "cac:PayeeFinancialAccount")
                self._add_text_element(payee_account, "cbc:ID", data.payment.iban)

                if data.payment.bank_name:
                    self._add_text_element(
                        payee_account, "cbc:Name", data.payment.bank_name
                    )

                if data.payment.bic:
                    branch = SubElement(payee_account, "cac:FinancialInstitutionBranch")
                    self._add_text_element(branch, "cbc:ID", data.payment.bic)

        # Payment terms
        if data.payment and data.payment.payment_terms:
            payment_terms = SubElement(root, "cac:PaymentTerms")
            self._add_text_element(payment_terms, "cbc:Note", data.payment.payment_terms)

        # Calculate totals
        line_totals = []
        tax_totals: dict[str, Decimal] = {}

        for item in data.line_items:
            line_total = item.quantity * item.unit_price
            line_totals.append(line_total)

            tax_key = f"{item.tax_rate}_{item.tax_category}"
            tax_amount = line_total * item.tax_rate / Decimal("100")
            tax_totals[tax_key] = tax_totals.get(tax_key, Decimal("0")) + tax_amount

        net_total = sum(line_totals)
        tax_total = sum(tax_totals.values())
        gross_total = net_total + tax_total

        # Tax total
        tax_total_elem = SubElement(root, "cac:TaxTotal")
        tax_amount_elem = SubElement(tax_total_elem, "cbc:TaxAmount")
        tax_amount_elem.set("currencyID", data.currency)
        tax_amount_elem.text = f"{tax_total:.2f}"

        # Tax subtotals by rate
        for tax_key, amount in tax_totals.items():
            rate, category = tax_key.split("_")
            subtotal = SubElement(tax_total_elem, "cac:TaxSubtotal")

            taxable_amount = SubElement(subtotal, "cbc:TaxableAmount")
            taxable_amount.set("currencyID", data.currency)
            # Calculate taxable amount for this rate
            rate_taxable = sum(
                item.quantity * item.unit_price
                for item in data.line_items
                if f"{item.tax_rate}_{item.tax_category}" == tax_key
            )
            taxable_amount.text = f"{rate_taxable:.2f}"

            tax_amt = SubElement(subtotal, "cbc:TaxAmount")
            tax_amt.set("currencyID", data.currency)
            tax_amt.text = f"{amount:.2f}"

            tax_cat = SubElement(subtotal, "cac:TaxCategory")
            self._add_text_element(tax_cat, "cbc:ID", category)
            self._add_text_element(tax_cat, "cbc:Percent", str(rate))
            tax_scheme = SubElement(tax_cat, "cac:TaxScheme")
            self._add_text_element(tax_scheme, "cbc:ID", "VAT")

        # Legal monetary total
        monetary_total = SubElement(root, "cac:LegalMonetaryTotal")

        line_ext = SubElement(monetary_total, "cbc:LineExtensionAmount")
        line_ext.set("currencyID", data.currency)
        line_ext.text = f"{net_total:.2f}"

        tax_excl = SubElement(monetary_total, "cbc:TaxExclusiveAmount")
        tax_excl.set("currencyID", data.currency)
        tax_excl.text = f"{net_total:.2f}"

        tax_incl = SubElement(monetary_total, "cbc:TaxInclusiveAmount")
        tax_incl.set("currencyID", data.currency)
        tax_incl.text = f"{gross_total:.2f}"

        payable = SubElement(monetary_total, "cbc:PayableAmount")
        payable.set("currencyID", data.currency)
        payable.text = f"{gross_total:.2f}"

        # Invoice lines
        for i, item in enumerate(data.line_items, 1):
            self._add_invoice_line(root, i, item, data.currency)

        # Convert to string with proper formatting
        xml_string = tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_string)
        formatted = dom.toprettyxml(indent="  ", encoding="UTF-8")

        # Remove extra blank lines and fix declaration
        lines = formatted.decode("utf-8").split("\n")
        cleaned = "\n".join(line for line in lines if line.strip())

        return cleaned

    def _add_text_element(
        self, parent: Element, tag: str, text: str | None
    ) -> Element | None:
        """Add a text element if text is not None."""
        if text is None:
            return None
        elem = SubElement(parent, tag)
        elem.text = str(text)
        return elem

    def _add_party(self, root: Element, tag: str, party: PartyInfo) -> None:
        """Add a party (seller or buyer) element."""
        party_elem = SubElement(root, tag)
        inner_party = SubElement(party_elem, "cac:Party")

        # Party name
        party_name = SubElement(inner_party, "cac:PartyName")
        self._add_text_element(party_name, "cbc:Name", party.name)

        # Postal address
        if party.address:
            postal = SubElement(inner_party, "cac:PostalAddress")
            if party.address.street:
                self._add_text_element(postal, "cbc:StreetName", party.address.street)
            if party.address.city:
                self._add_text_element(postal, "cbc:CityName", party.address.city)
            if party.address.postal_code:
                self._add_text_element(
                    postal, "cbc:PostalZone", party.address.postal_code
                )

            country = SubElement(postal, "cac:Country")
            self._add_text_element(
                country, "cbc:IdentificationCode", party.address.country
            )

        # Tax scheme (VAT ID)
        if party.vat_id:
            tax_scheme_elem = SubElement(inner_party, "cac:PartyTaxScheme")
            self._add_text_element(tax_scheme_elem, "cbc:CompanyID", party.vat_id)
            scheme = SubElement(tax_scheme_elem, "cac:TaxScheme")
            self._add_text_element(scheme, "cbc:ID", "VAT")

        # Legal entity
        legal = SubElement(inner_party, "cac:PartyLegalEntity")
        self._add_text_element(legal, "cbc:RegistrationName", party.name)
        if party.tax_id:
            self._add_text_element(legal, "cbc:CompanyID", party.tax_id)

        # Contact
        if party.email or party.phone:
            contact = SubElement(inner_party, "cac:Contact")
            if party.phone:
                self._add_text_element(contact, "cbc:Telephone", party.phone)
            if party.email:
                self._add_text_element(contact, "cbc:ElectronicMail", party.email)

    def _add_invoice_line(
        self, root: Element, line_id: int, item: LineItem, currency: str
    ) -> None:
        """Add an invoice line element."""
        line = SubElement(root, "cac:InvoiceLine")

        self._add_text_element(line, "cbc:ID", str(line_id))

        # Quantity
        qty = SubElement(line, "cbc:InvoicedQuantity")
        qty.set("unitCode", item.unit)
        qty.text = str(item.quantity)

        # Line total
        line_total = item.quantity * item.unit_price
        line_ext = SubElement(line, "cbc:LineExtensionAmount")
        line_ext.set("currencyID", currency)
        line_ext.text = f"{line_total:.2f}"

        # Item
        invoice_item = SubElement(line, "cac:Item")
        self._add_text_element(invoice_item, "cbc:Description", item.description)
        self._add_text_element(invoice_item, "cbc:Name", item.description)

        # Classified tax category
        tax_cat = SubElement(invoice_item, "cac:ClassifiedTaxCategory")
        self._add_text_element(tax_cat, "cbc:ID", item.tax_category)
        self._add_text_element(tax_cat, "cbc:Percent", str(item.tax_rate))
        tax_scheme = SubElement(tax_cat, "cac:TaxScheme")
        self._add_text_element(tax_scheme, "cbc:ID", "VAT")

        # Price
        price = SubElement(line, "cac:Price")
        price_amount = SubElement(price, "cbc:PriceAmount")
        price_amount.set("currencyID", currency)
        price_amount.text = f"{item.unit_price:.2f}"


# Singleton instance
xrechnung_generator = XRechnungGenerator()
