import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Plug,
  ArrowLeft,
  Loader2,
  Shield,
  Check,
  X,
  Settings,
  Trash2,
  TestTube,
  MessageSquare,
  FileSpreadsheet,
  Bell,
  AlertTriangle,
} from 'lucide-react'
import { useUser } from '@/hooks/useAuth'
import {
  useIntegrations,
  useCreateIntegration,
  useUpdateIntegration,
  useDeleteIntegration,
  useTestIntegration,
} from '@/hooks/useIntegrations'
import { cn, formatDateTime } from '@/lib/utils'
import type { Integration, IntegrationType } from '@/types'

const INTEGRATION_INFO: Record<IntegrationType, {
  name: string
  description: string
  icon: typeof Plug
  configField: string
  configLabel: string
  configPlaceholder: string
}> = {
  lexoffice: {
    name: 'Lexoffice',
    description: 'Verbinden Sie Ihr Lexoffice-Konto, um Rechnungen direkt zu importieren und zu validieren.',
    icon: FileSpreadsheet,
    configField: 'api_key',
    configLabel: 'API-Schluessel',
    configPlaceholder: 'Ihr Lexoffice API-Schluessel',
  },
  slack: {
    name: 'Slack',
    description: 'Erhalten Sie Validierungs-Benachrichtigungen direkt in Ihrem Slack-Kanal.',
    icon: MessageSquare,
    configField: 'webhook_url',
    configLabel: 'Webhook URL',
    configPlaceholder: 'https://hooks.slack.com/services/...',
  },
  teams: {
    name: 'Microsoft Teams',
    description: 'Erhalten Sie Validierungs-Benachrichtigungen direkt in Ihrem Teams-Kanal.',
    icon: MessageSquare,
    configField: 'webhook_url',
    configLabel: 'Webhook URL',
    configPlaceholder: 'https://outlook.office.com/webhook/...',
  },
}

