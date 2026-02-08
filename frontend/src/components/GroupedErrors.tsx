import { useState, useMemo } from 'react'
import {
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Layers,
  Lightbulb,
} from 'lucide-react'
import { cn } from '@/lib/utils'

// Generic error type that both ValidationError and ConversionValidationError can satisfy
export interface GroupableError {
  code: string
  message?: string
  message_de?: string
  location?: string
  suggestion?: string
  severity?: string
}

// Group errors by error code
export interface GroupedError<T extends GroupableError> {
  code: string
  errors: T[]
  count: number
  locations: string[]
}

export function groupErrorsByCode<T extends GroupableError>(errors: T[]): GroupedError<T>[] {
  const groups = new Map<string, GroupedError<T>>()

  errors.forEach((error) => {
    const key = error.code || (error.message_de || error.message || '')
    if (!groups.has(key)) {
      groups.set(key, {
        code: error.code,
        errors: [],
        count: 0,
        locations: [],
      })
    }
    const group = groups.get(key)!
    group.errors.push(error)
    group.count++
    if (error.location) {
      // Extract line number from location if present
      const lineMatch = error.location.match(/line[:\s]*(\d+)/i) ||
                        error.location.match(/\[(\d+)\]/) ||
                        error.location.match(/InvoiceLine\[(\d+)\]/)
      if (lineMatch) {
        group.locations.push(`Zeile ${lineMatch[1]}`)
      } else if (error.location.includes('InvoiceLine')) {
        // Extract position number from XPath
        const posMatch = error.location.match(/InvoiceLine\[(\d+)\]/)
        if (posMatch) {
          group.locations.push(`Position ${posMatch[1]}`)
        }
      }
    }
  })

  return Array.from(groups.values())
}

// Error explanations for common XRechnung/ZUGFeRD error codes
// Normalize error code for lookup (strip brackets, whitespace, etc.)
function normalizeErrorCode(code: string | undefined): string {
  if (!code) return ''
  // Remove brackets and trim
  return code.replace(/^\[|\]$/g, '').trim()
}

// Get error explanation with normalized code lookup
function getErrorExplanation(code: string | undefined): { title: string; explanation: string; fix?: string } | null {
  if (!code) return null
  const normalizedCode = normalizeErrorCode(code)
  return ERROR_EXPLANATIONS[normalizedCode] || null
}

