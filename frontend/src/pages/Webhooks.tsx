import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Webhook,
  ArrowLeft,
  Loader2,
  Shield,
  Plus,
  Check,
  Copy,
  Trash2,
  AlertTriangle,
  Eye,
  EyeOff,
  TestTube,
  RefreshCw,
  Activity,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { useUser } from '@/hooks/useAuth'
import {
  useWebhooks,
  useWebhook,
  useCreateWebhook,
  useUpdateWebhook,
  useDeleteWebhook,
  useTestWebhook,
  useRotateWebhookSecret,
} from '@/hooks/useWebhooks'
import { cn, formatDateTime } from '@/lib/utils'
import type { Webhook as WebhookType, WebhookCreated, WebhookEventType, WebhookDelivery } from '@/types'

const EVENT_OPTIONS: { value: WebhookEventType; label: string; description: string }[] = [
  {
    value: 'validation.completed',
    label: 'Validierung abgeschlossen',
    description: 'Wird ausgeloest, wenn eine Validierung erfolgreich war',
  },
  {
    value: 'validation.failed',
    label: 'Validierung fehlgeschlagen',
    description: 'Wird ausgeloest, wenn eine Validierung Fehler enthaelt',
  },
]

export function WebhooksPage() {
  const { data: user } = useUser()
  const { data: webhooksData, isLoading } = useWebhooks()
  const createWebhook = useCreateWebhook()
  const updateWebhook = useUpdateWebhook()
  const deleteWebhook = useDeleteWebhook()
  const testWebhook = useTestWebhook()
  const rotateSecret = useRotateWebhookSecret()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [newWebhook, setNewWebhook] = useState<WebhookCreated | null>(null)
  const [copiedSecret, setCopiedSecret] = useState(false)
  const [expandedWebhook, setExpandedWebhook] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})

  const canUseWebhooks = user?.plan === 'pro' || user?.plan === 'steuerberater'

  if (!canUseWebhooks) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Webhooks nicht verfuegbar</h1>
          <p className="text-gray-600 mb-6">
            Webhooks sind nur mit dem Pro- oder Steuerberater-Plan verfuegbar.
          </p>
          <Link to="/preise" className="btn-primary">
            Jetzt wechseln
          </Link>
        </div>
      </div>
    )
  }

  const handleCopySecret = async (secret: string) => {
    await navigator.clipboard.writeText(secret)
    setCopiedSecret(true)
    setTimeout(() => setCopiedSecret(false), 2000)
  }

  const handleCreate = async (url: string, events: WebhookEventType[], description?: string) => {
    try {
      const result = await createWebhook.mutateAsync({ url, events, description })
      setNewWebhook(result)
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create webhook:', error)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteWebhook.mutateAsync(id)
      setShowDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete webhook:', error)
    }
  }

  const handleToggle = async (webhook: WebhookType) => {
    try {
      await updateWebhook.mutateAsync({
        id: webhook.id,
        data: { is_active: !webhook.is_active },
      })
    } catch (error) {
      console.error('Failed to toggle webhook:', error)
    }
  }

  const handleTest = async (id: string) => {
    try {
      const result = await testWebhook.mutateAsync(id)
      setTestResults((prev) => ({
        ...prev,
        [id]: { success: result.success, message: result.message },
      }))
      setTimeout(() => {
        setTestResults((prev) => {
          const { [id]: _, ...rest } = prev
          return rest
        })
      }, 5000)
    } catch (error) {
      setTestResults((prev) => ({
        ...prev,
        [id]: { success: false, message: 'Test fehlgeschlagen' },
      }))
    }
  }

  const handleRotateSecret = async (id: string) => {
    try {
      const result = await rotateSecret.mutateAsync(id)
      setNewWebhook(result)
    } catch (error) {
      console.error('Failed to rotate secret:', error)
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Webhooks</h1>
            <p className="text-gray-600 mt-1">
              Erhalten Sie automatische Benachrichtigungen bei Validierungen
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={webhooksData && webhooksData.total >= webhooksData.max_webhooks}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Neuer Webhook
          </button>
        </div>
      </div>

      {/* Usage Stats */}
      {webhooksData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Webhook className="h-8 w-8 text-primary-500" />
              <div>
                <p className="text-sm text-gray-500">Webhooks</p>
                <p className="text-xl font-semibold">
                  {webhooksData.total} / {webhooksData.max_webhooks}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-success-500" />
              <div>
                <p className="text-sm text-gray-500">Aktive Webhooks</p>
                <p className="text-xl font-semibold">
                  {webhooksData.items.filter((w) => w.is_active).length}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-warning-500" />
              <div>
                <p className="text-sm text-gray-500">Gesamt Zustellungen</p>
                <p className="text-xl font-semibold">
                  {webhooksData.items.reduce((sum, w) => sum + w.total_deliveries, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Webhook Secret Banner */}
      {newWebhook && (
        <div className="mb-6 p-4 bg-success-50 border border-success-200 rounded-lg">
          <div className="flex items-start gap-3">
            <Check className="h-5 w-5 text-success-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-success-700">
                Webhook {newWebhook.id === webhooksData?.items[0]?.id ? 'erstellt' : 'Secret erneuert'}!
              </p>
              <p className="text-sm text-success-600 mt-1">
                Kopieren Sie das Secret jetzt - es wird nicht erneut angezeigt.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-white rounded border border-success-300 text-sm font-mono break-all">
                  {newWebhook.secret}
                </code>
                <button
                  onClick={() => handleCopySecret(newWebhook.secret)}
                  className="btn-secondary btn-sm"
                >
                  {copiedSecret ? (
                    <Check className="h-4 w-4 text-success-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <button
                onClick={() => setNewWebhook(null)}
                className="mt-3 text-sm text-success-700 hover:text-success-800"
              >
                Schliessen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Webhooks List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Ihre Webhooks</h2>
        </div>

        {isLoading ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : webhooksData?.items.length === 0 ? (
          <div className="p-8 text-center">
            <Webhook className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">Noch keine Webhooks erstellt</p>
            <button onClick={() => setShowCreateModal(true)} className="mt-4 btn-secondary">
              Ersten Webhook erstellen
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {webhooksData?.items.map((webhook) => (
              <WebhookRow
                key={webhook.id}
                webhook={webhook}
                isExpanded={expandedWebhook === webhook.id}
                onToggleExpand={() =>
                  setExpandedWebhook(expandedWebhook === webhook.id ? null : webhook.id)
                }
                onToggle={() => handleToggle(webhook)}
                onTest={() => handleTest(webhook.id)}
                onRotateSecret={() => handleRotateSecret(webhook.id)}
                onDelete={() => setShowDeleteConfirm(webhook.id)}
                testResult={testResults[webhook.id]}
                isDeleting={showDeleteConfirm === webhook.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Documentation */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-2">Webhook-Signatur</h3>
        <p className="text-sm text-gray-600 mb-3">
          Jeder Webhook wird mit einem HMAC-SHA256-Header signiert. Verifizieren Sie die Signatur:
        </p>
        <code className="block px-3 py-2 bg-gray-900 text-green-400 rounded text-sm font-mono overflow-x-auto">
          X-Webhook-Signature: sha256=...
        </code>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateWebhookModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
          isLoading={createWebhook.isPending}
        />
      )}

      {/* Delete Confirm Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          onClose={() => setShowDeleteConfirm(null)}
          onConfirm={() => handleDelete(showDeleteConfirm)}
          isLoading={deleteWebhook.isPending}
        />
      )}
    </div>
  )
}

function WebhookRow({
  webhook,
  isExpanded,
  onToggleExpand,
  onToggle,
  onTest,
  onRotateSecret,
  onDelete,
  testResult,
  isDeleting,
}: {
  webhook: WebhookType
  isExpanded: boolean
  onToggleExpand: () => void
  onToggle: () => void
  onTest: () => void
  onRotateSecret: () => void
  onDelete: () => void
  testResult?: { success: boolean; message: string }
  isDeleting: boolean
}) {
  const { data: webhookDetails } = useWebhook(isExpanded ? webhook.id : '')

  return (
    <div className={cn(!webhook.is_active && 'bg-gray-50')}>
      <div className="px-6 py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <button
                onClick={onToggleExpand}
                className="text-gray-400 hover:text-gray-600"
              >
                {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              <span className="font-mono text-sm text-gray-900 truncate">{webhook.url}</span>
              {!webhook.is_active && (
                <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded">
                  Deaktiviert
                </span>
              )}
            </div>
            {webhook.description && (
              <p className="text-sm text-gray-500 mt-1 ml-6">{webhook.description}</p>
            )}
            <div className="flex items-center gap-4 mt-2 ml-6 text-xs text-gray-400">
              <span>Events: {webhook.events.join(', ')}</span>
              <span>
                {webhook.successful_deliveries}/{webhook.total_deliveries} erfolgreich
              </span>
              {webhook.last_triggered_at && (
                <span>Zuletzt: {formatDateTime(webhook.last_triggered_at)}</span>
              )}
            </div>
            {testResult && (
              <div
                className={cn(
                  'mt-2 ml-6 px-3 py-1 rounded text-sm inline-flex items-center gap-2',
                  testResult.success
                    ? 'bg-success-50 text-success-700'
                    : 'bg-error-50 text-error-700'
                )}
              >
                {testResult.success ? <Check className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                {testResult.message}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={onToggle}
              className={cn(
                'p-2 rounded hover:bg-gray-100',
                webhook.is_active ? 'text-success-600' : 'text-gray-400'
              )}
              title={webhook.is_active ? 'Deaktivieren' : 'Aktivieren'}
            >
              {webhook.is_active ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            </button>
            <button
              onClick={onTest}
              disabled={!webhook.is_active}
              className="p-2 rounded hover:bg-gray-100 text-gray-600 disabled:opacity-50"
              title="Testen"
            >
              <TestTube className="h-4 w-4" />
            </button>
            <button
              onClick={onRotateSecret}
              className="p-2 rounded hover:bg-gray-100 text-gray-600"
              title="Secret erneuern"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button
              onClick={onDelete}
              disabled={isDeleting}
              className="p-2 rounded hover:bg-error-50 text-error-600"
              title="Loeschen"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Deliveries */}
      {isExpanded && webhookDetails && (
        <div className="px-6 pb-4">
          <div className="ml-6 border-l-2 border-gray-200 pl-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Letzte Zustellungen</h4>
            {webhookDetails.recent_deliveries.length === 0 ? (
              <p className="text-sm text-gray-500">Noch keine Zustellungen</p>
            ) : (
              <div className="space-y-2">
                {webhookDetails.recent_deliveries.slice(0, 5).map((delivery) => (
                  <DeliveryRow key={delivery.id} delivery={delivery} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function DeliveryRow({ delivery }: { delivery: WebhookDelivery }) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-600',
    success: 'bg-success-100 text-success-700',
    failed: 'bg-error-100 text-error-700',
    retrying: 'bg-warning-100 text-warning-700',
  }

  return (
    <div className="flex items-center gap-4 text-sm">
      <span className={cn('px-2 py-0.5 rounded text-xs', statusColors[delivery.status])}>
        {delivery.status}
      </span>
      <span className="text-gray-600">{delivery.event_type}</span>
      {delivery.response_status_code && (
        <span className="text-gray-500">HTTP {delivery.response_status_code}</span>
      )}
      {delivery.response_time_ms && (
        <span className="text-gray-400">{delivery.response_time_ms}ms</span>
      )}
      <span className="text-gray-400">{formatDateTime(delivery.created_at)}</span>
    </div>
  )
}

function CreateWebhookModal({
  onClose,
  onCreate,
  isLoading,
}: {
  onClose: () => void
  onCreate: (url: string, events: WebhookEventType[], description?: string) => void
  isLoading: boolean
}) {
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [events, setEvents] = useState<WebhookEventType[]>(['validation.completed', 'validation.failed'])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate(url, events, description || undefined)
  }

  const toggleEvent = (event: WebhookEventType) => {
    setEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Neuen Webhook erstellen</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Webhook URL *
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/webhook"
                className="input"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beschreibung
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="z.B. Produktions-Webhook"
                className="input"
                maxLength={200}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Events *
              </label>
              <div className="space-y-2">
                {EVENT_OPTIONS.map((option) => (
                  <label key={option.value} className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={events.includes(option.value)}
                      onChange={() => toggleEvent(option.value)}
                      className="mt-1 rounded"
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-900">{option.label}</span>
                      <p className="text-xs text-gray-500">{option.description}</p>
                    </div>
                  </label>
                ))}
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
              disabled={isLoading || !url.trim() || events.length === 0}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function DeleteConfirmModal({
  onClose,
  onConfirm,
  isLoading,
}: {
  onClose: () => void
  onConfirm: () => void
  isLoading: boolean
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-error-100 rounded-full">
            <AlertTriangle className="h-5 w-5 text-error-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Webhook loeschen?</h2>
        </div>
        <p className="text-gray-600 mb-6">
          Diese Aktion kann nicht rueckgaengig gemacht werden. Sie erhalten keine
          Benachrichtigungen mehr an diese URL.
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
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Loeschen'}
          </button>
        </div>
      </div>
    </div>
  )
}
