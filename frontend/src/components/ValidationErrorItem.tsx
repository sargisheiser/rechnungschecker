import { useState } from 'react'
import {
  XCircle,
  AlertTriangle,
  Info,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Code,
  ExternalLink,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ValidationError } from '@/types'

// German explanations for common XRechnung/ZUGFeRD error codes
const ERROR_EXPLANATIONS: Record<string, { title: string; explanation: string; fix?: string; docLink?: string }> = {
  // === EN16931 Business Rules (BR-CO-*) ===
  'BR-CO-10': {
    title: 'Steuersumme stimmt nicht überein',
    explanation: 'Die Summe aller einzelnen Steuerbeträge muss dem Gesamtsteuerbetrag entsprechen.',
    fix: 'Prüfen Sie: Nettosumme aller Positionen + MwSt-Summe = Bruttosumme. Runden Sie Zwischenergebnisse kaufmännisch auf 2 Nachkommastellen.',
  },
  'BR-CO-13': {
    title: 'Fälligkeitsdatum vor Rechnungsdatum',
    explanation: 'Das Zahlungsfälligkeitsdatum darf nicht vor dem Rechnungsdatum liegen.',
    fix: 'Korrigieren Sie das Fälligkeitsdatum (BT-9) oder das Rechnungsdatum (BT-2).',
  },
  'BR-CO-15': {
    title: 'Negativer Einzelpreis',
    explanation: 'Der Nettoeinzelpreis eines Artikels muss positiv oder null sein.',
    fix: 'Verwenden Sie für Gutschriften/Rabatte die Zuschläge/Abzüge (Allowances/Charges) anstatt negativer Preise.',
  },
  'BR-CO-16': {
    title: 'Summe der Positionsnettobeträge falsch',
    explanation: 'Die Summe aller Positionsnettobeträge stimmt nicht mit der Rechnungssumme überein.',
    fix: 'Prüfen Sie: Summe(Positionsnetto) = Rechnungsnetto vor Zu-/Abschlägen.',
  },
  'BR-CO-25': {
    title: 'Zahlungsziel fehlt',
    explanation: 'Bei positivem Zahlbetrag muss entweder ein Fälligkeitsdatum oder Zahlungsbedingungen angegeben werden.',
    fix: 'Fügen Sie entweder das Fälligkeitsdatum (BT-9, z.B. "2024-02-15") oder Zahlungsbedingungen (BT-20, z.B. "Zahlbar innerhalb 14 Tagen") hinzu.',
  },
  // === PEPPOL Rules ===
  'PEPPOL-EN16931-R120': {
    title: 'Positionsnettobetrag falsch berechnet',
    explanation: 'Der Nettobetrag einer Rechnungsposition stimmt nicht mit der Berechnung überein.',
    fix: 'Formel: Positionsnetto = Menge × (Einzelpreis / Preisbasis) + Zuschläge - Abzüge. Prüfen Sie Rundung auf 2 Nachkommastellen.',
  },
  'PEPPOL-EN16931-R121': {
    title: 'Rechnungssumme falsch berechnet',
    explanation: 'Die Gesamtsumme der Rechnung stimmt nicht mit der Berechnung überein.',
    fix: 'Formel: Brutto = Netto + MwSt. Prüfen Sie alle Zwischenberechnungen.',
  },
  'PEPPOL-EN16931-R110': {
    title: 'Rechnungsdatum fehlt',
    explanation: 'Jede Rechnung muss ein Rechnungsdatum haben.',
    fix: 'Fügen Sie das Rechnungsdatum (BT-2) im Format JJJJ-MM-TT hinzu.',
  },
  'PEPPOL-EN16931-R080': {
    title: 'Dokumentwährung fehlt',
    explanation: 'Die Rechnungswährung muss angegeben sein.',
    fix: 'Fügen Sie den Währungscode (BT-5) hinzu, z.B. "EUR".',
  },
  // === German specific rules (BR-DE-*) ===
  'BR-DE-1': {
    title: 'Fehlende XRechnung-Kennung',
    explanation: 'Das Dokument muss eine gueltige XRechnung-Versionskennung enthalten.',
    fix: 'Fügen Sie das Element <cbc:CustomizationID> mit dem Wert "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0" hinzu.',
    docLink: 'https://xeinkauf.de/xrechnung/',
  },
  'BR-DE-2': {
    title: 'Fehlende Leitweg-ID',
    explanation: 'Für Rechnungen an öffentliche Auftraggeber ist eine Leitweg-ID erforderlich.',
    fix: 'Tragen Sie die Leitweg-ID Ihres Auftraggebers im Element <cbc:BuyerReference> ein.',
    docLink: 'https://leitweg-id.de/',
  },
  'BR-DE-3': {
    title: 'Fehlende Kontaktdaten Verkaeufer',
    explanation: 'Der Verkaeufer muss mindestens eine E-Mail-Adresse oder Telefonnummer angeben.',
    fix: 'Fügen Sie im Bereich AccountingSupplierParty/Party/Contact eine E-Mail-Adresse oder Telefonnummer hinzu.',
  },
  'BR-DE-4': {
    title: 'Fehlende Kontaktdaten Kaeufer',
    explanation: 'Der Kaeufer muss mindestens eine E-Mail-Adresse oder Telefonnummer angeben.',
    fix: 'Fügen Sie im Bereich AccountingCustomerParty/Party/Contact eine E-Mail-Adresse oder Telefonnummer hinzu.',
  },
  'BR-DE-5': {
    title: 'Fehlende Zahlungsart',
    explanation: 'Es muss eine gueltige Zahlungsart angegeben werden.',
    fix: 'Fügen Sie ein PaymentMeans-Element mit einem gültigen PaymentMeansCode hinzu (z.B. 58 für SEPA-Überweisung).',
  },
  'BR-DE-6': {
    title: 'Fehlende IBAN',
    explanation: 'Bei Zahlung per Überweisung ist eine gueltige IBAN erforderlich.',
    fix: 'Tragen Sie die IBAN im Element PayeeFinancialAccount/ID ein.',
  },
  'BR-DE-7': {
    title: 'Fehlende BIC',
    explanation: 'Bei internationalen Zahlungen ist der BIC/SWIFT-Code erforderlich.',
    fix: 'Fügen Sie den BIC im Element FinancialInstitutionBranch/ID hinzu.',
  },
  'BR-DE-8': {
    title: 'Ungueltige Steuer-ID',
    explanation: 'Die Umsatzsteuer-Identifikationsnummer hat ein ungueltiges Format.',
    fix: 'Die USt-IdNr. muss mit dem Ländercode beginnen (z.B. DE123456789 für Deutschland).',
  },
  'BR-DE-9': {
    title: 'Fehlende Rechnungsnummer',
    explanation: 'Jede Rechnung muss eine eindeutige Rechnungsnummer haben.',
    fix: 'Tragen Sie Ihre Rechnungsnummer im Element <cbc:ID> ein.',
  },
  'BR-DE-10': {
    title: 'Fehlende Steuerberechnung',
    explanation: 'Die Steuerbeträge müssen korrekt berechnet sein.',
    fix: 'Pruefen Sie, ob TaxTotal und TaxSubtotal korrekt berechnet sind.',
  },
  'BR-DE-11': {
    title: 'Ungueltige Waehrung',
    explanation: 'Die Dokumentenwaehrung muss EUR sein.',
    fix: 'Setzen Sie DocumentCurrencyCode auf "EUR".',
  },
  'BR-DE-12': {
    title: 'Fehlende Steuerkategorie',
    explanation: 'Jede Rechnungsposition muss eine Steuerkategorie haben.',
    fix: 'Fügen Sie ClassifiedTaxCategory mit ID und Percent zu jeder InvoiceLine hinzu.',
  },
  'BR-DE-13': {
    title: 'Fehlende Positionsbezeichnung',
    explanation: 'Jede Rechnungsposition muss einen Namen haben.',
    fix: 'Tragen Sie die Artikelbezeichnung im Element Item/Name ein.',
  },
  'BR-DE-14': {
    title: 'Ungueltige Mengeneinheit',
    explanation: 'Die Mengeneinheit entspricht nicht dem UN/ECE Rec 20 Standard.',
    fix: 'Verwenden Sie einen gültigen unitCode (z.B. C62 für Stück, HUR für Stunden).',
  },
  'BR-DE-15': {
    title: 'Fehlende Adressdaten',
    explanation: 'Strasse, PLZ und Ort müssen angegeben werden.',
    fix: 'Vervollstaendigen Sie die Adresse mit StreetName, PostalZone und CityName.',
  },
  'BR-DE-16': {
    title: 'Fehlender Ländercode',
    explanation: 'Der Ländercode muss im ISO 3166-1 Alpha-2 Format angegeben werden.',
    fix: 'Fügen Sie Country/IdentificationCode hinzu (z.B. "DE" für Deutschland).',
  },
  'BR-DE-17': {
    title: 'Ungueltige Datumsformate',
    explanation: 'Datumsangaben müssen im Format JJJJ-MM-TT vorliegen.',
    fix: 'Verwenden Sie das ISO-Datumsformat (z.B. 2024-01-15).',
  },
  'BR-DE-18': {
    title: 'Fehlende Bankverbindung',
    explanation: 'Bei Überweisung muss eine Bankverbindung angegeben werden.',
    fix: 'Fügen Sie PayeeFinancialAccount mit IBAN und optional BIC hinzu.',
  },
  'CII-SR': {
    title: 'CII-Syntaxfehler',
    explanation: 'Die XML-Struktur entspricht nicht dem CII-Standard.',
    fix: 'Pruefen Sie die XML-Struktur auf fehlende oder falsch geschachtelte Elemente.',
  },
  'UBL-SR': {
    title: 'UBL-Syntaxfehler',
    explanation: 'Die XML-Struktur entspricht nicht dem UBL-Standard.',
    fix: 'Pruefen Sie die XML-Struktur auf fehlende oder falsch geschachtelte Elemente.',
  },
}

