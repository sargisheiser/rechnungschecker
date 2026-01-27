"""PDF report generation service for validation results using ReportLab."""

import io
import logging
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.validation import ValidationResponse

logger = logging.getLogger(__name__)

# Colors
PRIMARY_COLOR = colors.HexColor("#1A5276")
SUCCESS_COLOR = colors.HexColor("#28B463")
ERROR_COLOR = colors.HexColor("#E74C3C")
WARNING_COLOR = colors.HexColor("#F39C12")
INFO_COLOR = colors.HexColor("#2E86AB")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
BORDER_COLOR = colors.HexColor("#dddddd")


def get_styles():
    """Get custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        alignment=1,  # Center
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.gray,
        alignment=1,  # Center
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="ValidStatus",
        parent=styles["Normal"],
        fontSize=18,
        textColor=SUCCESS_COLOR,
        alignment=1,  # Center
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="InvalidStatus",
        parent=styles["Normal"],
        fontSize=18,
        textColor=ERROR_COLOR,
        alignment=1,  # Center
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceBefore=20,
        spaceAfter=10,
        borderPadding=(0, 0, 5, 0),
    ))

    styles.add(ParagraphStyle(
        name="ErrorItem",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=10,
        spaceBefore=5,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="WarningItem",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=10,
        spaceBefore=5,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="InfoItem",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=10,
        spaceBefore=5,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="FooterText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.gray,
        alignment=1,  # Center
    ))

    return styles


def generate_validation_report_pdf(result: ValidationResponse) -> bytes:
    """Generate PDF report for validation result using ReportLab.

    Args:
        result: ValidationResponse to generate report for

    Returns:
        PDF file content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = get_styles()
    story = []

    # Header
    story.append(Paragraph("RechnungsChecker", styles["ReportTitle"]))
    story.append(Paragraph("Validierungsbericht", styles["Subtitle"]))
    story.append(Spacer(1, 10 * mm))

    # Status box
    if result.is_valid:
        status_text = "✓ GÜLTIG"
        status_style = styles["ValidStatus"]
        status_bg = colors.HexColor("#d4edda")
        status_border = SUCCESS_COLOR
    else:
        status_text = "✗ UNGÜLTIG"
        status_style = styles["InvalidStatus"]
        status_bg = colors.HexColor("#f8d7da")
        status_border = ERROR_COLOR

    status_table = Table(
        [[Paragraph(status_text, status_style)]],
        colWidths=[14 * cm],
        rowHeights=[1.5 * cm],
    )
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_bg),
        ("BOX", (0, 0), (-1, -1), 2, status_border),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 10 * mm))

    # Summary section
    story.append(Paragraph("Zusammenfassung", styles["SectionHeader"]))

    # Format type
    file_type_display = "XRechnung" if result.file_type == "xrechnung" else "ZUGFeRD"
    version_info = ""
    if result.xrechnung_version:
        version_info = f" (Version {result.xrechnung_version})"
    elif result.zugferd_profile:
        version_info = f" (Profil: {result.zugferd_profile})"

    summary_data = [
        ["Validierungs-ID:", str(result.id)],
        ["Dateiformat:", f"{file_type_display}{version_info}"],
        ["Datei-Hash (SHA256):", f"{result.file_hash[:32]}..."],
        ["Validiert am:", result.validated_at.strftime("%d.%m.%Y %H:%M:%S") + " UTC"],
        ["Validator-Version:", result.validator_version],
        ["Verarbeitungszeit:", f"{result.processing_time_ms} ms"],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[5 * cm, 11 * cm],
    )
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    # Count boxes
    count_data = [[
        Paragraph(f"<b>{result.error_count}</b><br/><font size='8'>Fehler</font>",
                  ParagraphStyle("ErrorCount", fontSize=14, alignment=1, textColor=ERROR_COLOR)),
        Paragraph(f"<b>{result.warning_count}</b><br/><font size='8'>Warnungen</font>",
                  ParagraphStyle("WarnCount", fontSize=14, alignment=1, textColor=WARNING_COLOR)),
        Paragraph(f"<b>{result.info_count}</b><br/><font size='8'>Hinweise</font>",
                  ParagraphStyle("InfoCount", fontSize=14, alignment=1, textColor=INFO_COLOR)),
    ]]

    count_table = Table(count_data, colWidths=[5.3 * cm, 5.3 * cm, 5.3 * cm])
    count_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f8d7da")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fff3cd")),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#d1ecf1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (0, 0), 1, ERROR_COLOR),
        ("BOX", (1, 0), (1, 0), 1, WARNING_COLOR),
        ("BOX", (2, 0), (2, 0), 1, INFO_COLOR),
    ]))
    story.append(count_table)
    story.append(Spacer(1, 10 * mm))

    # Errors section
    if result.errors:
        story.append(Paragraph("Fehler", styles["SectionHeader"]))
        for error in result.errors:
            error_text = f"<b>[{error.code}]</b> {error.message_de}"
            if error.suggestion:
                error_text += f"<br/><i><font size='9' color='#666666'>Empfehlung: {error.suggestion}</font></i>"

            error_table = Table(
                [[Paragraph(error_text, styles["ErrorItem"])]],
                colWidths=[15.5 * cm],
            )
            error_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8d7da")),
                ("LEFTPADDING", (0, 0), (-1, -1), 15),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
            ]))
            # Add left border effect with another table
            border_table = Table(
                [[" ", error_table]],
                colWidths=[4 * mm, 15.5 * cm],
            )
            border_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), ERROR_COLOR),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 0),
            ]))
            story.append(border_table)
            story.append(Spacer(1, 3 * mm))

    # Warnings section
    if result.warnings:
        story.append(Paragraph("Warnungen", styles["SectionHeader"]))
        for warning in result.warnings:
            warning_text = f"<b>[{warning.code}]</b> {warning.message_de}"

            warning_table = Table(
                [[Paragraph(warning_text, styles["WarningItem"])]],
                colWidths=[15.5 * cm],
            )
            warning_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3cd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 15),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            border_table = Table(
                [[" ", warning_table]],
                colWidths=[4 * mm, 15.5 * cm],
            )
            border_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), WARNING_COLOR),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 0),
            ]))
            story.append(border_table)
            story.append(Spacer(1, 3 * mm))

    # Infos section
    if result.infos:
        story.append(Paragraph("Informationen", styles["SectionHeader"]))
        for info in result.infos:
            info_text = f"<b>[{info.code}]</b> {info.message_de}"

            info_table = Table(
                [[Paragraph(info_text, styles["InfoItem"])]],
                colWidths=[15.5 * cm],
            )
            info_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#d1ecf1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 15),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            border_table = Table(
                [[" ", info_table]],
                colWidths=[4 * mm, 15.5 * cm],
            )
            border_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), INFO_COLOR),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 0),
            ]))
            story.append(border_table)
            story.append(Spacer(1, 3 * mm))

    # Footer
    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph("_" * 80, styles["FooterText"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Erstellt von RechnungsChecker - E-Rechnung Validierung & Konvertierung",
        styles["FooterText"]
    ))
    story.append(Paragraph(
        "Dieser Bericht dient der Information und stellt keine rechtliche Beratung dar.",
        styles["FooterText"]
    ))
    story.append(Paragraph(
        f"Generiert: {datetime.now(UTC).replace(tzinfo=None).strftime('%d.%m.%Y %H:%M:%S')} UTC",
        styles["FooterText"]
    ))

    # Build PDF
    doc.build(story)
    return buffer.getvalue()


