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
            # Dev mode - log to console with high visibility
            print("\n" + "=" * 60)
            print("[DEV EMAIL] - Mailgun not configured, logging email:")
            print("=" * 60)
            print(f"To: {to}")
            print(f"Subject: {subject}")
            print("-" * 60)
            print(f"Content preview: {html_content[:500]}...")
            print("=" * 60 + "\n")
            logger.info(f"[DEV EMAIL] To: {to}, Subject: {subject}")
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
        # In production, use actual frontend URL
        verification_url = f"http://localhost:3000/verifizieren?token={token}"

        # In dev mode, print verification URL prominently
        if not self.is_configured:
            print("\n" + "*" * 60)
            print("*  EMAIL VERIFICATION LINK (DEV MODE)")
            print("*" * 60)
            print(f"*  Email: {to}")
            print(f"*  ")
            print(f"*  Click here to verify:")
            print(f"*  {verification_url}")
            print("*" * 60 + "\n")

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
        # In dev mode, print verification code prominently
        if not self.is_configured:
            print("\n" + "*" * 60)
            print("*  EMAIL VERIFICATION CODE (DEV MODE)")
            print("*" * 60)
            print(f"*  Email: {to}")
            print(f"*  ")
            print(f"*  Your verification code is: {code}")
            print("*" * 60 + "\n")

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
        reset_url = f"http://localhost:3000/passwort-zuruecksetzen?token={token}"

        # In dev mode, print reset URL prominently
        if not self.is_configured:
            print("\n" + "*" * 60)
            print("*  PASSWORD RESET LINK (DEV MODE)")
            print("*" * 60)
            print(f"*  Email: {to}")
            print(f"*  ")
            print(f"*  Click here to reset password:")
            print(f"*  {reset_url}")
            print("*" * 60 + "\n")

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
        # In dev mode, print notification prominently
        if not self.is_configured:
            print("\n" + "*" * 60)
            print("*  PAYMENT FAILED NOTIFICATION (DEV MODE)")
            print("*" * 60)
            print(f"*  Email: {to}")
            print(f"*  Invoice: {invoice_id}")
            print("*" * 60 + "\n")

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
                        <a href="http://localhost:3000/dashboard/abrechnung" class="button">
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
http://localhost:3000/dashboard/abrechnung

Falls Sie Fragen haben, kontaktieren Sie uns unter support@rechnungschecker.de.

Rechnungsnummer: {invoice_id}

---
RechnungsChecker - E-Rechnung Validierung & Konvertierung
        """

        return await self.send_email(to, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()
