"""Email sending service."""

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending emails via Mailgun or console (dev mode)."""

    def __init__(self):
        """Initialize email service."""
        self.api_key = settings.mailgun_api_key
        self.domain = settings.mailgun_domain
        self.from_email = settings.email_from
        self.base_url = f"https://api.eu.mailgun.net/v3/{self.domain}/messages"

    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.api_key and self.domain)

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)

        Returns:
            True if email was sent successfully
        """
        if not self.is_configured:
            # Dev mode - log email details
            logger.warning(f"[DEV EMAIL] Mailgun not configured. To: {to}, Subject: {subject}")
            logger.debug(f"[DEV EMAIL] Content preview: {html_content[:500]}...")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    auth=("api", self.api_key),
                    data={
                        "from": f"RechnungsChecker <{self.from_email}>",
                        "to": to,
                        "subject": subject,
                        "html": html_content,
                        "text": text_content or "",
                    },
                )
                response.raise_for_status()
                logger.info(f"Email sent to {to}: {subject}")
                return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

    async def send_verification_email(self, to: str, token: str) -> bool:
        """
        Send email verification email.

        Args:
            to: Recipient email address
            token: Verification token

        Returns:
            True if email was sent successfully
        """
        verification_url = f"{settings.frontend_url}/verifizieren?token={token}"

        # In dev mode, log verification URL
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Verification link for {to}: {verification_url}")

        subject = "Bitte bestätigen Sie Ihre E-Mail-Adresse - RechnungsChecker"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #2563eb; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; }}
                .button {{
                    display: inline-block;
                    padding: 14px 30px;
                    background-color: #2563eb;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .button:hover {{ background-color: #1d4ed8; }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .link {{ word-break: break-all; color: #2563eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <h2>Willkommen bei RechnungsChecker!</h2>
                    <p>Vielen Dank für Ihre Registrierung. Bitte bestätigen Sie Ihre E-Mail-Adresse,
                    um Ihr Konto zu aktivieren.</p>

                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">E-Mail bestätigen</a>
                    </p>

                    <p>Falls der Button nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:</p>
                    <p class="link">{verification_url}</p>

                    <p><strong>Dieser Link ist 24 Stunden gültig.</strong></p>

                    <p>Falls Sie sich nicht bei RechnungsChecker registriert haben,
                    können Sie diese E-Mail ignorieren.</p>
                </div>
                <div class="footer">
                    <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
                    <p>&copy; 2024 RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Willkommen bei RechnungsChecker!

Vielen Dank für Ihre Registrierung. Bitte bestätigen Sie Ihre E-Mail-Adresse,
um Ihr Konto zu aktivieren.

Klicken Sie auf diesen Link zur Bestätigung:
{verification_url}

Dieser Link ist 24 Stunden gültig.

Falls Sie sich nicht bei RechnungsChecker registriert haben,
können Sie diese E-Mail ignorieren.

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)

    async def send_verification_code_email(self, to: str, code: str) -> bool:
        """
        Send email verification code.

        Args:
            to: Recipient email address
            code: 6-digit verification code

        Returns:
            True if email was sent successfully
        """
        # In dev mode, log verification code
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Verification code for {to}: {code}")

        subject = "Ihr Verifizierungscode - RechnungsChecker"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #2563eb; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; text-align: center; }}
                .code-box {{
                    display: inline-block;
                    padding: 20px 40px;
                    background-color: #f3f4f6;
                    border-radius: 12px;
                    margin: 20px 0;
                }}
                .code {{
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #2563eb;
                    font-family: monospace;
                }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <h2>Willkommen bei RechnungsChecker!</h2>
                    <p>Vielen Dank für Ihre Registrierung. Bitte geben Sie den folgenden Code ein, um Ihre E-Mail-Adresse zu bestätigen:</p>

                    <div class="code-box">
                        <span class="code">{code}</span>
                    </div>

                    <p><strong>Dieser Code ist 15 Minuten gültig.</strong></p>

                    <p>Falls Sie sich nicht bei RechnungsChecker registriert haben,
                    können Sie diese E-Mail ignorieren.</p>
                </div>
                <div class="footer">
                    <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
                    <p>&copy; 2024 RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Willkommen bei RechnungsChecker!

Vielen Dank für Ihre Registrierung. Bitte geben Sie den folgenden Code ein,
um Ihre E-Mail-Adresse zu bestätigen:

Ihr Verifizierungscode: {code}

Dieser Code ist 15 Minuten gültig.

Falls Sie sich nicht bei RechnungsChecker registriert haben,
können Sie diese E-Mail ignorieren.

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)

    async def send_password_reset_email(self, to: str, token: str) -> bool:
        """
        Send password reset email.

        Args:
            to: Recipient email address
            token: Password reset token

        Returns:
            True if email was sent successfully
        """
        reset_url = f"{settings.frontend_url}/passwort-zuruecksetzen?token={token}"

        # In dev mode, log reset URL
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Password reset link for {to}: {reset_url}")

        subject = "Passwort zurücksetzen - RechnungsChecker"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #2563eb; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; }}
                .button {{
                    display: inline-block;
                    padding: 14px 30px;
                    background-color: #2563eb;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .link {{ word-break: break-all; color: #2563eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <h2>Passwort zurücksetzen</h2>
                    <p>Sie haben angefordert, Ihr Passwort zurückzusetzen.
                    Klicken Sie auf den Button unten, um ein neues Passwort zu erstellen.</p>

                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Passwort zurücksetzen</a>
                    </p>

                    <p>Falls der Button nicht funktioniert, kopieren Sie diesen Link in Ihren Browser:</p>
                    <p class="link">{reset_url}</p>

                    <p><strong>Dieser Link ist 1 Stunde gültig.</strong></p>

                    <p>Falls Sie kein neues Passwort angefordert haben,
                    können Sie diese E-Mail ignorieren. Ihr Passwort bleibt unverändert.</p>
                </div>
                <div class="footer">
                    <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
                    <p>&copy; 2024 RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Passwort zurücksetzen

Sie haben angefordert, Ihr Passwort zurückzusetzen.
Klicken Sie auf den folgenden Link, um ein neues Passwort zu erstellen:

{reset_url}

Dieser Link ist 1 Stunde gültig.

Falls Sie kein neues Passwort angefordert haben,
können Sie diese E-Mail ignorieren. Ihr Passwort bleibt unverändert.

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)


    async def send_payment_failed_email(self, to: str, invoice_id: str) -> bool:
        """
        Send payment failed notification email.

        Args:
            to: Recipient email address
            invoice_id: Stripe invoice ID

        Returns:
            True if email was sent successfully
        """
        # In dev mode, log notification
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Payment failed notification for {to}, invoice: {invoice_id}")

        subject = "Zahlung fehlgeschlagen - RechnungsChecker"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #dc2626; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; }}
                .alert {{
                    background-color: #fef2f2;
                    border: 1px solid #fecaca;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 20px 0;
                }}
                .alert-title {{
                    color: #dc2626;
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 30px;
                    background-color: #2563eb;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <div class="alert">
                        <div class="alert-title">Zahlung fehlgeschlagen</div>
                        <p>Leider konnte Ihre letzte Zahlung nicht verarbeitet werden.</p>
                    </div>

                    <p>Bitte aktualisieren Sie Ihre Zahlungsinformationen, um eine Unterbrechung
                    Ihres Dienstes zu vermeiden.</p>

                    <p style="text-align: center;">
                        <a href="{settings.frontend_url}/dashboard/abrechnung" class="button">
                            Zahlungsmethode aktualisieren
                        </a>
                    </p>

                    <p>Falls Sie Fragen haben, kontaktieren Sie uns unter
                    <a href="mailto:support@rechnungschecker.de">support@rechnungschecker.de</a>.</p>

                    <p><small>Rechnungsnummer: {invoice_id}</small></p>
                </div>
                <div class="footer">
                    <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
                    <p>&copy; 2024 RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Zahlung fehlgeschlagen

Leider konnte Ihre letzte Zahlung nicht verarbeitet werden.

Bitte aktualisieren Sie Ihre Zahlungsinformationen, um eine Unterbrechung
Ihres Dienstes zu vermeiden.

Zahlungsmethode aktualisieren:
{settings.frontend_url}/dashboard/abrechnung

Falls Sie Fragen haben, kontaktieren Sie uns unter support@rechnungschecker.de.

Rechnungsnummer: {invoice_id}

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)

    async def send_usage_alert_email(self, to: str, usage_percent: int, plan: str, limit: int) -> bool:
        """
        Send usage alert when approaching limit.

        Args:
            to: Recipient email address
            usage_percent: Current usage percentage
            plan: User's plan name
            limit: Monthly limit

        Returns:
            True if email was sent successfully
        """
        # In dev mode, log notification
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Usage alert for {to}: {usage_percent}% of {plan}")

        subject = f"Nutzungslimit fast erreicht ({usage_percent}%) - RechnungsChecker"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #f59e0b; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; }}
                .alert {{
                    background-color: #fffbeb;
                    border: 1px solid #fcd34d;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 20px 0;
                }}
                .progress-bar {{
                    background-color: #e5e7eb;
                    border-radius: 9999px;
                    height: 24px;
                    overflow: hidden;
                    margin: 16px 0;
                }}
                .progress-fill {{
                    background-color: #f59e0b;
                    height: 100%;
                    width: {usage_percent}%;
                    border-radius: 9999px;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 30px;
                    background-color: #2563eb;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <div class="alert">
                        <h2 style="margin-top: 0;">Ihr monatliches Limit ist fast erreicht</h2>
                        <p>Sie haben <strong>{usage_percent}%</strong> Ihres monatlichen Validierungskontingents verbraucht.</p>
                    </div>

                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>

                    <p><strong>Ihr aktueller Plan:</strong> {plan}</p>
                    <p><strong>Monatliches Limit:</strong> {limit} Validierungen</p>

                    <p>Upgraden Sie Ihren Plan, um unbegrenzte Validierungen zu erhalten:</p>

                    <p style="text-align: center;">
                        <a href="{settings.frontend_url}/preise" class="button">Jetzt upgraden</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
                    <p>&copy; 2024 RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Ihr monatliches Limit ist fast erreicht

Sie haben {usage_percent}% Ihres monatlichen Validierungskontingents verbraucht.

Ihr aktueller Plan: {plan}
Monatliches Limit: {limit} Validierungen

Upgraden Sie Ihren Plan, um unbegrenzte Validierungen zu erhalten:
{settings.frontend_url}/preise

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)

    async def send_batch_complete_email(
        self,
        to: str,
        job_name: str,
        total_files: int,
        successful_count: int,
        failed_count: int,
        valid_count: int,
        invalid_count: int,
    ) -> bool:
        """
        Send batch validation completion notification.

        Args:
            to: Recipient email address
            job_name: Name of the batch job
            total_files: Total number of files
            successful_count: Successfully processed files
            failed_count: Failed files
            valid_count: Valid invoices
            invalid_count: Invalid invoices

        Returns:
            True if email was sent successfully
        """
        # In dev mode, log notification
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Batch complete for {to}: {job_name} - Total: {total_files}, Valid: {valid_count}, Invalid: {invalid_count}")

        status_emoji = "🎉" if failed_count == 0 else "⚠️"
        subject = f"{status_emoji} Stapelvalidierung abgeschlossen: {job_name}"

        success_rate = round(successful_count / total_files * 100, 1) if total_files > 0 else 0
        valid_rate = round(valid_count / successful_count * 100, 1) if successful_count > 0 else 0

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #22c55e; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 16px;
                    margin: 20px 0;
                }}
                .stat-box {{
                    background-color: #f9fafb;
                    border-radius: 8px;
                    padding: 16px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #111827;
                }}
                .stat-label {{
                    font-size: 14px;
                    color: #6b7280;
                }}
                .success {{ color: #22c55e; }}
                .error {{ color: #ef4444; }}
                .button {{
                    display: inline-block;
                    padding: 14px 30px;
                    background-color: #2563eb;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <h2>Stapelvalidierung abgeschlossen</h2>
                    <p><strong>Auftrag:</strong> {job_name}</p>

                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-value">{total_files}</div>
                            <div class="stat-label">Dateien gesamt</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value success">{successful_count}</div>
                            <div class="stat-label">Verarbeitet</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value success">{valid_count}</div>
                            <div class="stat-label">Gueltig</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value error">{invalid_count}</div>
                            <div class="stat-label">Ungueltig</div>
                        </div>
                    </div>

                    <p><strong>Erfolgsrate:</strong> {success_rate}% verarbeitet, {valid_rate}% gueltig</p>

                    <p style="text-align: center;">
                        <a href="{settings.frontend_url}/batch" class="button">Ergebnisse anzeigen</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
                    <p>&copy; 2024 RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Stapelvalidierung abgeschlossen

Auftrag: {job_name}

Ergebnis:
- Dateien gesamt: {total_files}
- Verarbeitet: {successful_count}
- Fehlgeschlagen: {failed_count}
- Gueltig: {valid_count}
- Ungueltig: {invalid_count}

Erfolgsrate: {success_rate}% verarbeitet, {valid_rate}% gueltig

Ergebnisse anzeigen:
{settings.frontend_url}/batch

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)


    async def send_invoice_email(
        self,
        to: str,
        sender_name: str,
        invoice_number: str,
        invoice_date: str,
        gross_amount: str,
        currency: str,
        output_format: str,
        file_content: bytes,
        filename: str,
    ) -> bool:
        """
        Send converted invoice via email with attachment.

        Args:
            to: Recipient email address
            sender_name: Name of the sender/company
            invoice_number: Invoice number
            invoice_date: Invoice date
            gross_amount: Total amount
            currency: Currency code (e.g., EUR)
            output_format: Format type (XRechnung or ZUGFeRD)
            file_content: Binary content of the invoice file
            filename: Name of the attachment file

        Returns:
            True if email was sent successfully
        """
        # In dev mode, log notification
        if not self.is_configured:
            logger.warning(f"[DEV EMAIL] Invoice email to {to}: {invoice_number} from {sender_name}, {gross_amount} {currency}, format: {output_format}")
            return True

        subject = f"Ihre E-Rechnung: {invoice_number}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #2563eb; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .content {{ padding: 30px 0; }}
                .invoice-details {{
                    background-color: #f9fafb;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .invoice-details table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .invoice-details td {{
                    padding: 8px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .invoice-details td:first-child {{
                    color: #6b7280;
                    width: 40%;
                }}
                .invoice-details td:last-child {{
                    font-weight: 500;
                    text-align: right;
                }}
                .invoice-details tr:last-child td {{
                    border-bottom: none;
                }}
                .format-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    background-color: #dbeafe;
                    color: #1d4ed8;
                    border-radius: 9999px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                .attachment-info {{
                    background-color: #ecfdf5;
                    border: 1px solid #a7f3d0;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .footer {{
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">RechnungsChecker</div>
                </div>
                <div class="content">
                    <p>Guten Tag,</p>

                    <p>anbei erhalten Sie die E-Rechnung <strong>{invoice_number}</strong> vom {invoice_date}.</p>

                    <div class="invoice-details">
                        <table>
                            <tr>
                                <td>Rechnungsnummer</td>
                                <td>{invoice_number}</td>
                            </tr>
                            <tr>
                                <td>Rechnungsdatum</td>
                                <td>{invoice_date}</td>
                            </tr>
                            <tr>
                                <td>Betrag</td>
                                <td><strong>{gross_amount} {currency}</strong></td>
                            </tr>
                            <tr>
                                <td>Format</td>
                                <td><span class="format-badge">{output_format}</span></td>
                            </tr>
                        </table>
                    </div>

                    <div class="attachment-info">
                        <p style="margin: 0;">📎 Die Rechnung ist als Anhang beigefuegt: <strong>{filename}</strong></p>
                    </div>

                    <p>Mit freundlichen Gruessen<br><strong>{sender_name}</strong></p>
                </div>
                <div class="footer">
                    <p>Gesendet ueber RechnungsChecker - E-Rechnung Validierung & Konvertierung</p>
                    <p><a href="https://rechnungschecker.de">rechnungschecker.de</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
Guten Tag,

anbei erhalten Sie die E-Rechnung {invoice_number} vom {invoice_date}.

Rechnungsdetails:
- Rechnungsnummer: {invoice_number}
- Rechnungsdatum: {invoice_date}
- Betrag: {gross_amount} {currency}
- Format: {output_format}

Die Rechnung ist als Anhang beigefuegt: {filename}

Mit freundlichen Gruessen
{sender_name}

---
Gesendet ueber RechnungsChecker
https://rechnungschecker.de
        """

        # Send email with attachment
        try:
            async with httpx.AsyncClient() as client:
                # Determine content type based on filename
                if filename.endswith('.pdf'):
                    content_type = 'application/pdf'
                else:
                    content_type = 'application/xml'

                response = await client.post(
                    self.base_url,
                    auth=("api", self.api_key),
                    data={
                        "from": f"RechnungsChecker <{self.from_email}>",
                        "to": to,
                        "subject": subject,
                        "html": html_content,
                        "text": text_content,
                    },
                    files={
                        "attachment": (filename, file_content, content_type),
                    },
                )
                response.raise_for_status()
                logger.info(f"Invoice email sent to {to}: {invoice_number}")
                return True
        except Exception as e:
            logger.error(f"Failed to send invoice email to {to}: {e}")
            return False


# Singleton instance
email_service = EmailService()
