import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Key,
  Plus,
  Copy,
  Check,
  Trash2,
  AlertTriangle,
  Clock,
  Activity,
  ArrowLeft,
  Loader2,
  Eye,
  EyeOff,
  Shield,
  BookOpen,
  ExternalLink,
} from 'lucide-react'
import { useUser } from '@/hooks/useAuth'
import { useAPIKeys, useCreateAPIKey, useDeleteAPIKey, useUpdateAPIKey } from '@/hooks/useAPIKeys'
import { cn, formatDate, formatDateTime } from '@/lib/utils'
import type { APIKey, APIKeyCreated } from '@/types'

export function APIKeysPage() {
  const { data: user } = useUser()
  const { data: apiKeysData, isLoading } = useAPIKeys()
  const createKey = useCreateAPIKey()
  const deleteKey = useDeleteAPIKey()
  const updateKey = useUpdateAPIKey()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [newKey, setNewKey] = useState<APIKeyCreated | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)

  // Check if user can use API
  const canUseApi = user?.plan === 'pro' || user?.plan === 'steuerberater'

  if (!canUseApi) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">API-Zugang nicht verfuegbar</h1>
          <p className="text-gray-600 mb-6">
            API-Zugang ist nur mit dem Pro- oder Steuerberater-Plan verfuegbar.
          </p>
          <Link to="/preise" className="btn-primary">
            Jetzt wechseln
          </Link>
        </div>
      </div>
    )
  }

  const handleCopyKey = async (key: string) => {
    await navigator.clipboard.writeText(key)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
  }

  const handleCreateKey = async (name: string, description: string, expiresInDays: number | null) => {
    try {
      const result = await createKey.mutateAsync({
        name,
        description: description || undefined,
        expires_in_days: expiresInDays || undefined,
      })
      setNewKey(result)
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create API key:', error)
    }
  }

  const handleDeleteKey = async (id: string) => {
    try {
      await deleteKey.mutateAsync(id)
      setShowDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete API key:', error)
    }
  }

  const handleToggleKey = async (key: APIKey) => {
    try {
      await updateKey.mutateAsync({
        id: key.id,
        data: { is_active: !key.is_active },
      })
    } catch (error) {
      console.error('Failed to toggle API key:', error)
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
            <h1 className="text-2xl font-bold text-gray-900">API-Schluessel</h1>
            <p className="text-gray-600 mt-1">
              Verwalten Sie Ihre API-Schluessel fuer programmatischen Zugriff
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary flex items-center gap-2"
            >
              <BookOpen className="h-4 w-4" />
              API-Dokumentation
              <ExternalLink className="h-3 w-3" />
            </a>
            <button
              onClick={() => setShowCreateModal(true)}
              disabled={apiKeysData && apiKeysData.total >= apiKeysData.max_keys}
              className="btn-primary"
            >
              <Plus className="h-4 w-4 mr-2" />
              Neuer Schluessel
            </button>
          </div>
        </div>
      </div>

      {/* Usage Stats */}
      {apiKeysData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Key className="h-8 w-8 text-primary-500" />
              <div>
                <p className="text-sm text-gray-500">API-Schluessel</p>
                <p className="text-xl font-semibold">
                  {apiKeysData.total} / {apiKeysData.max_keys}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-success-500" />
              <div>
                <p className="text-sm text-gray-500">API-Aufrufe diesen Monat</p>
                <p className="text-xl font-semibold">
                  {apiKeysData.api_calls_used} / {apiKeysData.api_calls_limit}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-warning-500" />
              <div>
                <p className="text-sm text-gray-500">Plan</p>
                <p className="text-xl font-semibold capitalize">{user?.plan}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Key Created Banner */}
      {newKey && (
        <div className="mb-6 p-4 bg-success-50 border border-success-200 rounded-lg">
          <div className="flex items-start gap-3">
            <Check className="h-5 w-5 text-success-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-success-700">API-Schluessel erstellt!</p>
              <p className="text-sm text-success-600 mt-1">
                Kopieren Sie den Schluessel jetzt - er wird nicht erneut angezeigt.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-white rounded border border-success-300 text-sm font-mono break-all">
                  {newKey.key}
                </code>
                <button
                  onClick={() => handleCopyKey(newKey.key)}
                  className="btn-secondary btn-sm"
                >
                  {copiedKey ? (
                    <Check className="h-4 w-4 text-success-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <button
                onClick={() => setNewKey(null)}
                className="mt-3 text-sm text-success-700 hover:text-success-800"
              >
                Schliessen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Ihre API-Schluessel</h2>
        </div>

        {isLoading ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : apiKeysData?.items.length === 0 ? (
          <div className="p-8 text-center">
            <Key className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">Noch keine API-Schluessel erstellt</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 btn-secondary"
            >
              Ersten Schluessel erstellen
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {apiKeysData?.items.map((key) => (
              <APIKeyRow
                key={key.id}
                apiKey={key}
                onToggle={() => handleToggleKey(key)}
                onDelete={() => setShowDeleteConfirm(key.id)}
                isDeleting={showDeleteConfirm === key.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Documentation Link */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-2">API-Dokumentation</h3>
        <p className="text-sm text-gray-600 mb-3">
          Verwenden Sie Ihren API-Schluessel im Authorization-Header:
        </p>
        <code className="block px-3 py-2 bg-gray-900 text-green-400 rounded text-sm font-mono overflow-x-auto">
          curl -H "Authorization: Bearer rc_live_xxx..." https://api.rechnungschecker.de/api/v1/validate/
        </code>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateAPIKeyModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateKey}
          isLoading={createKey.isPending}
        />
      )}

      {/* Delete Confirm Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          onClose={() => setShowDeleteConfirm(null)}
          onConfirm={() => handleDeleteKey(showDeleteConfirm)}
          isLoading={deleteKey.isPending}
        />
      )}
    </div>
  )
}

function APIKeyRow({
  apiKey,
  onToggle,
  onDelete,
  isDeleting,
}: {
  apiKey: APIKey
  onToggle: () => void
  onDelete: () => void
  isDeleting: boolean
}) {
  const isExpired = apiKey.expires_at && new Date(apiKey.expires_at) < new Date()

  return (
    <div className={cn('px-6 py-4', !apiKey.is_active && 'bg-gray-50')}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-gray-900">{apiKey.name}</h3>
            {!apiKey.is_active && (
              <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded">
                Deaktiviert
              </span>
            )}
            {isExpired && (
              <span className="px-2 py-0.5 text-xs bg-error-100 text-error-700 rounded">
                Abgelaufen
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1 font-mono">{apiKey.key_prefix}</p>
          {apiKey.description && (
            <p className="text-sm text-gray-500 mt-1">{apiKey.description}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Erstellt: {formatDate(apiKey.created_at)}
            </span>
            {apiKey.last_used_at && (
              <span>Letzte Nutzung: {formatDateTime(apiKey.last_used_at)}</span>
            )}
            <span>{apiKey.requests_this_month} Aufrufe diesen Monat</span>
          </div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={onToggle}
            className={cn(
              'p-2 rounded hover:bg-gray-100',
              apiKey.is_active ? 'text-success-600' : 'text-gray-400'
            )}
            title={apiKey.is_active ? 'Deaktivieren' : 'Aktivieren'}
          >
            {apiKey.is_active ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
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
  )
}

function CreateAPIKeyModal({
  onClose,
  onCreate,
  isLoading,
}: {
  onClose: () => void
  onCreate: (name: string, description: string, expiresInDays: number | null) => void
  isLoading: boolean
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [expiresInDays, setExpiresInDays] = useState<string>('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate(name, description, expiresInDays ? parseInt(expiresInDays) : null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Neuen API-Schluessel erstellen
        </h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="z.B. Produktions-Server"
                className="input"
                required
                maxLength={100}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beschreibung
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional: Wofuer wird dieser Schluessel verwendet?"
                className="input"
                rows={2}
                maxLength={500}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ablauf (Tage)
              </label>
              <input
                type="number"
                value={expiresInDays}
                onChange={(e) => setExpiresInDays(e.target.value)}
                placeholder="Leer = kein Ablauf"
                className="input"
                min={1}
                max={365}
              />
              <p className="text-xs text-gray-500 mt-1">
                Leer lassen fuer unbegrenzten Schluessel
              </p>
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={isLoading}
            >
              Abbrechen
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={isLoading || !name.trim()}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Erstellen'
              )}
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
          <h2 className="text-lg font-semibold text-gray-900">
            Schluessel loeschen?
          </h2>
        </div>
        <p className="text-gray-600 mb-6">
          Diese Aktion kann nicht rueckgaengig gemacht werden. Alle Anwendungen, die
          diesen Schluessel verwenden, werden keinen Zugriff mehr haben.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="btn-secondary flex-1"
            disabled={isLoading}
          >
            Abbrechen
          </button>
          <button
            onClick={onConfirm}
            className="btn-primary bg-error-600 hover:bg-error-700 flex-1"
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Loeschen'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
