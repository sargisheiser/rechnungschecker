"""Internationalization (i18n) support for error messages."""

from typing import Literal

SupportedLanguage = Literal["de", "en"]

# Translation dictionaries for error messages
TRANSLATIONS: dict[str, dict[str, str]] = {
    # Authentication errors
    "auth.invalid_credentials": {
        "de": "E-Mail oder Passwort ist falsch",
        "en": "Email or password is incorrect",
    },
    "auth.email_not_verified": {
        "de": "Bitte verifizieren Sie zuerst Ihre E-Mail-Adresse",
        "en": "Please verify your email address first",
    },
    "auth.token_expired": {
        "de": "Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an",
        "en": "Your session has expired. Please log in again",
    },
    "auth.token_invalid": {
        "de": "Ungueltige Authentifizierung",
        "en": "Invalid authentication",
    },
    "auth.email_already_exists": {
        "de": "Diese E-Mail-Adresse ist bereits registriert",
        "en": "This email address is already registered",
    },
    "auth.password_too_weak": {
        "de": "Das Passwort muss mindestens 8 Zeichen lang sein",
        "en": "Password must be at least 8 characters long",
    },
    "auth.account_disabled": {
        "de": "Dieses Konto wurde deaktiviert",
        "en": "This account has been disabled",
    },
    # Authorization errors
    "authz.insufficient_permissions": {
        "de": "Sie haben keine Berechtigung fuer diese Aktion",
        "en": "You do not have permission for this action",
    },
    "authz.plan_required": {
        "de": "Diese Funktion erfordert ein Upgrade Ihres Plans",
        "en": "This feature requires a plan upgrade",
    },
    "authz.pro_plan_required": {
        "de": "Diese Funktion ist nur im Pro-Plan verfuegbar",
        "en": "This feature is only available in the Pro plan",
    },
    "authz.steuerberater_plan_required": {
        "de": "Diese Funktion ist nur im Steuerberater-Plan verfuegbar",
        "en": "This feature is only available in the Tax Advisor plan",
    },
    # Validation errors
    "validation.file_too_large": {
        "de": "Die Datei ist zu gross. Maximale Groesse: {max_size} MB",
        "en": "File is too large. Maximum size: {max_size} MB",
    },
    "validation.invalid_file_type": {
        "de": "Ungueltige Datei. Bitte laden Sie eine XML- oder PDF-Datei hoch",
        "en": "Invalid file. Please upload an XML or PDF file",
    },
    "validation.processing_failed": {
        "de": "Fehler bei der Verarbeitung der Datei",
        "en": "Error processing the file",
    },
    "validation.xrechnung_invalid": {
        "de": "Die XRechnung entspricht nicht dem Standard",
        "en": "The XRechnung does not conform to the standard",
    },
    "validation.zugferd_invalid": {
        "de": "Die ZUGFeRD-Datei entspricht nicht dem Standard",
        "en": "The ZUGFeRD file does not conform to the standard",
    },
    # Rate limit errors
    "rate_limit.exceeded": {
        "de": "Zu viele Anfragen. Bitte versuchen Sie es spaeter erneut",
        "en": "Too many requests. Please try again later",
    },
    "rate_limit.validation_limit_reached": {
        "de": "Sie haben Ihr monatliches Validierungslimit erreicht",
        "en": "You have reached your monthly validation limit",
    },
    "rate_limit.conversion_limit_reached": {
        "de": "Sie haben Ihr monatliches Konvertierungslimit erreicht",
        "en": "You have reached your monthly conversion limit",
    },
    # API key errors
    "api_key.invalid": {
        "de": "Ungueltiger API-Schluessel",
        "en": "Invalid API key",
    },
    "api_key.expired": {
        "de": "Der API-Schluessel ist abgelaufen",
        "en": "The API key has expired",
    },
    "api_key.limit_reached": {
        "de": "Sie haben die maximale Anzahl an API-Schluesseln erreicht",
        "en": "You have reached the maximum number of API keys",
    },
    # Client errors
    "client.not_found": {
        "de": "Mandant nicht gefunden",
        "en": "Client not found",
    },
    "client.limit_reached": {
        "de": "Sie haben die maximale Anzahl an Mandanten erreicht",
        "en": "You have reached the maximum number of clients",
    },
    # Webhook errors
    "webhook.not_found": {
        "de": "Webhook nicht gefunden",
        "en": "Webhook not found",
    },
    "webhook.limit_reached": {
        "de": "Sie haben die maximale Anzahl an Webhooks erreicht",
        "en": "You have reached the maximum number of webhooks",
    },
    "webhook.delivery_failed": {
        "de": "Webhook-Zustellung fehlgeschlagen",
        "en": "Webhook delivery failed",
    },
    # Integration errors
    "integration.not_configured": {
        "de": "Diese Integration ist nicht konfiguriert",
        "en": "This integration is not configured",
    },
    "integration.connection_failed": {
        "de": "Verbindung zur Integration fehlgeschlagen",
        "en": "Failed to connect to integration",
    },
    # Export errors
    "export.failed": {
        "de": "Export fehlgeschlagen",
        "en": "Export failed",
    },
    "export.no_data": {
        "de": "Keine Daten fuer den Export vorhanden",
        "en": "No data available for export",
    },
    # General errors
    "general.internal_error": {
        "de": "Ein interner Fehler ist aufgetreten. Bitte versuchen Sie es spaeter erneut",
        "en": "An internal error occurred. Please try again later",
    },
    "general.not_found": {
        "de": "Die angeforderte Ressource wurde nicht gefunden",
        "en": "The requested resource was not found",
    },
    "general.bad_request": {
        "de": "Ungueltige Anfrage",
        "en": "Invalid request",
    },
}


def get_translation(
    key: str,
    lang: SupportedLanguage = "de",
    **kwargs: str | int | float,
) -> str:
    """
    Get a translated message by key.

    Args:
        key: The translation key (e.g., "auth.invalid_credentials")
        lang: The target language ("de" or "en")
        **kwargs: Format arguments for the message

    Returns:
        The translated message, or the key itself if not found
    """
    if key not in TRANSLATIONS:
        return key

    translations = TRANSLATIONS[key]
    message = translations.get(lang, translations.get("de", key))

    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass

    return message


def t(
    key: str,
    lang: SupportedLanguage = "de",
    **kwargs: str | int | float,
) -> str:
    """Shorthand for get_translation."""
    return get_translation(key, lang, **kwargs)


def get_language_from_header(accept_language: str | None) -> SupportedLanguage:
    """
    Parse Accept-Language header and return the best matching language.

    Args:
        accept_language: The Accept-Language header value

    Returns:
        The best matching supported language
    """
    if not accept_language:
        return "de"

    # Simple parsing - look for "en" or "de" in the header
    lower = accept_language.lower()
    if "en" in lower:
        # Check if English comes before German
        en_pos = lower.find("en")
        de_pos = lower.find("de")
        if de_pos == -1 or en_pos < de_pos:
            return "en"

    return "de"
