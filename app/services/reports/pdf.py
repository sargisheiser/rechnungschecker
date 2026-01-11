"""PDF report generation service for validation results."""

import io
import logging
from datetime import datetime

from weasyprint import HTML, CSS

from app.schemas.validation import ValidationResponse

logger = logging.getLogger(__name__)


def generate_validation_report_html(result: ValidationResponse) -> str:
    """Generate HTML content for validation report.

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
            <p class="timestamp">Generiert: {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')} UTC</p>
        </footer>
    </body>
    </html>
    """

    return html


def get_report_css() -> str:
    """Get CSS styles for the PDF report."""
    return """
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: "Seite " counter(page) " von " counter(pages);
            font-size: 10px;
            color: #666;
        }
    }

    body {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #2C3E50;
    }

    header {
        text-align: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 2px solid #1A5276;
    }

    .logo {
        font-size: 24pt;
        font-weight: bold;
        color: #1A5276;
    }

    .subtitle {
        font-size: 14pt;
        color: #666;
        margin-top: 5px;
    }

    .status-box {
        text-align: center;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
    }

    .status-box.valid {
        background-color: #d4edda;
        border: 2px solid #28B463;
    }

    .status-box.invalid {
        background-color: #f8d7da;
        border: 2px solid #E74C3C;
    }

    .status-icon {
        font-size: 36pt;
        display: block;
        margin-bottom: 10px;
    }

    .status-box.valid .status-icon {
        color: #28B463;
    }

    .status-box.invalid .status-icon {
        color: #E74C3C;
    }

    .status-text {
        font-size: 18pt;
        font-weight: bold;
    }

    .status-box.valid .status-text {
        color: #1e7e34;
    }

    .status-box.invalid .status-text {
        color: #c82333;
    }

    h2 {
        color: #1A5276;
        border-bottom: 1px solid #ddd;
        padding-bottom: 10px;
        margin-top: 30px;
    }

    h3 {
        color: #2E86AB;
        margin-top: 20px;
    }

    .summary-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }

    .summary-table td {
        padding: 8px;
        border-bottom: 1px solid #eee;
    }

    .summary-table td:first-child {
        font-weight: bold;
        width: 40%;
        color: #555;
    }

    code {
        font-family: 'Courier New', monospace;
        background-color: #f5f5f5;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10pt;
    }

    .counts {
        display: flex;
        justify-content: space-around;
        margin: 30px 0;
    }

    .count-box {
        text-align: center;
        padding: 15px 30px;
        border-radius: 8px;
        min-width: 100px;
    }

    .count-box.errors {
        background-color: #f8d7da;
    }

    .count-box.warnings {
        background-color: #fff3cd;
    }

    .count-box.infos {
        background-color: #d1ecf1;
    }

    .count-number {
        font-size: 24pt;
        font-weight: bold;
    }

    .count-box.errors .count-number {
        color: #E74C3C;
    }

    .count-box.warnings .count-number {
        color: #F39C12;
    }

    .count-box.infos .count-number {
        color: #2E86AB;
    }

    .count-label {
        font-size: 10pt;
        color: #666;
        margin-top: 5px;
    }

    ul {
        list-style-type: none;
        padding: 0;
    }

    li {
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
        border-left: 4px solid;
    }

    li.error {
        background-color: #f8d7da;
        border-left-color: #E74C3C;
    }

    li.warning {
        background-color: #fff3cd;
        border-left-color: #F39C12;
    }

    li.info {
        background-color: #d1ecf1;
        border-left-color: #2E86AB;
    }

    li strong {
        color: #333;
    }

    li small {
        color: #666;
        font-style: italic;
    }

    footer {
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #ddd;
        text-align: center;
        font-size: 9pt;
        color: #666;
    }

    footer p {
        margin: 5px 0;
    }

    .timestamp {
        font-family: monospace;
    }
    """


def generate_validation_report_pdf(result: ValidationResponse) -> bytes:
    """Generate PDF report for validation result.

    Args:
        result: ValidationResponse to generate report for

    Returns:
        PDF file content as bytes
    """
    html_content = generate_validation_report_html(result)
    css = CSS(string=get_report_css())

    # Generate PDF
    html = HTML(string=html_content)
    pdf_buffer = io.BytesIO()
    html.write_pdf(pdf_buffer, stylesheets=[css])

    return pdf_buffer.getvalue()


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
