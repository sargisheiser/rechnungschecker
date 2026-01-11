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
} from 'lucide-react'
import { FileUpload } from '@/components/FileUpload'
import { ValidationResults } from '@/components/ValidationResults'
import { useValidationStore, useValidationHistory } from '@/hooks/useValidation'
import { useUser } from '@/hooks/useAuth'
import { useUsage, useSubscription, usePortalSession } from '@/hooks/useBilling'
import { cn, formatDate, formatDateTime } from '@/lib/utils'
import type { ValidationStatus } from '@/types'

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

          {/* Quick tips */}
          <div className="card p-6 bg-primary-50 border-primary-100">
            <h3 className="text-sm font-medium text-primary-900 mb-2">
              Tipp
            </h3>
            <p className="text-sm text-primary-700">
              Mit dem Pro-Plan erhalten Sie API-Zugang und koennen Validierungen
              direkt in Ihre Systeme integrieren.
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
    file_name: string
    status: ValidationStatus
    file_type: string
    validated_at: string
  }
}) {
  const statusConfig: Record<
    ValidationStatus,
    { icon: typeof CheckCircle; color: string; label: string }
  > = {
    valid: { icon: CheckCircle, color: 'text-success-500', label: 'Gueltig' },
    invalid: { icon: XCircle, color: 'text-error-500', label: 'Ungueltig' },
    error: { icon: Clock, color: 'text-warning-500', label: 'Fehler' },
  }

  const config = statusConfig[item.status]
  const StatusIcon = config.icon

  return (
    <div className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
      <div className="flex items-center gap-3 min-w-0">
        <StatusIcon className={cn('h-5 w-5 flex-shrink-0', config.color)} />
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {item.file_name}
          </p>
          <p className="text-xs text-gray-500">
            {item.file_type.toUpperCase()} • {formatDateTime(item.validated_at)}
          </p>
        </div>
      </div>
      <span
        className={cn(
          'text-xs font-medium px-2 py-1 rounded',
          item.status === 'valid' && 'bg-success-50 text-success-700',
          item.status === 'invalid' && 'bg-error-50 text-error-700',
          item.status === 'error' && 'bg-warning-50 text-warning-700'
        )}
      >
        {config.label}
      </span>
    </div>
  )
}
