"""German error messages for KoSIT validation rules.

This module provides German translations for XRechnung validation errors.
Based on official KoSIT/XRechnung business rules.
"""

# German translations for XRechnung business rules (BR-DE-*)
GERMAN_MESSAGES: dict[str, str] = {
    # XRechnung specific rules (BR-DE)
    "BR-DE-01": "Eine Rechnung muss eine Leitweg-ID enthalten.",
    "BR-DE-02": "Die Bankverbindungsinformationen des Verkäufers müssen angegeben werden, wenn Lastschrift oder Überweisung als Zahlungsmittel vereinbart wurde.",
    "BR-DE-03": "Wenn Skonto gewährt wird, müssen die Skontobedingungen im Element Zahlungsbedingungen angegeben werden.",
    "BR-DE-04": "Die Umsatzsteuer-Identifikationsnummer des Verkäufers muss angegeben werden.",
    "BR-DE-05": "Die Kontaktinformationen des Verkäufers müssen eine Telefonnummer oder E-Mail-Adresse enthalten.",
    "BR-DE-06": "Die E-Mail-Adresse des Verkäufers muss angegeben werden.",
    "BR-DE-07": "Die Telefonnummer des Verkäufers muss angegeben werden.",
    "BR-DE-08": "Die IBAN muss in einem gültigen Format angegeben werden.",
    "BR-DE-09": "Das Fälligkeitsdatum der Zahlung muss angegeben werden.",
    "BR-DE-10": "Die BIC (Bank Identifier Code) muss angegeben werden.",
    "BR-DE-11": "Der Verwendungszweck muss angegeben werden.",
    "BR-DE-13": "Der Umsatzsteuerbetrag muss korrekt berechnet sein.",
    "BR-DE-14": "Die Rechnungsnummer darf nicht leer sein.",
    "BR-DE-15": "Das Rechnungsdatum muss angegeben werden.",
    "BR-DE-16": "Eine Rechnung muss mindestens eine Rechnungsposition enthalten.",
    "BR-DE-17": "Die Menge der Rechnungsposition muss angegeben werden.",
    "BR-DE-18": "Der Einzelpreis der Rechnungsposition muss angegeben werden.",
    "BR-DE-19": "Die Beschreibung der Rechnungsposition muss angegeben werden.",
    "BR-DE-20": "Der Lieferort muss auf Dokumentenebene angegeben werden.",
    "BR-DE-21": "Die Leitweg-ID hat ein ungültiges Format. Erwartet: 04011000-1234512345-06 oder ähnlich.",
    "BR-DE-22": "Die E-Mail-Adresse des Käufers sollte angegeben werden.",
    "BR-DE-23": "Der Rechnungstyp-Code muss gültig sein.",
    "BR-DE-24": "Die Währung muss EUR sein oder ein Wechselkurs angegeben werden.",
    "BR-DE-25": "Die Dokumentenebene für Abzüge und Zuschläge muss korrekt sein.",
    "BR-DE-26": "Der Steuerbefreiungsgrund muss angegeben werden, wenn keine Steuer berechnet wird.",
    "BR-DE-27": "Die Steuer-ID des Käufers muss angegeben werden bei innergemeinschaftlichen Lieferungen.",
    "BR-DE-28": "Der Ländercode muss ein gültiger ISO 3166-1 Alpha-2 Code sein.",
    "BR-DE-29": "Die Postleitzahl muss dem Format des jeweiligen Landes entsprechen.",

    # EN16931 Core Business Rules (BR-*)
    "BR-01": "Eine Rechnung muss eine eindeutige Rechnungsnummer enthalten.",
    "BR-02": "Eine Rechnung muss ein Rechnungsdatum enthalten.",
    "BR-03": "Eine Rechnung muss einen Rechnungstyp-Code enthalten.",
    "BR-04": "Eine Rechnung muss einen Währungscode enthalten.",
    "BR-05": "Eine Rechnung muss den Namen des Verkäufers enthalten.",
    "BR-06": "Eine Rechnung muss den Namen des Käufers enthalten.",
    "BR-07": "Eine Rechnung muss den Ländercode des Verkäufers enthalten.",
    "BR-08": "Eine Rechnung muss den Ländercode des Käufers enthalten.",
    "BR-09": "Eine Rechnung muss mindestens eine Rechnungsposition enthalten.",
    "BR-10": "Eine Rechnung muss den Nettobetrag angeben.",
    "BR-11": "Eine Rechnung muss den Gesamtsteuerbetrag angeben.",
    "BR-12": "Eine Rechnung muss den Bruttobetrag angeben.",
    "BR-13": "Eine Rechnung muss den fälligen Betrag angeben.",
    "BR-14": "Die Rechnungsposition muss eine Positionsnummer haben.",
    "BR-15": "Die Rechnungsposition muss eine Menge haben.",
    "BR-16": "Die Rechnungsposition muss eine Mengeneinheit haben.",
    "BR-17": "Die Rechnungsposition muss einen Nettopreis haben.",
    "BR-18": "Die Rechnungsposition muss einen Steuersatz haben.",
    "BR-19": "Die Positionssumme muss korrekt berechnet sein.",
    "BR-20": "Die Steuersumme muss korrekt berechnet sein.",

    # Calculation rules
    "BR-CO-03": "Der Steuerbetrag pro Kategorie muss korrekt berechnet sein.",
    "BR-CO-04": "Die Bemessungsgrundlage muss korrekt berechnet sein.",
    "BR-CO-05": "Die Summe der Nettowerte muss dem Dokumentennettowert entsprechen.",
    "BR-CO-10": "Die Summe aller Steuern muss dem Gesamtsteuerbetrag entsprechen.",
    "BR-CO-11": "Die Summe aus Nettobetrag und Steuerbetrag muss dem Bruttobetrag entsprechen.",
    "BR-CO-12": "Der fällige Betrag muss korrekt berechnet sein.",
    "BR-CO-13": "Der Nettobetrag der Position muss Menge × Einzelpreis sein.",
    "BR-CO-15": "Der Einzelpreis muss positiv oder null sein.",
    "BR-CO-16": "Die Menge muss positiv sein.",
    "BR-CO-17": "Der Rabatt darf nicht größer als der Positionspreis sein.",

    # Format validations
    "BR-S-01": "Die Summe der Beträge je Steuerkategorie muss korrekt sein.",
    "BR-S-08": "Bei Steuerkategorie S muss ein gültiger Steuersatz angegeben werden.",
    "BR-AE-01": "Bei innergemeinschaftlicher Lieferung muss die Steuer-ID des Käufers angegeben werden.",
    "BR-AE-02": "Bei Steuerkategorie AE muss der Steuersatz 0 sein.",
    "BR-E-01": "Bei steuerbefreiten Umsätzen muss ein Befreiungsgrund angegeben werden.",
    "BR-E-02": "Bei Steuerkategorie E muss der Steuersatz 0 sein.",
    "BR-G-01": "Bei Ausfuhrlieferungen muss ein Befreiungsgrund angegeben werden.",
    "BR-G-02": "Bei Steuerkategorie G muss der Steuersatz 0 sein.",

    # UBL specific rules
    "UBL-CR-001": "Ungültiges UBL-Format erkannt.",
    "UBL-CR-002": "UBL Version nicht unterstützt.",
    "UBL-CR-003": "Ungültiges UBL-Element gefunden.",
    "UBL-SR-001": "Unerwartetes Element im UBL-Dokument.",
    "UBL-SR-002": "Erforderliches UBL-Element fehlt.",

    # CII specific rules
    "CII-SR-001": "Ungültiges CII-Format erkannt.",
    "CII-SR-002": "Erforderliches CII-Element fehlt.",
    "CII-SR-003": "CII Version nicht unterstützt.",
    "CII-SR-004": "Das CII-Dokument enthält ungültige Elemente.",
    "CII-SR-005": "Die CII-Dokumentstruktur ist fehlerhaft.",

    # Additional BR rules (21-50)
    "BR-21": "Die Rechnungsposition muss eine Artikelkennung oder Beschreibung haben.",
    "BR-22": "Die Rechnungsposition muss einen Nettopositionsbetrag haben.",
    "BR-23": "Eine Rechnungsposition muss die Rechnungspositionsmenge angeben.",
    "BR-24": "Eine Rechnungsposition muss den Einzelpreis angeben.",
    "BR-25": "Der Dokumentennettobetrag muss berechnet werden können.",
    "BR-26": "Der Gesamtsteuerbetrag muss berechnet werden können.",
    "BR-27": "Der Rechnungsendbetrag muss berechnet werden können.",
    "BR-28": "Der zu zahlende Betrag muss berechnet werden können.",
    "BR-29": "Der Lieferort muss einen Ländercode enthalten.",
    "BR-30": "Die Käuferadresse muss einen Ländercode enthalten.",
    "BR-31": "Die Verkäuferadresse muss einen Ländercode enthalten.",
    "BR-32": "Die Steuervertretungsadresse muss einen Ländercode enthalten.",
    "BR-33": "Der Steuerbetrag je Kategorie muss angegeben werden.",
    "BR-34": "Die Steuerbemessungsgrundlage je Kategorie muss angegeben werden.",
    "BR-35": "Die Steuerkategorie muss einen Code haben.",
    "BR-36": "Die Steuerkategorie muss einen Steuersatz haben.",
    "BR-37": "Die Steuerkategorie muss ein Steuerschema haben.",
    "BR-38": "Die Positionssteuerkategorie muss einen Code haben.",
    "BR-39": "Die Positionssteuerkategorie muss ein Steuerschema haben.",
    "BR-40": "Die Positionssteuerkategorie muss einen Steuersatz haben.",
    "BR-41": "Die Anzahlung muss einen Betrag haben.",
    "BR-42": "Die Anzahlung muss eine Steuerkategorie haben.",
    "BR-43": "Der Abzug muss einen Betrag haben.",
    "BR-44": "Der Abzug muss eine Steuerkategorie haben.",
    "BR-45": "Die Steuerkennung des Verkäufers muss angegeben werden.",
    "BR-46": "Die Steuerkennung des Käufers muss bei bestimmten Kategorien angegeben werden.",
    "BR-47": "Der Zahlungsempfänger muss identifizierbar sein.",
    "BR-48": "Die Bankverbindung muss vollständig sein.",
    "BR-49": "Das Fälligkeitsdatum darf nicht in der Vergangenheit liegen.",
    "BR-50": "Der Rechnungstyp muss gültig sein.",

    # Additional calculation rules
    "BR-CO-01": "Die Summe der Positionsnettobeträge muss korrekt sein.",
    "BR-CO-02": "Die Summe der Zuschläge auf Dokumentenebene muss korrekt sein.",
    "BR-CO-06": "Der Steuerbetrag muss korrekt berechnet sein.",
    "BR-CO-07": "Der Gesamtbetrag muss korrekt sein.",
    "BR-CO-08": "Der zu zahlende Betrag muss korrekt sein.",
    "BR-CO-09": "Die Steuerbemessungsgrundlage muss berechnet werden können.",
    "BR-CO-14": "Der Positionsnettobetrag muss korrekt berechnet sein.",
    "BR-CO-18": "Der Steuersatz muss als Dezimalzahl angegeben werden.",
    "BR-CO-19": "Die Mengeneinheit muss ein gültiger UN/ECE Code sein.",
    "BR-CO-20": "Der Währungscode muss ein gültiger ISO 4217 Code sein.",
    "BR-CO-21": "Der Ländercode muss ein gültiger ISO 3166-1 Code sein.",

    # Tax category specific rules
    "BR-IC-01": "Bei innergemeinschaftlicher Lieferung muss der Steuersatz 0% sein.",
    "BR-IC-02": "Bei innergemeinschaftlicher Lieferung muss die USt-ID des Käufers angegeben werden.",
    "BR-IC-03": "Bei innergemeinschaftlicher Lieferung muss ein Befreiungsgrund angegeben werden.",
    "BR-O-01": "Bei nicht steuerbaren Umsätzen muss der Steuersatz 0% sein.",
    "BR-O-02": "Bei nicht steuerbaren Umsätzen muss ein Grund angegeben werden.",
    "BR-Z-01": "Bei Nullsteuersatz muss der Steuersatz 0% sein.",
    "BR-Z-02": "Bei Nullsteuersatz muss ein Befreiungsgrund angegeben werden.",

    # ZUGFeRD/Factur-X specific
    "FX-001": "Das Factur-X-Profil konnte nicht erkannt werden.",
    "FX-002": "Die eingebettete XML-Datei entspricht nicht dem Factur-X-Standard.",
    "FX-003": "Das PDF/A-Format ist ungültig oder nicht kompatibel.",
    "ZF-001": "Das ZUGFeRD-Profil konnte nicht erkannt werden.",
    "ZF-002": "Die eingebettete XML-Datei entspricht nicht dem ZUGFeRD-Standard.",
    "ZF-003": "Die ZUGFeRD-Version wird nicht unterstützt.",
    "ZUGFERD-PROFILE-DEPRECATED": "Das verwendete ZUGFeRD-Profil ist veraltet.",
    "ZUGFERD-PROFILE-UNKNOWN": "Das ZUGFeRD-Profil konnte nicht erkannt werden.",

    # Peppol specific
    "PEPPOL-EN16931-R001": "Der Rechnungstyp muss gültig sein.",
    "PEPPOL-EN16931-R002": "Die Währung muss angegeben werden.",
    "PEPPOL-EN16931-R003": "Der Dokumentencode muss gültig sein.",
    "PEPPOL-EN16931-R004": "Die Käuferreferenz muss angegeben werden.",
    "PEPPOL-EN16931-R005": "Die Verkäuferkennung muss angegeben werden.",

    # Schema validation
    "SCH-001": "Das Dokument entspricht nicht dem erwarteten Schema.",
    "SCH-002": "Ein erforderliches Element fehlt im Dokument.",
    "SCH-003": "Ein Element enthält einen ungültigen Wert.",
    "SCH-004": "Die Elementreihenfolge ist ungültig.",
    "SCH-005": "Ein unbekanntes Element wurde gefunden.",

    # Generic/fallback
    "PARSE-ERROR": "Die XML-Datei konnte nicht gelesen werden.",
    "FORMAT-UNKNOWN": "Das Dateiformat wurde nicht erkannt.",
    "FALLBACK-MODE": "Eingeschränkte Validierung aktiv - vollständige Prüfung nicht verfügbar.",
    "XML-PARSE": "Die XML-Struktur ist ungültig.",
    "PDF-PARSE": "Die PDF-Datei konnte nicht gelesen werden.",
    "PDF-NO-XML": "Keine eingebettete XML-Datei in der PDF gefunden.",
    "TIMEOUT": "Die Validierung wurde wegen Zeitüberschreitung abgebrochen.",
    "INTERNAL-ERROR": "Ein interner Fehler ist aufgetreten.",
}


def get_german_message(code: str, fallback: str | None = None) -> str:
    """Get German error message for a validation code.

    Args:
        code: The validation rule code (e.g., BR-DE-01)
        fallback: Optional fallback message if code not found

    Returns:
        German error message
    """
    # Try exact match
    if code in GERMAN_MESSAGES:
        return GERMAN_MESSAGES[code]

    # Try to find partial match (e.g., for BR-DE-01-01 -> BR-DE-01)
    for known_code in GERMAN_MESSAGES:
        if code.startswith(known_code):
            return GERMAN_MESSAGES[known_code]

    # Use fallback or generate generic message
    if fallback:
        return fallback

    return f"Validierungsfehler: {code}"