const ERROR_EXPLANATIONS: Record<string, { title: string; explanation: string; fix?: string }> = {
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
  'BR-DE-1': {
    title: 'Fehlende XRechnung-Kennung',
    explanation: 'Das Dokument muss eine gueltige XRechnung-Versionskennung enthalten.',
    fix: 'Fügen Sie das Element <cbc:CustomizationID> mit dem Wert "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0" hinzu.',
  },
  'BR-DE-2': {
    title: 'Fehlende Leitweg-ID',
    explanation: 'Für Rechnungen an öffentliche Auftraggeber ist eine Leitweg-ID erforderlich.',
    fix: 'Tragen Sie die Leitweg-ID Ihres Auftraggebers im Element <cbc:BuyerReference> ein.',
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
}

interface GroupedErrorsSectionProps<T extends GroupableError> {
  title: string
  errors: T[]
  type: 'error' | 'warning'
}

export function GroupedErrorsSection<T extends GroupableError>({
  title,
  errors,
  type,
}: GroupedErrorsSectionProps<T>) {
  const groupedErrors = useMemo(() => groupErrorsByCode(errors), [errors])
  const hasDuplicates = groupedErrors.some((g) => g.count > 1)

  const icon = type === 'error'
    ? <XCircle className="h-4 w-4 text-error-500" />
    : <AlertTriangle className="h-4 w-4 text-warning-500" />

  return (
    <div className="mb-4">
      <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
        {icon}
        {title} ({errors.length})
        {hasDuplicates && (
          <span className="text-xs font-normal text-gray-500 flex items-center gap-1">
            <Layers className="h-3 w-3" />
            {groupedErrors.length} Typen
          </span>
        )}
      </h4>
      <div className="space-y-2">
        {groupedErrors.map((group, index) => (
          <GroupedErrorItem key={`${group.code}-${index}`} group={group} type={type} />
        ))}
      </div>
    </div>
  )
}

interface GroupedErrorItemProps<T extends GroupableError> {
  group: GroupedError<T>
  type: 'error' | 'warning'
}

function GroupedErrorItem<T extends GroupableError>({ group, type }: GroupedErrorItemProps<T>) {
  const [expanded, setExpanded] = useState(false)
  const hasMultiple = group.count > 1

  // Get unique locations
  const uniqueLocations = [...new Set(group.locations)]

  // Get error explanation if available (with normalized code lookup)
  const errorInfo = getErrorExplanation(group.code)

  // Get message from first error (handles both message and message_de)
  const firstError = group.errors[0]
  const rawMessage = firstError.message_de || firstError.message || ''
  // Clean up the message - remove redundant code prefix like "[BR-CO-25]-"
  const message = rawMessage.replace(/^\[[\w-]+\]-?\s*/, '')
  const suggestion = firstError.suggestion

  const bgColor = type === 'error' ? 'bg-error-50' : 'bg-warning-50'
  const borderColor = type === 'error' ? 'border-error-200' : 'border-warning-200'
  const iconColor = type === 'error' ? 'text-error-500' : 'text-warning-500'
  const badgeBg = type === 'error' ? 'bg-error-100' : 'bg-warning-100'
  const badgeText = type === 'error' ? 'text-error-700' : 'text-warning-700'
  const Icon = type === 'error' ? XCircle : AlertTriangle

  if (!hasMultiple) {
    // Single error - show simple format
    return (
      <div className={cn('rounded-lg border p-3', bgColor, borderColor)}>
        <div className="flex items-start gap-2">
          <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', iconColor)} />
          <div className="flex-1 min-w-0">
            {/* Error code badge */}
            {group.code && (
              <span className={cn('font-mono text-xs px-1 rounded', badgeBg, badgeText)}>
                {normalizeErrorCode(group.code)}
              </span>
            )}

            {/* German title - prominent display */}
            {errorInfo ? (
              <>
                <p className="font-semibold text-gray-900 text-sm mt-1">{errorInfo.title}</p>
                <p className="text-sm text-gray-600 mt-0.5">{errorInfo.explanation}</p>
              </>
            ) : (
              /* Fallback to raw message if no German explanation available */
              <p className="text-sm text-gray-900 mt-1">{message}</p>
            )}

            {/* Technical details (location + original message) - shown smaller */}
            {(firstError.location || (errorInfo && message)) && (
              <div className="mt-2 p-2 bg-gray-100 rounded text-xs space-y-1">
                {firstError.location && (
                  <p className="font-mono text-gray-500 break-all">
                    <span className="text-gray-400">Pfad:</span> {firstError.location}
                  </p>
                )}
                {errorInfo && message && (
                  <p className="text-gray-500">
                    <span className="text-gray-400">Original:</span> {message}
                  </p>
                )}
              </div>
            )}

            {/* Fix suggestion */}
            {(errorInfo?.fix || suggestion) && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-md">
                <div className="flex items-start gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-700">{errorInfo?.fix || suggestion}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Multiple occurrences - show grouped
  return (
    <div className={cn('rounded-lg border overflow-hidden', bgColor, borderColor)}>
      {/* Header with count badge */}
      <div className="p-3">
        <div className="flex items-start gap-2">
          <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', iconColor)} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', badgeBg, badgeText)}>
                {group.count}× betroffen
              </span>
              {group.code && (
                <span className="text-xs font-mono text-gray-500">
                  {normalizeErrorCode(group.code)}
                </span>
              )}
            </div>

            {/* German title - prominent display */}
            {errorInfo ? (
              <>
                <p className="font-semibold text-gray-900 text-sm mt-1">{errorInfo.title}</p>
                <p className="text-sm text-gray-600 mt-0.5">{errorInfo.explanation}</p>
              </>
            ) : (
              <p className="text-sm text-gray-900 mt-1">{message}</p>
            )}

            {/* Affected positions */}
            {uniqueLocations.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                <span className="text-xs text-gray-500">Betroffen:</span>
                {uniqueLocations.slice(0, expanded ? undefined : 5).map((loc, i) => (
                  <span
                    key={i}
                    className="inline-flex px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                  >
                    {loc}
                  </span>
                ))}
                {!expanded && uniqueLocations.length > 5 && (
                  <span className="text-xs text-gray-400">
                    +{uniqueLocations.length - 5} weitere
                  </span>
                )}
              </div>
            )}

            {/* Suggestion */}
            {(errorInfo?.fix || suggestion) && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-md">
                <div className="flex items-start gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-700">{errorInfo?.fix || suggestion}</p>
                </div>
              </div>
            )}

            {/* Expand button for details */}
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-3 w-3" />
                  Weniger anzeigen
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" />
                  Alle {group.count} Vorkommen anzeigen
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded: show all individual errors */}
      {expanded && (
        <div className={cn('border-t p-3 pt-0 space-y-2', borderColor)}>
          <p className="text-xs text-gray-500 pt-3 pb-1">Einzelne Vorkommen:</p>
          {group.errors.map((error, i) => (
            <div
              key={i}
              className="text-xs p-2 bg-white rounded border border-gray-200"
            >
              {error.location && (
                <p className="font-mono text-gray-500 break-all">
                  {error.location}
                </p>
              )}
              <p className="text-gray-700 mt-1">{error.message_de || error.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
