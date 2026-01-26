import { Link } from 'react-router-dom'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  RefreshCw,
  UserPlus,
} from 'lucide-react'
import { cn, formatDateTime } from '@/lib/utils'
import { useValidationStore, useDownloadReport } from '@/hooks/useValidation'
import { useAuthStore } from '@/hooks/useAuth'
import { ValidationErrorItem } from './ValidationErrorItem'
import type { ValidationStatus } from '@/types'

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

        {/* Errors */}
        {errors.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <XCircle className="h-4 w-4 text-error-500" />
              Fehler ({errors.length})
            </h4>
            <div className="space-y-2">
              {errors.map((error, index) => (
                <ValidationErrorItem key={index} error={error} />
              ))}
            </div>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-warning-500" />
              Warnungen ({warnings.length})
            </h4>
            <div className="space-y-2">
              {warnings.map((warning, index) => (
                <ValidationErrorItem key={index} error={warning} />
              ))}
            </div>
          </div>
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
