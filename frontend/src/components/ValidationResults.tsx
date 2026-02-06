import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  RefreshCw,
  UserPlus,
  ChevronDown,
  ChevronUp,
  Layers,
} from 'lucide-react'
import { cn, formatDateTime } from '@/lib/utils'
import { useValidationStore, useDownloadReport } from '@/hooks/useValidation'
import { useAuthStore } from '@/hooks/useAuth'
import { ValidationErrorItem } from './ValidationErrorItem'
import type { ValidationError, ValidationStatus } from '@/types'

// Group errors by error code
interface GroupedError {
  code: string
  errors: ValidationError[]
  count: number
  locations: string[]
}

function groupErrorsByCode(errors: ValidationError[]): GroupedError[] {
  const groups = new Map<string, GroupedError>()

  errors.forEach((error) => {
    const key = error.code || error.message
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

interface ValidationResultsProps {
  className?: string
}

export function ValidationResults({ className }: ValidationResultsProps) {
  const { currentResult, clearResult } = useValidationStore()
  const { isAuthenticated } = useAuthStore()
  const downloadReport = useDownloadReport()

  if (!currentResult) return null

  const { status, file_name, file_type, zugferd_profile, errors, warnings, validated_at, can_download_report, id } =
    currentResult

  const statusConfig: Record<
    ValidationStatus,
    { icon: typeof CheckCircle; color: string; label: string; bg: string }
  > = {
    valid: {
      icon: CheckCircle,
      color: 'text-success-600',
      label: 'Gueltig',
      bg: 'bg-success-50',
    },
    invalid: {
      icon: XCircle,
      color: 'text-error-600',
      label: 'Ungueltig',
      bg: 'bg-error-50',
    },
    error: {
      icon: AlertTriangle,
      color: 'text-warning-600',
      label: 'Fehler',
      bg: 'bg-warning-50',
    },
  }

  const config = statusConfig[status]
  const StatusIcon = config.icon

  return (
    <div className={cn('card', className)}>
      {/* Header */}
      <div className={cn('px-6 py-4 border-b border-gray-200', config.bg)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusIcon className={cn('h-8 w-8', config.color)} />
            <div>
              <h3 className={cn('text-xl font-semibold', config.color)}>
                {config.label}
              </h3>
              <p className="text-sm text-gray-600">{file_name}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {can_download_report && (
              <button
                onClick={() => downloadReport.mutate(id)}
                disabled={downloadReport.isPending}
                className="btn-secondary btn-sm"
              >
                <Download className="h-4 w-4 mr-1" />
                PDF Bericht
              </button>
            )}
            <button
              onClick={clearResult}
              className="btn-ghost btn-sm"
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Neu
            </button>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="px-6 py-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Dateityp
            </p>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {file_type === 'xrechnung' ? 'XRechnung' : 'ZUGFeRD'}
            </p>
          </div>
          {zugferd_profile && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">
                Profil
              </p>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {zugferd_profile}
              </p>
            </div>
          )}
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Fehler
            </p>
            <p
              className={cn(
                'text-sm font-medium mt-1',
                errors.length > 0 ? 'text-error-600' : 'text-gray-900'
              )}
            >
              {errors.length}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Warnungen
            </p>
            <p
              className={cn(
                'text-sm font-medium mt-1',
                warnings.length > 0 ? 'text-warning-600' : 'text-gray-900'
              )}
            >
              {warnings.length}
            </p>
          </div>
        </div>

        {/* Errors - Grouped */}
        {errors.length > 0 && (
          <GroupedErrorsSection
            title="Fehler"
            errors={errors}
            icon={<XCircle className="h-4 w-4 text-error-500" />}
          />
        )}

        {/* Warnings - Grouped */}
        {warnings.length > 0 && (
          <GroupedErrorsSection
            title="Warnungen"
            errors={warnings}
            icon={<AlertTriangle className="h-4 w-4 text-warning-500" />}
          />
        )}

        {/* Success message */}
        {status === 'valid' && errors.length === 0 && warnings.length === 0 && (
          <div className="flex items-center gap-3 p-4 bg-success-50 rounded-lg">
            <CheckCircle className="h-6 w-6 text-success-600" />
            <div>
              <p className="font-medium text-success-700">
                Ihre E-Rechnung ist vollstaendig konform!
              </p>
              <p className="text-sm text-success-600">
                Keine Fehler oder Warnungen gefunden.
              </p>
            </div>
          </div>
        )}

        {/* Timestamp */}
        <p className="text-xs text-gray-400 mt-4">
          Validiert am {formatDateTime(validated_at)}
        </p>

        {/* Register prompt for guests */}
        {!isAuthenticated && (
          <div className="mt-6 p-4 bg-primary-50 rounded-lg border border-primary-200">
            <div className="flex items-start gap-3">
              <UserPlus className="h-6 w-6 text-primary-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">
                  Das war Ihre kostenlose Validierung
                </h4>
                <p className="text-sm text-gray-600 mt-1">
                  Registrieren Sie sich kostenlos für 5 Validierungen pro Monat, oder wählen Sie einen Plan für mehr.
                </p>
                <div className="flex flex-wrap gap-2 mt-3">
                  <Link
                    to="/registrieren"
                    className="btn-primary btn-sm"
                  >
                    Kostenlos registrieren
                  </Link>
                  <Link
                    to="/login"
                    className="btn-secondary btn-sm"
                  >
                    Anmelden
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Component for grouped error display
function GroupedErrorsSection({
  title,
  errors,
  icon,
}: {
  title: string
  errors: ValidationError[]
  icon: React.ReactNode
}) {
  const groupedErrors = useMemo(() => groupErrorsByCode(errors), [errors])
  const hasDuplicates = groupedErrors.some((g) => g.count > 1)

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
          <GroupedErrorItem key={`${group.code}-${index}`} group={group} />
        ))}
      </div>
    </div>
  )
}

// Component for a single grouped error
function GroupedErrorItem({ group }: { group: GroupedError }) {
  const [expanded, setExpanded] = useState(false)
  const hasMultiple = group.count > 1

  // Get unique locations
  const uniqueLocations = [...new Set(group.locations)]

  if (!hasMultiple) {
    // Single error - show normally
    return <ValidationErrorItem error={group.errors[0]} />
  }

  // Multiple occurrences - show grouped
  return (
    <div className="rounded-lg border border-error-200 bg-error-50 overflow-hidden">
      {/* Header with count badge */}
      <div className="p-3">
        <div className="flex items-start gap-2">
          <XCircle className="h-5 w-5 mt-0.5 flex-shrink-0 text-error-500" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-error-100 text-error-700">
                {group.count}× betroffen
              </span>
              {group.code && (
                <span className="text-xs font-mono text-gray-500">
                  {group.code}
                </span>
              )}
            </div>

            {/* Error message - show first one */}
            <p className="text-sm text-gray-900 mt-1">
              {group.errors[0].message}
            </p>

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
            {group.errors[0].suggestion && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-md">
                <p className="text-xs text-amber-700">
                  💡 {group.errors[0].suggestion}
                </p>
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
        <div className="border-t border-error-200 p-3 pt-0 space-y-2">
          <p className="text-xs text-gray-500 pt-3 pb-1">Einzelne Vorkommen:</p>
          {group.errors.map((error, i) => (
            <div
              key={i}
              className="text-xs p-2 bg-white rounded border border-gray-200"
            >
              {error.location && (
                <p className="font-mono text-gray-500 break-all">
                  📍 {error.location}
                </p>
              )}
              <p className="text-gray-700 mt-1">{error.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
