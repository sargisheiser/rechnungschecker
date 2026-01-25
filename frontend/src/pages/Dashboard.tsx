import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  FileCheck,
  CheckCircle,
  XCircle,
  TrendingUp,
  CreditCard,
  ArrowRight,
  Loader2,
  Key,
  Users,
  Building2,
  ChevronDown,
  FolderUp,
  FileOutput,
  Layers,
  ClipboardList,
  BarChart3,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { FileUpload } from '@/components/FileUpload'
import { ValidationResults } from '@/components/ValidationResults'
import { useValidationStore, useValidationHistory } from '@/hooks/useValidation'
import { useUser } from '@/hooks/useAuth'
import { useUsage, useSubscription, usePortalSession } from '@/hooks/useBilling'
import { useClients, useClientContext } from '@/hooks/useClients'
import { cn, formatDate, formatDateTime } from '@/lib/utils'

export function Dashboard() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const { currentResult } = useValidationStore()
  const { data: user } = useUser()
  const { data: usage, isLoading: usageLoading } = useUsage()
  const { data: subscription } = useSubscription()
  const { selectedClientId, setSelectedClientId } = useClientContext()
  const { data: clients } = useClients(1, 100, true) // Get active clients for dropdown
  const { data: history, isLoading: historyLoading } = useValidationHistory(1, 5)
  const portalSession = usePortalSession()
  const [showClientDropdown, setShowClientDropdown] = useState(false)

  // Check for checkout success
  const checkoutStatus = searchParams.get('checkout')

  // Check if user can manage clients (Steuerberater plan)
  const canManageClients = user?.plan === 'steuerberater'
  const selectedClient = clients?.items.find((c) => c.id === selectedClientId)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Checkout success message */}
      {checkoutStatus === 'success' && (
        <div className="mb-6 p-4 bg-success-50 border border-success-200 rounded-lg flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-success-600" />
          <div>
            <p className="font-medium text-success-700">
              {t('dashboard.paymentSuccess')}
            </p>
            <p className="text-sm text-success-600">
              {t('dashboard.subscriptionActivated')}
            </p>
          </div>
        </div>
      )}

      {/* Header Card */}
      <div className="card p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-primary-100 flex items-center justify-center">
              <FileCheck className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {t('dashboard.welcomeBack')}, {user?.company_name || user?.email?.split('@')[0]}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                <span className={cn(
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  user?.plan === 'steuerberater' ? 'bg-purple-100 text-purple-700' :
                  user?.plan === 'pro' ? 'bg-primary-100 text-primary-700' :
                  'bg-gray-100 text-gray-700'
                )}>
                  {user?.plan === 'steuerberater' ? 'Steuerberater' : user?.plan === 'pro' ? 'Pro' : 'Free'}
                </span>
                {usage && !usageLoading && (
                  <span className="text-sm text-gray-500">
                    {usage.validations_used} {t('dashboard.validations').toLowerCase()} diesen Monat
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Client Selector (Steuerberater only) */}
          {canManageClients && clients && clients.items.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setShowClientDropdown(!showClientDropdown)}
                className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <Building2 className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">
                  {selectedClient?.name || 'Alle Mandanten'}
                </span>
                <ChevronDown className={cn('h-4 w-4 text-gray-400 transition-transform', showClientDropdown && 'rotate-180')} />
              </button>

              {showClientDropdown && (
                <>
                  <div
                    className="fixed inset-0"
                    onClick={() => setShowClientDropdown(false)}
                  />
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10 max-h-80 overflow-y-auto">
                    <button
                      onClick={() => {
                        setSelectedClientId(null)
                        setShowClientDropdown(false)
                      }}
                      className={cn(
                        'w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2',
                        !selectedClientId && 'bg-primary-50 text-primary-700'
                      )}
                    >
                      <Users className="h-4 w-4" />
                      Alle Mandanten
                    </button>
                    <hr className="my-1" />
                    {clients.items.map((client) => (
                      <button
                        key={client.id}
                        onClick={() => {
                          setSelectedClientId(client.id)
                          setShowClientDropdown(false)
                        }}
                        className={cn(
                          'w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2',
                          selectedClientId === client.id && 'bg-primary-50 text-primary-700'
                        )}
                      >
                        <Building2 className="h-4 w-4" />
                        <span className="truncate">{client.name}</span>
                        {client.client_number && (
                          <span className="text-xs text-gray-400">#{client.client_number}</span>
                        )}
                      </button>
                    ))}
                    <hr className="my-1" />
                    <Link
                      to="/mandanten"
                      onClick={() => setShowClientDropdown(false)}
                      className="w-full px-4 py-2 text-left text-sm text-primary-600 hover:bg-primary-50 flex items-center gap-2"
                    >
                      Mandanten verwalten
                    </Link>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Actions */}
          <QuickActions plan={user?.plan || 'free'} />

          {/* Upload section */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {t('dashboard.newValidation')}
            </h2>
            {currentResult ? <ValidationResults /> : <FileUpload />}
          </div>

          {/* Recent validations */}
          <div className="card">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                {t('dashboard.recentValidations')}
              </h2>
              <Link
                to="/dashboard/verlauf"
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                {t('common.viewAll')}
              </Link>
            </div>

            {historyLoading ? (
              <div className="p-6 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : history?.items.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <FileCheck className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>{t('dashboard.noValidations')}</p>
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
              {t('dashboard.usageThisMonth')}
            </h3>

            {usageLoading ? (
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            ) : (
              <div className="space-y-4">
                <UsageStat
                  label={t('dashboard.validations')}
                  used={usage?.validations_used || 0}
                  limit={usage?.validations_limit}
                  icon={FileCheck}
                />
                <UsageStat
                  label={t('dashboard.conversions')}
                  used={usage?.conversions_used || 0}
                  limit={usage?.conversions_limit || 0}
                  icon={TrendingUp}
                />
              </div>
            )}

            {usage && usage.validations_limit && usage.validations_used >= usage.validations_limit && (
              <div className="mt-4 p-3 bg-warning-50 rounded-lg">
                <p className="text-sm text-warning-700">
                  {t('dashboard.limitReached')}{' '}
                  <Link to="/preise" className="font-medium underline">
                    {t('dashboard.upgradeNow')}
                  </Link>
                </p>
              </div>
            )}
          </div>

          {/* Current plan */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
              {t('dashboard.currentPlan')}
            </h3>

            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {user?.plan || 'Free'}
                </p>
                {subscription && (
                  <p className="text-sm text-gray-500">
                    {t('dashboard.renewsOn')} {formatDate(subscription.current_period_end)}
                  </p>
                )}
              </div>
              <CreditCard className="h-8 w-8 text-gray-400" />
            </div>

            {user?.plan === 'free' ? (
              <Link to="/preise" className="btn-primary w-full">
                {t('common.upgrade')}
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
                  t('dashboard.manageSubscription')
                )}
              </button>
            )}
          </div>

          {/* Mandantenverwaltung (Steuerberater only) */}
          {user?.plan === 'steuerberater' && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
                {t('clients.title')}
              </h3>
              <div className="flex items-center gap-3 mb-4">
                <Users className="h-8 w-8 text-primary-500" />
                <div>
                  <p className="font-medium text-gray-900">{t('clients.clients')}</p>
                  <p className="text-sm text-gray-500">
                    {clients?.total || 0} {t('clients.clients')}
                  </p>
                </div>
              </div>
              <Link to="/mandanten" className="btn-secondary w-full">
                {t('clients.manageClients')}
              </Link>
            </div>
          )}

          {/* API Keys (Pro and Steuerberater only) */}
          {(user?.plan === 'pro' || user?.plan === 'steuerberater') && (
            <div className="card p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
                {t('apiKeys.title')}
              </h3>
              <div className="flex items-center gap-3 mb-4">
                <Key className="h-8 w-8 text-primary-500" />
                <div>
                  <p className="font-medium text-gray-900">{t('apiKeys.apiKeys')}</p>
                  <p className="text-sm text-gray-500">
                    {t('apiKeys.programmaticAccess')}
                  </p>
                </div>
              </div>
              <Link to="/api-keys" className="btn-secondary w-full">
                {t('apiKeys.manageKeys')}
              </Link>
            </div>
          )}

          {/* Quick tips */}
          <div className="card p-6 bg-primary-50 border-primary-100">
            <h3 className="text-sm font-medium text-primary-900 mb-2">
              {t('dashboard.tip')}
            </h3>
            <p className="text-sm text-primary-700">
              {user?.plan === 'pro' || user?.plan === 'steuerberater'
                ? t('dashboard.tipPro')
                : t('dashboard.tipFree')}
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

function QuickActions({ plan }: { plan: string }) {
  const { t } = useTranslation()
  const isPro = plan === 'pro' || plan === 'steuerberater'

  const actions = [
    { label: t('dashboard.quickActions.batchValidation'), icon: FolderUp, to: '/batch', show: true },
    { label: t('dashboard.quickActions.convertPdf'), icon: FileOutput, to: '/konvertierung', show: true },
    { label: t('dashboard.quickActions.batchConversion'), icon: Layers, to: '/batch-konvertierung', show: isPro },
    { label: t('dashboard.quickActions.templates'), icon: ClipboardList, to: '/vorlagen', show: isPro },
    { label: t('dashboard.quickActions.analytics'), icon: BarChart3, to: '/analytik', show: isPro },
  ].filter((action) => action.show)

  return (
    <div className="card p-4">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
        {t('dashboard.quickActions.title')}
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        {actions.map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className="flex flex-col items-center gap-2 p-3 rounded-lg border border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50 transition-all hover:shadow-sm group"
          >
            <action.icon className="h-6 w-6 text-gray-400 group-hover:text-primary-500 transition-colors" />
            <span className="text-xs font-medium text-gray-600 group-hover:text-primary-700 text-center">
              {action.label}
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
