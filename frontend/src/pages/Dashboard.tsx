import { useSearchParams, Link } from 'react-router-dom'
import {
  FileCheck,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  CreditCard,
  ArrowRight,
  Loader2,
  Key,
} from 'lucide-react'
import { FileUpload } from '@/components/FileUpload'
import { ValidationResults } from '@/components/ValidationResults'
import { useValidationStore, useValidationHistory } from '@/hooks/useValidation'
import { useUser } from '@/hooks/useAuth'
import { useUsage, useSubscription, usePortalSession } from '@/hooks/useBilling'
import { cn, formatDate, formatDateTime } from '@/lib/utils'

export function Dashboard() {
  const [searchParams] = useSearchParams()
  const { currentResult } = useValidationStore()
  const { data: user } = useUser()
  const { data: usage, isLoading: usageLoading } = useUsage()
  const { data: subscription } = useSubscription()
  const { data: history, isLoading: historyLoading } = useValidationHistory(1, 5)
  const portalSession = usePortalSession()

  // Check for checkout success
  const checkoutStatus = searchParams.get('checkout')

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Checkout success message */}
      {checkoutStatus === 'success' && (
        <div className="mb-6 p-4 bg-success-50 border border-success-200 rounded-lg flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-success-600" />
          <div>
            <p className="font-medium text-success-700">
              Zahlung erfolgreich!
            </p>
            <p className="text-sm text-success-600">
              Ihr Abonnement wurde aktiviert.
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Willkommen zurueck, {user?.company_name || user?.email}
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Upload section */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Neue Validierung
            </h2>
            {currentResult ? <ValidationResults /> : <FileUpload />}
          </div>

          {/* Recent validations */}
          <div className="card">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Letzte Validierungen
              </h2>
              <Link
                to="/dashboard/verlauf"
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Alle anzeigen
              </Link>
            </div>

            {historyLoading ? (
              <div className="p-6 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : history?.items.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <FileCheck className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>Noch keine Validierungen durchgefuehrt</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {history?.items.map((item) => (
                  <ValidationHistoryItem key={item.id} item={item} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Usage stats */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
              Nutzung diesen Monat
            </h3>

            {usageLoading ? (
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            ) : (
              <div className="space-y-4">
                <UsageStat
                  label="Validierungen"
                  used={usage?.validations_used || 0}
                  limit={usage?.validations_limit}
                  icon={FileCheck}
                />
                <UsageStat
                  label="Konvertierungen"
                  used={usage?.conversions_used || 0}
                  limit={usage?.conversions_limit || 0}
                  icon={TrendingUp}
                />
              </div>
            )}

            {usage && usage.validations_limit && usage.validations_used >= usage.validations_limit && (
              <div className="mt-4 p-3 bg-warning-50 rounded-lg">
                <p className="text-sm text-warning-700">
                  Limit erreicht.{' '}
                  <Link to="/preise" className="font-medium underline">
                    Jetzt upgraden
                  </Link>
                </p>
              </div>
            )}
          </div>

          {/* Current plan */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
              Aktueller Plan
            </h3>

            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {user?.plan || 'Free'}
                </p>
                {subscription && (
                  <p className="text-sm text-gray-500">
                    Erneuert am {formatDate(subscription.current_period_end)}
                  </p>
                )}
              </div>
              <CreditCard className="h-8 w-8 text-gray-400" />
            </div>

            {user?.plan === 'free' ? (
              <Link to="/preise" className="btn-primary w-full">
                Upgraden
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            ) : (
              <button
                onClick={() => portalSession.mutate()}
                disabled={portalSession.isPending}
                className="btn-secondary w-full"
              >
                {portalSession.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Abo verwalten'
                )}
              </button>
            )}
          </div>

          {/* API Keys (Pro and Steuerberater only) */}
          {(user?.plan === 'pro' || user?.plan === 'steuerberater') && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
                API-Zugang
              </h3>
              <div className="flex items-center gap-3 mb-4">
                <Key className="h-8 w-8 text-primary-500" />
                <div>
                  <p className="font-medium text-gray-900">API-Schluessel</p>
                  <p className="text-sm text-gray-500">
                    Programmatischer Zugriff
                  </p>
                </div>
              </div>
              <Link to="/api-keys" className="btn-secondary w-full">
                Schluessel verwalten
              </Link>
            </div>
          )}

          {/* Quick tips */}
          <div className="card p-6 bg-primary-50 border-primary-100">
            <h3 className="text-sm font-medium text-primary-900 mb-2">
              Tipp
            </h3>
            <p className="text-sm text-primary-700">
              {user?.plan === 'pro' || user?.plan === 'steuerberater'
                ? 'Nutzen Sie die API, um Validierungen direkt in Ihre Systeme zu integrieren.'
                : 'Mit dem Pro-Plan erhalten Sie API-Zugang und koennen Validierungen direkt in Ihre Systeme integrieren.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function UsageStat({
  label,
  used,
  limit,
  icon: Icon,
}: {
  label: string
  used: number
  limit: number | null | undefined
  icon: typeof FileCheck
}) {
  const percentage = limit ? Math.min((used / limit) * 100, 100) : 0
  const isUnlimited = limit === null || limit === undefined

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-600">{label}</span>
        </div>
        <span className="text-sm font-medium text-gray-900">
          {used}
          {!isUnlimited && ` / ${limit}`}
          {isUnlimited && ' (unbegrenzt)'}
        </span>
      </div>
      {!isUnlimited && (
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              percentage >= 90 ? 'bg-error-500' : percentage >= 70 ? 'bg-warning-500' : 'bg-primary-500'
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  )
}

function ValidationHistoryItem({
  item,
}: {
  item: {
    id: string
    file_name?: string
    file_type: string
    is_valid: boolean
    error_count: number
    warning_count: number
    validated_at: string
  }
}) {
  const isValid = item.is_valid
  const StatusIcon = isValid ? CheckCircle : XCircle
  const statusColor = isValid ? 'text-success-500' : 'text-error-500'
  const statusLabel = isValid ? 'Gueltig' : 'Ungueltig'
  const statusBg = isValid ? 'bg-success-50 text-success-700' : 'bg-error-50 text-error-700'

  return (
    <Link
      to={`/validierung/${item.id}`}
      className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex items-center gap-3 min-w-0">
        <StatusIcon className={cn('h-5 w-5 flex-shrink-0', statusColor)} />
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {item.file_name || 'Unbekannte Datei'}
          </p>
          <p className="text-xs text-gray-500">
            {item.file_type.toUpperCase()} • {formatDateTime(item.validated_at)}
            {item.error_count > 0 && ` • ${item.error_count} Fehler`}
            {item.warning_count > 0 && ` • ${item.warning_count} Warnungen`}
          </p>
        </div>
      </div>
      <span className={cn('text-xs font-medium px-2 py-1 rounded', statusBg)}>
        {statusLabel}
      </span>
    </Link>
  )
}
