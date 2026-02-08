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
  ClipboardList,
  BarChart3,
  Download,
  Eye,
  AlertTriangle,
  HelpCircle,
  FileText,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { FileUpload } from '@/components/FileUpload'
import { ValidationResults } from '@/components/ValidationResults'
import { OnboardingTour } from '@/components/OnboardingTour'
import { Skeleton, OnboardingChecklist } from '@/components'
import { useValidationStore, useValidationHistory, useDownloadReport } from '@/hooks/useValidation'
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
  const { data: clients } = useClients(1, 100, true)
  const { data: history, isLoading: historyLoading } = useValidationHistory(1, 5)
  const portalSession = usePortalSession()
  const [showClientDropdown, setShowClientDropdown] = useState(false)

  const checkoutStatus = searchParams.get('checkout')
  const canManageClients = user?.plan === 'steuerberater'
  const selectedClient = clients?.items.find((c) => c.id === selectedClientId)
  const isPro = user?.plan === 'pro' || user?.plan === 'steuerberater'

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Onboarding tour for new users */}
      {user && <OnboardingTour userCreatedAt={user.created_at} />}

      {/* Onboarding checklist for new users */}
      {user && (
        <OnboardingChecklist
          className="mb-6"
          hasValidations={(history?.total ?? 0) > 0}
          hasCompletedProfile={!!(user.full_name || user.company_name)}
          hasTemplates={false}
        />
      )}

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

      {/* Compact Header with Client Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-gray-900">
            {t('dashboard.welcomeBack')}{user?.company_name || user?.full_name ? `, ${user?.company_name || user?.full_name}` : ''}
          </h1>
          <span className={cn(
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
            user?.plan === 'steuerberater' ? 'bg-purple-100 text-purple-700' :
            user?.plan === 'pro' ? 'bg-primary-100 text-primary-700' :
            'bg-gray-100 text-gray-700'
          )}>
            {user?.plan === 'steuerberater' ? 'Steuerberater' : user?.plan === 'pro' ? 'Pro' : 'Free'}
          </span>
        </div>

        {/* Client Selector (Steuerberater only) */}
        {canManageClients && clients && clients.items.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowClientDropdown(!showClientDropdown)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Building2 className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">
                {selectedClient?.name || 'Alle Mandanten'}
              </span>
              <ChevronDown className={cn('h-4 w-4 text-gray-400 transition-transform', showClientDropdown && 'rotate-180')} />
            </button>

            {showClientDropdown && (
              <>
                <div className="fixed inset-0" onClick={() => setShowClientDropdown(false)} />
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10 max-h-80 overflow-y-auto">
                  <button
                    onClick={() => { setSelectedClientId(null); setShowClientDropdown(false) }}
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
                      onClick={() => { setSelectedClientId(client.id); setShowClientDropdown(false) }}
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

      {/* Usage Bar - Prominent Position */}
      <UsageBar usage={usage} isLoading={usageLoading} />

      {/* Quick Actions Row - Always Visible */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <ActionCard
          to="/konvertierung"
          icon={FileOutput}
          label={t('dashboard.quickActions.convertPdf')}
          description={t('dashboard.convertDescription')}
        />
        <ActionCard
          to="/batch"
          icon={FolderUp}
          label={t('dashboard.quickActions.batchValidation')}
          description={t('dashboard.batchDescription')}
          badge={!isPro ? 'Pro' : undefined}
        />
        <ActionCard
          to="/vorlagen"
          icon={ClipboardList}
          label={t('dashboard.quickActions.templates')}
          description={t('dashboard.templatesDescription')}
        />
        <ActionCard
          to="/analytik"
          icon={BarChart3}
          label={t('dashboard.quickActions.analytics')}
          description={t('dashboard.analyticsDescription')}
        />
      </div>

      {/* HERO: File Upload Section - Primary Action */}
      <div className="card p-8 mb-6 bg-gradient-to-br from-primary-50 to-white border-primary-100">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {t('dashboard.heroTitle')}
          </h2>
          <p className="text-gray-600">
            {t('dashboard.heroSubtitle')}
          </p>
        </div>

        {currentResult ? <ValidationResults /> : <FileUpload />}

        {/* Help Links */}
        {!currentResult && (
          <div className="flex items-center justify-center gap-6 mt-6 text-sm">
            <Tooltip content={t('dashboard.xrechnungTooltip')}>
              <button className="flex items-center gap-1 text-gray-500 hover:text-primary-600 transition-colors">
                <HelpCircle className="h-4 w-4" />
                {t('dashboard.whatsXRechnung')}
              </button>
            </Tooltip>
            <Tooltip content={t('dashboard.zugferdTooltip')}>
              <button className="flex items-center gap-1 text-gray-500 hover:text-primary-600 transition-colors">
                <HelpCircle className="h-4 w-4" />
                {t('dashboard.whatsZugferd')}
              </button>
            </Tooltip>
          </div>
        )}
      </div>

      {/* Recent Validations with Actions */}
      <div className="card mb-6">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {t('dashboard.recentValidations')}
          </h2>
          <Link
            to="/dashboard/verlauf"
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
          >
            {t('common.viewAll')}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {historyLoading ? (
          <div className="divide-y divide-gray-100">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="px-6 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <Skeleton className="h-5 w-5 rounded-full flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <Skeleton className="h-4 w-48 mb-2" />
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-5 w-16 rounded" />
                        <Skeleton className="h-3 w-20" />
                        <Skeleton className="h-3 w-24" />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Skeleton className="h-7 w-16 rounded" />
                    <Skeleton className="h-7 w-7 rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : history?.items.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="divide-y divide-gray-100">
            {history?.items.map((item) => (
              <ValidationHistoryItem key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>

      {/* Bottom Row: Plan & Quick Links */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Current Plan Card */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm text-gray-500">{t('dashboard.currentPlan')}</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">
                {user?.plan || 'Free'}
              </p>
            </div>
            <CreditCard className="h-8 w-8 text-gray-300" />
          </div>
          {subscription && (
            <p className="text-xs text-gray-500 mb-3">
              {t('dashboard.renewsOn')} {formatDate(subscription.current_period_end)}
            </p>
          )}
          {user?.plan === 'free' ? (
            <Link to="/preise" className="btn-primary w-full text-sm py-2">
              {t('common.upgrade')}
            </Link>
          ) : (
            <button
              onClick={() => portalSession.mutate()}
              disabled={portalSession.isPending}
              className="btn-secondary w-full text-sm py-2"
            >
              {portalSession.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                t('dashboard.manageSubscription')
              )}
            </button>
          )}
        </div>

        {/* Mandanten (Steuerberater) */}
        {user?.plan === 'steuerberater' && (
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm text-gray-500">{t('clients.title')}</p>
                <p className="text-lg font-semibold text-gray-900">
                  {clients?.total || 0} {t('clients.clients')}
                </p>
              </div>
              <Users className="h-8 w-8 text-gray-300" />
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Mandanten und Rechnungen verwalten
            </p>
            <Link to="/mandanten" className="btn-secondary w-full text-sm py-2">
              {t('clients.manageClients')}
            </Link>
          </div>
        )}

        {/* API Keys (Pro+) */}
        {isPro && (
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm text-gray-500">{t('apiKeys.title')}</p>
                <p className="text-lg font-semibold text-gray-900">API</p>
              </div>
              <Key className="h-8 w-8 text-gray-300" />
            </div>
            <p className="text-xs text-gray-500 mb-3">
              {t('apiKeys.programmaticAccess')}
            </p>
            <Link to="/api-keys" className="btn-secondary w-full text-sm py-2">
              {t('apiKeys.manageKeys')}
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

// Compact Usage Bar Component
function UsageBar({
  usage,
  isLoading,
}: {
  usage: { validations_used: number; validations_limit: number | null; conversions_used: number; conversions_limit: number | null } | undefined
  isLoading: boolean
}) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
          <div className="hidden sm:block w-px h-8 bg-gray-300" />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
        </div>
      </div>
    )
  }

  if (!usage) return null

  const validationsPercent = usage.validations_limit
    ? Math.min((usage.validations_used / usage.validations_limit) * 100, 100)
    : 0
  const conversionsPercent = usage.conversions_limit
    ? Math.min((usage.conversions_used / usage.conversions_limit) * 100, 100)
    : 0

  const showWarning = usage.validations_limit && usage.validations_used >= usage.validations_limit

  return (
    <div className={cn(
      'mb-6 p-4 rounded-lg',
      showWarning ? 'bg-warning-50 border border-warning-200' : 'bg-gray-50'
    )}>
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        {/* Validations */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <FileCheck className="h-4 w-4" />
              {t('dashboard.validations')}
            </span>
            <span className="text-sm font-medium">
              {usage.validations_used}
              {usage.validations_limit ? ` / ${usage.validations_limit}` : ` (${t('common.unlimited')})`}
            </span>
          </div>
          {usage.validations_limit && (
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  validationsPercent >= 90 ? 'bg-error-500' : validationsPercent >= 70 ? 'bg-warning-500' : 'bg-primary-500'
                )}
                style={{ width: `${validationsPercent}%` }}
              />
            </div>
          )}
        </div>

        <div className="hidden sm:block w-px h-8 bg-gray-300" />

        {/* Conversions */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              {t('dashboard.conversions')}
            </span>
            <span className="text-sm font-medium">
              {usage.conversions_used}
              {usage.conversions_limit ? ` / ${usage.conversions_limit}` : ` (${t('common.unlimited')})`}
            </span>
          </div>
          {usage.conversions_limit && (
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  conversionsPercent >= 90 ? 'bg-error-500' : conversionsPercent >= 70 ? 'bg-warning-500' : 'bg-primary-500'
                )}
                style={{ width: `${conversionsPercent}%` }}
              />
            </div>
          )}
        </div>

        {/* Upgrade Link */}
        {showWarning && (
          <Link
            to="/preise"
            className="text-sm font-medium text-warning-700 hover:text-warning-800 whitespace-nowrap"
          >
            {t('dashboard.upgradeNow')} →
          </Link>
        )}
      </div>
    </div>
  )
}

// Empty State Component
function EmptyState() {
  const { t } = useTranslation()

  return (
    <div className="p-8 text-center">
      <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {t('dashboard.emptyTitle')}
      </h3>
      <p className="text-gray-500 mb-4 max-w-sm mx-auto">
        {t('dashboard.emptyDescription')}
      </p>
    </div>
  )
}

// Improved Validation History Item with Actions
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
  const { t } = useTranslation()
  const downloadReport = useDownloadReport()
  const isValid = item.is_valid
  const StatusIcon = isValid ? CheckCircle : XCircle

  return (
    <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <StatusIcon className={cn(
            'h-5 w-5 flex-shrink-0 mt-0.5',
            isValid ? 'text-success-500' : 'text-error-500'
          )} />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {item.file_name || 'Unbekannte Datei'}
            </p>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
              <span className={cn(
                'px-1.5 py-0.5 rounded font-medium',
                isValid ? 'bg-success-100 text-success-700' : 'bg-error-100 text-error-700'
              )}>
                {isValid ? t('dashboard.statusValid') : t('dashboard.statusInvalid')}
              </span>
              <span>{item.file_type.toUpperCase()}</span>
              <span>{formatDateTime(item.validated_at)}</span>
              {item.error_count > 0 && (
                <span className="text-error-600">{item.error_count} {t('dashboard.errors')}</span>
              )}
              {item.warning_count > 0 && (
                <span className="text-warning-600">{item.warning_count} {t('dashboard.warnings')}</span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {!isValid && (
            <Link
              to={`/validierung/${item.id}`}
              className="btn-primary text-xs px-3 py-1.5"
            >
              <AlertTriangle className="h-3 w-3 mr-1" />
              {t('dashboard.fixIssues')}
            </Link>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation()
              downloadReport.mutate(item.id)
            }}
            disabled={downloadReport.isPending}
            className="btn-secondary text-xs px-3 py-1.5"
            title={t('dashboard.downloadReport')}
          >
            {downloadReport.isPending ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Download className="h-3 w-3" />
            )}
          </button>
          <Link
            to={`/validierung/${item.id}`}
            className="btn-secondary text-xs px-3 py-1.5"
            title={t('dashboard.viewDetails')}
          >
            <Eye className="h-3 w-3" />
          </Link>
        </div>
      </div>
    </div>
  )
}

// Action Card Component
function ActionCard({
  to,
  icon: Icon,
  label,
  description,
  badge,
}: {
  to: string
  icon: typeof FileOutput
  label: string
  description: string
  badge?: string
}) {
  return (
    <Link
      to={to}
      className="flex flex-col p-4 rounded-lg border border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50 transition-all hover:shadow-sm group"
    >
      <div className="flex items-center justify-between mb-2">
        <Icon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors" />
        {badge && (
          <span className="text-xs px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded">
            {badge}
          </span>
        )}
      </div>
      <span className="text-sm font-medium text-gray-900 group-hover:text-primary-700">
        {label}
      </span>
      <span className="text-xs text-gray-500 mt-1">
        {description}
      </span>
    </Link>
  )
}

// Simple Tooltip Component
function Tooltip({ content, children }: { content: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false)

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        {children}
      </div>
      {show && (
        <div className="absolute z-10 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg max-w-xs text-center whitespace-normal">
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  )
}