export function IntegrationsPage() {
  const { data: user } = useUser()
  const { data: integrationsData, isLoading } = useIntegrations()
  const createIntegration = useCreateIntegration()
  const updateIntegration = useUpdateIntegration()
  const deleteIntegration = useDeleteIntegration()
  const testIntegration = useTestIntegration()

  const [showConfigModal, setShowConfigModal] = useState<IntegrationType | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<IntegrationType | null>(null)
  const [testResult, setTestResult] = useState<{ type: IntegrationType; success: boolean; message: string } | null>(null)

  const canUseIntegrations = user?.plan === 'pro' || user?.plan === 'steuerberater'

  if (!canUseIntegrations) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Integrationen nicht verfuegbar</h1>
          <p className="text-gray-600 mb-6">
            Integrationen sind nur mit dem Pro- oder Steuerberater-Plan verfuegbar.
          </p>
          <Link to="/preise" className="btn-primary">
            Jetzt wechseln
          </Link>
        </div>
      </div>
    )
  }

  const getIntegration = (type: IntegrationType): Integration | undefined => {
    return integrationsData?.items.find((i) => i.integration_type === type)
  }

  const handleTest = async (type: IntegrationType) => {
    try {
      const result = await testIntegration.mutateAsync(type)
      setTestResult({ type, success: result.success, message: result.message })
      setTimeout(() => setTestResult(null), 5000)
    } catch (error) {
      setTestResult({ type, success: false, message: 'Test fehlgeschlagen' })
      setTimeout(() => setTestResult(null), 5000)
    }
  }

  const handleDelete = async (type: IntegrationType) => {
    try {
      await deleteIntegration.mutateAsync(type)
      setShowDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete integration:', error)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Zurueck zum Dashboard
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrationen</h1>
          <p className="text-gray-600 mt-1">
            Verbinden Sie externe Dienste fuer automatische Benachrichtigungen und Import
          </p>
        </div>
      </div>

      {/* Test Result Banner */}
      {testResult && (
        <div
          className={cn(
            'mb-6 p-4 rounded-lg flex items-center gap-3',
            testResult.success
              ? 'bg-success-50 border border-success-200'
              : 'bg-error-50 border border-error-200'
          )}
        >
          {testResult.success ? (
            <Check className="h-5 w-5 text-success-600" />
          ) : (
            <X className="h-5 w-5 text-error-600" />
          )}
          <span className={testResult.success ? 'text-success-700' : 'text-error-700'}>
            {testResult.message}
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="p-8 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : (
        <div className="space-y-4">
          {(Object.keys(INTEGRATION_INFO) as IntegrationType[]).map((type) => {
            const info = INTEGRATION_INFO[type]
            const integration = getIntegration(type)
            const Icon = info.icon

            return (
              <div key={type} className="card p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div
                      className={cn(
                        'p-3 rounded-lg',
                        integration?.is_enabled ? 'bg-primary-100' : 'bg-gray-100'
                      )}
                    >
                      <Icon
                        className={cn(
                          'h-6 w-6',
                          integration?.is_enabled ? 'text-primary-600' : 'text-gray-400'
                        )}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{info.name}</h3>
                        {integration && (
                          <span
                            className={cn(
                              'px-2 py-0.5 text-xs rounded',
                              integration.is_enabled
                                ? 'bg-success-100 text-success-700'
                                : 'bg-gray-200 text-gray-600'
                            )}
                          >
                            {integration.is_enabled ? 'Aktiv' : 'Deaktiviert'}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{info.description}</p>

                      {integration && (
                        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-gray-500">
                          {integration.config_hint && (
                            <span className="font-mono">{integration.config_hint}</span>
                          )}
                          <span>
                            {integration.total_requests} Anfragen ({integration.successful_requests} erfolgreich)
                          </span>
                          {integration.last_used_at && (
                            <span>Zuletzt: {formatDateTime(integration.last_used_at)}</span>
                          )}
                        </div>
                      )}

                      {integration && (
                        <div className="mt-3 flex items-center gap-2">
                          <Bell className="h-4 w-4 text-gray-400" />
                          <span className="text-xs text-gray-500">Benachrichtigung bei:</span>
                          {integration.notify_on_valid && (
                            <span className="px-2 py-0.5 text-xs bg-success-50 text-success-700 rounded">
                              Gueltig
                            </span>
                          )}
                          {integration.notify_on_invalid && (
                            <span className="px-2 py-0.5 text-xs bg-error-50 text-error-700 rounded">
                              Ungueltig
                            </span>
                          )}
                          {integration.notify_on_warning && (
                            <span className="px-2 py-0.5 text-xs bg-warning-50 text-warning-700 rounded">
                              Warnung
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {integration ? (
                      <>
                        <button
                          onClick={() => handleTest(type)}
                          disabled={!integration.is_enabled || testIntegration.isPending}
                          className="btn-secondary btn-sm"
                          title="Testen"
                        >
                          <TestTube className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setShowConfigModal(type)}
                          className="btn-secondary btn-sm"
                          title="Einstellungen"
                        >
                          <Settings className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(type)}
                          className="btn-secondary btn-sm text-error-600 hover:bg-error-50"
                          title="Loeschen"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => setShowConfigModal(type)}
                        className="btn-primary btn-sm"
                      >
                        Verbinden
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Config Modal */}
      {showConfigModal && (
        <ConfigModal
          type={showConfigModal}
          integration={getIntegration(showConfigModal)}
          onClose={() => setShowConfigModal(null)}
          onCreate={async (type, data) => {
            await createIntegration.mutateAsync({ type, data })
            setShowConfigModal(null)
          }}
          onUpdate={async (type, data) => {
            await updateIntegration.mutateAsync({ type, data })
            setShowConfigModal(null)
          }}
          isLoading={createIntegration.isPending || updateIntegration.isPending}
        />
      )}

      {/* Delete Confirm Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          type={showDeleteConfirm}
          onClose={() => setShowDeleteConfirm(null)}
          onConfirm={() => handleDelete(showDeleteConfirm)}
          isLoading={deleteIntegration.isPending}
        />
      )}
    </div>
  )
}

function ConfigModal({
  type,
  integration,
  onClose,
  onCreate,
  onUpdate,
  isLoading,
}: {
  type: IntegrationType
  integration?: Integration
  onClose: () => void
  onCreate: (type: IntegrationType, data: { config: Record<string, string>; notify_on_valid: boolean; notify_on_invalid: boolean; notify_on_warning: boolean }) => Promise<void>
  onUpdate: (type: IntegrationType, data: { is_enabled?: boolean; notify_on_valid?: boolean; notify_on_invalid?: boolean; notify_on_warning?: boolean }) => Promise<void>
  isLoading: boolean
}) {
  const info = INTEGRATION_INFO[type]
  const [configValue, setConfigValue] = useState('')
  const [notifyOnValid, setNotifyOnValid] = useState(integration?.notify_on_valid ?? true)
  const [notifyOnInvalid, setNotifyOnInvalid] = useState(integration?.notify_on_invalid ?? true)
  const [notifyOnWarning, setNotifyOnWarning] = useState(integration?.notify_on_warning ?? true)
  const [isEnabled, setIsEnabled] = useState(integration?.is_enabled ?? true)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (integration) {
      await onUpdate(type, {
        is_enabled: isEnabled,
        notify_on_valid: notifyOnValid,
        notify_on_invalid: notifyOnInvalid,
        notify_on_warning: notifyOnWarning,
      })
    } else {
      await onCreate(type, {
        config: { [info.configField]: configValue },
        notify_on_valid: notifyOnValid,
        notify_on_invalid: notifyOnInvalid,
        notify_on_warning: notifyOnWarning,
      })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {integration ? `${info.name} konfigurieren` : `${info.name} verbinden`}
        </h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {!integration && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {info.configLabel} *
                </label>
                <input
                  type={info.configField === 'api_key' ? 'password' : 'url'}
                  value={configValue}
                  onChange={(e) => setConfigValue(e.target.value)}
                  placeholder={info.configPlaceholder}
                  className="input"
                  required
                />
              </div>
            )}

            {integration && (
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">Integration aktiv</label>
                <button
                  type="button"
                  onClick={() => setIsEnabled(!isEnabled)}
                  className={cn(
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                    isEnabled ? 'bg-primary-600' : 'bg-gray-200'
                  )}
                >
                  <span
                    className={cn(
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                      isEnabled ? 'translate-x-6' : 'translate-x-1'
                    )}
                  />
                </button>
              </div>
            )}

            <div className="border-t pt-4">
              <p className="text-sm font-medium text-gray-700 mb-3">Benachrichtigen bei:</p>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={notifyOnValid}
                    onChange={(e) => setNotifyOnValid(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-600">Gueltige Validierung</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={notifyOnInvalid}
                    onChange={(e) => setNotifyOnInvalid(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-600">Ungueltige Validierung</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={notifyOnWarning}
                    onChange={(e) => setNotifyOnWarning(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-600">Validierung mit Warnungen</span>
                </label>
              </div>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button type="button" onClick={onClose} className="btn-secondary flex-1" disabled={isLoading}>
              Abbrechen
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={isLoading || (!integration && !configValue.trim())}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Speichern'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function DeleteConfirmModal({
  type,
  onClose,
  onConfirm,
  isLoading,
}: {
  type: IntegrationType
  onClose: () => void
  onConfirm: () => void
  isLoading: boolean
}) {
  const info = INTEGRATION_INFO[type]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-error-100 rounded-full">
            <AlertTriangle className="h-5 w-5 text-error-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">
            {info.name} trennen?
          </h2>
        </div>
        <p className="text-gray-600 mb-6">
          Die Integration wird entfernt und Sie erhalten keine Benachrichtigungen mehr ueber
          diesen Dienst.
        </p>
        <div className="flex gap-3">
          <button onClick={onClose} className="btn-secondary flex-1" disabled={isLoading}>
            Abbrechen
          </button>
          <button
            onClick={onConfirm}
            className="btn-primary bg-error-600 hover:bg-error-700 flex-1"
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Trennen'}
          </button>
        </div>
      </div>
    </div>
  )
}
