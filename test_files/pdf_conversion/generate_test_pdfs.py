#!/usr/bin/env python3
"""
Generate test PDF files for conversion testing.
Run: pip install reportlab && python generate_test_pdfs.py
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def create_valid_invoice_pdf(filename="valid_invoice.pdf"):
    """Create a valid, well-structured invoice PDF."""
    doc = SimpleDocTemplate(filename, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    story = []

    # Header
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20)
    story.append(Paragraph("RECHNUNG", title_style))

    # Seller info
    seller_text = """
    <b>Muster GmbH</b><br/>
    Musterstrasse 1<br/>
    10115 Berlin<br/>
    Deutschland<br/>
    USt-IdNr.: DE123456789
    """
    story.append(Paragraph(seller_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # Invoice details
    invoice_info = """
    <b>Rechnungsnummer:</b> PDF-2024-001<br/>
    <b>Rechnungsdatum:</b> 15.01.2024<br/>
    <b>Faelligkeitsdatum:</b> 15.02.2024<br/>
    <b>Leitweg-ID:</b> 991-12345-67
    """
    story.append(Paragraph(invoice_info, styles['Normal']))
    story.append(Spacer(1, 20))

    # Buyer info
    buyer_text = """
    <b>Rechnungsempfaenger:</b><br/>
    Bundesamt fuer Muster<br/>
    Amtsstrasse 10<br/>
    53113 Bonn
    """
    story.append(Paragraph(buyer_text, styles['Normal']))
    story.append(Spacer(1, 30))

    # Line items table
    data = [
        ['Pos.', 'Beschreibung', 'Menge', 'Einzelpreis', 'Gesamt'],
        ['1', 'IT-Beratung', '8 Std.', '125,00 EUR', '1.000,00 EUR'],
        ['2', 'Software-Lizenz', '1 Stueck', '500,00 EUR', '500,00 EUR'],
        ['', '', '', 'Nettobetrag:', '1.500,00 EUR'],
        ['', '', '', 'MwSt. (19%):', '285,00 EUR'],
        ['', '', '', 'Gesamtbetrag:', '1.785,00 EUR'],
    ]

    table = Table(data, colWidths=[30, 180, 60, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('GRID', (0, 0), (-1, -4), 1, colors.black),
        ('FONTNAME', (3, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))

    # Bank info
    bank_text = """
    <b>Bankverbindung:</b><br/>
    IBAN: DE89 3704 0044 0532 0130 00<br/>
    BIC: COBADEFFXXX<br/>
    Verwendungszweck: PDF-2024-001
    """
    story.append(Paragraph(bank_text, styles['Normal']))

    doc.build(story)
    print(f"Created: {filename}")


def create_minimal_invoice_pdf(filename="minimal_invoice.pdf"):
    """Create a minimal invoice PDF with less data (tests edge cases)."""
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("RECHNUNG", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Rechnungsnummer: MIN-2024-001", styles['Normal']))
    story.append(Paragraph("Datum: 15.01.2024", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Von: Test Firma", styles['Normal']))
    story.append(Paragraph("An: Kunde", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Betrag: 100,00 EUR", styles['Normal']))
    story.append(Paragraph("MwSt: 19,00 EUR", styles['Normal']))
    story.append(Paragraph("Gesamt: 119,00 EUR", styles['Normal']))

    doc.build(story)
    print(f"Created: {filename}")


def create_complex_invoice_pdf(filename="complex_invoice.pdf"):
    """Create a complex multi-page invoice PDF."""
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("RECHNUNG", styles['Heading1']))
    story.append(Spacer(1, 10))

    # Detailed header
    header = """
    <b>Muster Consulting GmbH</b><br/>
    Hauptstrasse 100, 60313 Frankfurt am Main<br/>
    Tel: +49 69 12345678 | E-Mail: rechnung@muster-consulting.de<br/>
    Geschaeftsfuehrer: Dr. Hans Mueller | HRB 98765 | USt-IdNr.: DE987654321
    """
    story.append(Paragraph(header, styles['Normal']))
    story.append(Spacer(1, 20))

    invoice_details = """
    <b>Rechnungsnummer:</b> COMPLEX-2024-001<br/>
    <b>Bestellnummer:</b> PO-2024-12345<br/>
    <b>Rechnungsdatum:</b> 20.01.2024<br/>
    <b>Lieferdatum:</b> 15.01.2024<br/>
    <b>Faelligkeitsdatum:</b> 20.02.2024<br/>
    <b>Leitweg-ID:</b> 04011000-1234512345-12<br/>
    <b>Kaeuferreferenz:</b> Projekt Alpha 2024
    """
    story.append(Paragraph(invoice_details, styles['Normal']))
    story.append(Spacer(1, 15))

    buyer = """
    <b>Rechnungsempfaenger:</b><br/>
    Grossunternehmen AG<br/>
    Abteilung Einkauf<br/>
    Industriestrasse 50<br/>
    40210 Duesseldorf<br/>
    USt-IdNr.: DE111222333
    """
    story.append(Paragraph(buyer, styles['Normal']))
    story.append(Spacer(1, 20))

    # Many line items
    data = [['Pos.', 'Art.-Nr.', 'Beschreibung', 'Menge', 'Einheit', 'EP netto', 'Gesamt']]

    items = [
        ('1', 'BER-001', 'Strategieberatung Phase 1', '40', 'Std.', '180,00', '7.200,00'),
        ('2', 'BER-002', 'Prozessanalyse', '24', 'Std.', '150,00', '3.600,00'),
        ('3', 'BER-003', 'Workshop Moderation', '16', 'Std.', '200,00', '3.200,00'),
        ('4', 'BER-004', 'Dokumentation', '8', 'Std.', '120,00', '960,00'),
        ('5', 'SW-001', 'Software-Lizenzen Enterprise', '10', 'Stueck', '500,00', '5.000,00'),
        ('6', 'SW-002', 'Support-Vertrag 12 Monate', '1', 'Pauschal', '2.400,00', '2.400,00'),
        ('7', 'HW-001', 'Server-Hardware', '2', 'Stueck', '3.500,00', '7.000,00'),
        ('8', 'HW-002', 'Netzwerk-Komponenten', '1', 'Set', '1.500,00', '1.500,00'),
        ('9', 'INST-001', 'Installation vor Ort', '16', 'Std.', '95,00', '1.520,00'),
        ('10', 'TRAIN-001', 'Mitarbeiterschulung', '24', 'Std.', '150,00', '3.600,00'),
    ]

    for item in items:
        data.append(list(item))

    # Totals
    data.append(['', '', '', '', '', 'Nettobetrag:', '35.980,00 EUR'])
    data.append(['', '', '', '', '', 'MwSt. 19%:', '6.836,20 EUR'])
    data.append(['', '', '', '', '', 'Gesamtbetrag:', '42.816,20 EUR'])

    table = Table(data, colWidths=[25, 50, 150, 35, 40, 55, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('FONTNAME', (5, -3), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (5, -3), (-1, -3), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # Payment info
    payment = """
    <b>Zahlungsinformationen:</b><br/>
    IBAN: DE12 5001 0517 0123 4567 89<br/>
    BIC: INGDDEFFXXX<br/>
    Bank: ING-DiBa<br/>
    Verwendungszweck: COMPLEX-2024-001 / Projekt Alpha
    """
    story.append(Paragraph(payment, styles['Normal']))
    story.append(Spacer(1, 15))

    terms = """
    <b>Zahlungsbedingungen:</b><br/>
    Zahlbar innerhalb von 30 Tagen netto. Bei Zahlung innerhalb von 14 Tagen
    gewaehren wir 2% Skonto. Bei Zahlungsverzug berechnen wir Verzugszinsen
    in Hoehe von 9 Prozentpunkten ueber dem Basiszinssatz.
    """
    story.append(Paragraph(terms, styles['Normal']))

    doc.build(story)
    print(f"Created: {filename}")


def create_invalid_pdf(filename="not_an_invoice.pdf"):
    """Create a PDF that is NOT an invoice (should fail conversion)."""
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Willkommen!", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("""
        Dies ist ein einfaches Dokument ohne Rechnungsdaten.
        Es enthaelt keine strukturierten Finanzdaten und sollte
        bei der Konvertierung zu einer E-Rechnung fehlschlagen.
    """, styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Lorem ipsum dolor sit amet, consectetur adipiscing elit.", styles['Normal']))
    story.append(Paragraph("Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", styles['Normal']))

    doc.build(story)
    print(f"Created: {filename}")


if __name__ == "__main__":
    print("Generating test PDF files...")
    print("-" * 40)

    create_valid_invoice_pdf("valid_invoice.pdf")
    create_minimal_invoice_pdf("minimal_invoice.pdf")
    create_complex_invoice_pdf("complex_invoice.pdf")
    create_invalid_pdf("not_an_invoice.pdf")

    print("-" * 40)
    print("Done! Generated 4 test PDF files.")
    print("\nTest scenarios:")
    print("  - valid_invoice.pdf: Standard invoice, should convert successfully")
    print("  - minimal_invoice.pdf: Minimal data, may have extraction warnings")
    print("  - complex_invoice.pdf: Complex multi-item invoice")
    print("  - not_an_invoice.pdf: Not an invoice, should fail or produce poor results")