interface ValidationErrorItemProps {
  error: ValidationError
  expanded?: boolean
}

export function ValidationErrorItem({ error, expanded: initialExpanded = false }: ValidationErrorItemProps) {
  const [expanded, setExpanded] = useState(initialExpanded)

  const severityConfig = {
    error: {
      icon: XCircle,
      color: 'text-error-500',
      bg: 'bg-error-50',
      border: 'border-error-200',
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-warning-500',
      bg: 'bg-warning-50',
      border: 'border-warning-200',
    },
    info: {
      icon: Info,
      color: 'text-primary-500',
      bg: 'bg-primary-50',
      border: 'border-primary-200',
    },
  }

  const config = severityConfig[error.severity]
  const Icon = config.icon

  // Find explanation for this error code
  const errorInfo = error.code ? ERROR_EXPLANATIONS[error.code] : null
  const hasDetails = error.location || error.code || errorInfo?.docLink

  return (
    <div className={cn('rounded-lg border', config.bg, config.border)}>
      {/* Main error display */}
      <div className="p-3">
        <div className="flex items-start gap-2">
          <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', config.color)} />
          <div className="flex-1 min-w-0">
            {/* German title if available */}
            {errorInfo && (
              <p className="font-medium text-gray-900 text-sm">{errorInfo.title}</p>
            )}

            {/* Original message or explanation */}
            <p className={cn('text-sm', errorInfo ? 'text-gray-600 mt-0.5' : 'text-gray-900')}>
              {errorInfo?.explanation || error.message}
            </p>

            {/* Quick fix suggestion */}
            {(errorInfo?.fix || error.suggestion) && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-md">
                <div className="flex items-start gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-amber-800">So beheben Sie das:</p>
                    <p className="text-xs text-amber-700 mt-0.5">{errorInfo?.fix || error.suggestion}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Expandable technical details */}
            {hasDetails && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
              >
                <Code className="h-3 w-3" />
                Technische Details
                {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Expanded technical details */}
      {expanded && hasDetails && (
        <div className="px-3 pb-3 pt-0">
          <div className="ml-7 p-2 bg-gray-100 rounded-md text-xs space-y-1">
            {error.code && (
              <p className="font-mono text-gray-600">
                <span className="text-gray-400">Code:</span> {error.code}
              </p>
            )}
            {error.location && (
              <p className="font-mono text-gray-600 break-all">
                <span className="text-gray-400">Pfad:</span> {error.location}
              </p>
            )}
            {!errorInfo && error.message && (
              <p className="text-gray-600">
                <span className="text-gray-400">Meldung:</span> {error.message}
              </p>
            )}
            {errorInfo?.docLink && (
              <a
                href={errorInfo.docLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 mt-1"
              >
                Mehr erfahren
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