def generate_validation_report_html(result: ValidationResponse) -> str:
    """Generate HTML content for validation report (fallback).

    Args:
        result: ValidationResponse to generate report for

    Returns:
        HTML string for the report
    """
    # Determine status styling
    if result.is_valid:
        status_class = "valid"
        status_text = "GÜLTIG"
        status_icon = "&#x2714;"  # Checkmark
    else:
        status_class = "invalid"
        status_text = "UNGÜLTIG"
        status_icon = "&#x2718;"  # X mark

    # Build error list HTML
    errors_html = ""
    if result.errors:
        errors_html = "<h3>Fehler</h3><ul class='error-list'>"
        for error in result.errors:
            suggestion = f"<br><small>Empfehlung: {error.suggestion}</small>" if error.suggestion else ""
            errors_html += f"""
                <li class="error">
                    <strong>[{error.code}]</strong> {error.message_de}
                    {suggestion}
                </li>
            """
        errors_html += "</ul>"

    # Build warning list HTML
    warnings_html = ""
    if result.warnings:
        warnings_html = "<h3>Warnungen</h3><ul class='warning-list'>"
        for warning in result.warnings:
            warnings_html += f"""
                <li class="warning">
                    <strong>[{warning.code}]</strong> {warning.message_de}
                </li>
            """
        warnings_html += "</ul>"

    # Build info list HTML
    infos_html = ""
    if result.infos:
        infos_html = "<h3>Informationen</h3><ul class='info-list'>"
        for info in result.infos:
            infos_html += f"""
                <li class="info">
                    <strong>[{info.code}]</strong> {info.message_de}
                </li>
            """
        infos_html += "</ul>"

    # Format type
    file_type_display = "XRechnung" if result.file_type == "xrechnung" else "ZUGFeRD"
    version_info = ""
    if result.xrechnung_version:
        version_info = f"Version: {result.xrechnung_version}"
    if result.zugferd_profile:
        version_info = f"Profil: {result.zugferd_profile}"

    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Validierungsbericht - RechnungsChecker</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #2C3E50;
            }}
            header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #1A5276; }}
            .subtitle {{ color: #666; }}
            .status-box {{
                text-align: center;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .status-box.valid {{
                background-color: #d4edda;
                border: 2px solid #28B463;
            }}
            .status-box.invalid {{
                background-color: #f8d7da;
                border: 2px solid #E74C3C;
            }}
            .status-icon {{ font-size: 36px; display: block; }}
            .valid .status-icon {{ color: #28B463; }}
            .invalid .status-icon {{ color: #E74C3C; }}
            .status-text {{ font-size: 18px; font-weight: bold; }}
            .valid .status-text {{ color: #1e7e34; }}
            .invalid .status-text {{ color: #c82333; }}
            h2 {{ color: #1A5276; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
            h3 {{ color: #2E86AB; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            td:first-child {{ font-weight: bold; width: 40%; color: #555; }}
            code {{ background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
            .counts {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .count-box {{ text-align: center; padding: 15px 30px; border-radius: 8px; }}
            .count-box.errors {{ background-color: #f8d7da; }}
            .count-box.warnings {{ background-color: #fff3cd; }}
            .count-box.infos {{ background-color: #d1ecf1; }}
            .count-number {{ font-size: 24px; font-weight: bold; }}
            .errors .count-number {{ color: #E74C3C; }}
            .warnings .count-number {{ color: #F39C12; }}
            .infos .count-number {{ color: #2E86AB; }}
            .count-label {{ font-size: 10px; color: #666; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ padding: 12px; margin: 8px 0; border-radius: 4px; border-left: 4px solid; }}
            li.error {{ background-color: #f8d7da; border-left-color: #E74C3C; }}
            li.warning {{ background-color: #fff3cd; border-left-color: #F39C12; }}
            li.info {{ background-color: #d1ecf1; border-left-color: #2E86AB; }}
            footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; font-size: 9px; color: #666; }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo">RechnungsChecker</div>
            <div class="subtitle">Validierungsbericht</div>
        </header>

        <div class="status-box {status_class}">
            <span class="status-icon">{status_icon}</span>
            <span class="status-text">{status_text}</span>
        </div>

        <section class="summary">
            <h2>Zusammenfassung</h2>
            <table class="summary-table">
                <tr>
                    <td>Validierungs-ID:</td>
                    <td><code>{result.id}</code></td>
                </tr>
                <tr>
                    <td>Dateiformat:</td>
                    <td>{file_type_display} {version_info}</td>
                </tr>
                <tr>
                    <td>Datei-Hash (SHA256):</td>
                    <td><code>{result.file_hash[:16]}...</code></td>
                </tr>
                <tr>
                    <td>Validiert am:</td>
                    <td>{result.validated_at.strftime('%d.%m.%Y %H:%M:%S')} UTC</td>
                </tr>
                <tr>
                    <td>Validator-Version:</td>
                    <td>{result.validator_version}</td>
                </tr>
                <tr>
                    <td>Verarbeitungszeit:</td>
                    <td>{result.processing_time_ms} ms</td>
                </tr>
            </table>

            <div class="counts">
                <div class="count-box errors">
                    <div class="count-number">{result.error_count}</div>
                    <div class="count-label">Fehler</div>
                </div>
                <div class="count-box warnings">
                    <div class="count-number">{result.warning_count}</div>
                    <div class="count-label">Warnungen</div>
                </div>
                <div class="count-box infos">
                    <div class="count-number">{result.info_count}</div>
                    <div class="count-label">Hinweise</div>
                </div>
            </div>
        </section>

        <section class="details">
            {errors_html}
            {warnings_html}
            {infos_html}
        </section>

        <footer>
            <p>Erstellt von RechnungsChecker - E-Rechnung Validierung &amp; Konvertierung</p>
            <p>Dieser Bericht dient der Information und stellt keine rechtliche Beratung dar.</p>
            <p class="timestamp">Generiert: {datetime.now(UTC).replace(tzinfo=None).strftime('%d.%m.%Y %H:%M:%S')} UTC</p>
        </footer>
    </body>
    </html>
    """

    return html


class ReportService:
    """Service for generating validation reports."""

    def generate_pdf(self, result: ValidationResponse) -> bytes:
        """Generate PDF report for validation result.

        Args:
            result: ValidationResponse to generate report for

        Returns:
            PDF file content as bytes
        """
        return generate_validation_report_pdf(result)

    def generate_html(self, result: ValidationResponse) -> str:
        """Generate HTML report for validation result.

        Args:
            result: ValidationResponse to generate report for

        Returns:
            HTML string for the report
        """
        return generate_validation_report_html(result)
