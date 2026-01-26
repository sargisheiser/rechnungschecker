import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Users,
  Plus,
  Search,
  Building2,
  FileCheck,
  Clock,
  ArrowLeft,
  Loader2,
  MoreVertical,
  Pencil,
  Trash2,
  Eye,
  EyeOff,
  AlertTriangle,
  AlertCircle,
} from 'lucide-react'
import { useUser } from '@/hooks/useAuth'
import {
  useClients,
  useClientStats,
  useCreateClient,
  useDeleteClient,
  useUpdateClient,
  useClientContext,
} from '@/hooks/useClients'
import { cn, formatDateTime } from '@/lib/utils'
import type { Client, ClientListItem, ClientCreateRequest } from '@/types'

export function ClientsPage() {
  const { data: user } = useUser()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const { data: clientsData, isLoading } = useClients(page, 20, !showInactive, search || undefined)
  const { data: stats } = useClientStats()
  const createClient = useCreateClient()
  const deleteClient = useDeleteClient()
  const updateClient = useUpdateClient()
  const { selectedClientId, setSelectedClientId } = useClientContext()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Check if user can manage clients
  const canManageClients = user?.plan === 'steuerberater'

  if (!canManageClients) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <Users className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Mandantenverwaltung nicht verfügbar</h1>
          <p className="text-gray-600 mb-6">
            Mandantenverwaltung ist nur mit dem Steuerberater-Plan verfügbar.
          </p>
          <Link to="/preise" className="btn-primary">
            Jetzt wechseln
          </Link>
        </div>
      </div>
    )
  }

  const handleCreateClient = async (data: ClientCreateRequest) => {
    try {
      setError(null)
      await createClient.mutateAsync(data)
      setShowCreateModal(false)
    } catch (err) {
      setError('Mandant konnte nicht erstellt werden')
    }
  }

  const handleUpdateClient = async (id: string, data: Partial<ClientCreateRequest> & { is_active?: boolean }) => {
    try {
      setError(null)
      await updateClient.mutateAsync({ id, data })
      setEditingClient(null)
    } catch (err) {
      setError('Mandant konnte nicht aktualisiert werden')
    }
  }

  const handleDeleteClient = async (id: string) => {
    try {
      setError(null)
      await deleteClient.mutateAsync(id)
      setShowDeleteConfirm(null)
    } catch (err) {
      setError('Mandant konnte nicht gelöscht werden')
    }
  }

  const handleToggleActive = async (client: ClientListItem) => {
    try {
      setError(null)
      await updateClient.mutateAsync({
        id: client.id,
        data: { is_active: !client.is_active },
      })
    } catch (err) {
      setError('Status konnte nicht geändert werden')
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Zurück zum Dashboard
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Mandantenverwaltung</h1>
            <p className="text-gray-600 mt-1">
              Verwalten Sie Ihre Mandanten und deren Validierungen
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={stats && stats.total_clients >= stats.max_clients}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Neuer Mandant
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-error-600" />
          <p className="text-error-700">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto text-error-600 hover:text-error-700">
            ×
          </button>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-primary-500" />
              <div>
                <p className="text-sm text-gray-500">Mandanten</p>
                <p className="text-xl font-semibold">
                  {stats.total_clients} / {stats.max_clients}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-8 w-8 text-success-500" />
              <div>
                <p className="text-sm text-gray-500">Aktive Mandanten</p>
                <p className="text-xl font-semibold">{stats.active_clients}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <FileCheck className="h-8 w-8 text-warning-500" />
              <div>
                <p className="text-sm text-gray-500">Validierungen gesamt</p>
                <p className="text-xl font-semibold">{stats.total_validations}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-gray-400" />
              <div>
                <p className="text-sm text-gray-500">Ausgewählter Mandant</p>
                <p className="text-sm font-medium truncate">
                  {selectedClientId
                    ? clientsData?.items.find((c) => c.id === selectedClientId)?.name || 'Laden...'
                    : 'Alle Mandanten'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Mandanten suchen..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10 w-full"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="rounded border-gray-300"
          />
          Inaktive anzeigen
        </label>
      </div>

      {/* Clients List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Ihre Mandanten</h2>
        </div>

        {isLoading ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : clientsData?.items.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              {search ? 'Keine Mandanten gefunden' : 'Noch keine Mandanten angelegt'}
            </p>
            {!search && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 btn-secondary"
              >
                Ersten Mandanten anlegen
              </button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {clientsData?.items.map((client) => (
              <ClientRow
                key={client.id}
                client={client}
                isSelected={selectedClientId === client.id}
                onSelect={() =>
                  setSelectedClientId(selectedClientId === client.id ? null : client.id)
                }
                onEdit={() => {
                  // Fetch full client data for editing
                  setEditingClient(client as unknown as Client)
                }}
                onToggle={() => handleToggleActive(client)}
                onDelete={() => setShowDeleteConfirm(client.id)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {clientsData && clientsData.total > clientsData.page_size && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Seite {clientsData.page} von {Math.ceil(clientsData.total / clientsData.page_size)}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary btn-sm"
              >
                Zurück
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * clientsData.page_size >= clientsData.total}
                className="btn-secondary btn-sm"
              >
                Weiter
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <ClientFormModal
          title="Neuen Mandanten anlegen"
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateClient}
          isLoading={createClient.isPending}
        />
      )}

      {/* Edit Modal */}
      {editingClient && (
        <ClientFormModal
          title="Mandant bearbeiten"
          initialData={editingClient}
          onClose={() => setEditingClient(null)}
          onSubmit={(data) => handleUpdateClient(editingClient.id, data)}
          isLoading={updateClient.isPending}
        />
      )}

      {/* Delete Confirm Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          onClose={() => setShowDeleteConfirm(null)}
          onConfirm={() => handleDeleteClient(showDeleteConfirm)}
          isLoading={deleteClient.isPending}
        />
      )}
    </div>
  )
}

function ClientRow({
  client,
  isSelected,
  onSelect,
  onEdit,
  onToggle,
  onDelete,
}: {
  client: ClientListItem
  isSelected: boolean
  onSelect: () => void
  onEdit: () => void
  onToggle: () => void
  onDelete: () => void
}) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div
      className={cn(
        'px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors',
        isSelected && 'bg-primary-50 hover:bg-primary-100',
        !client.is_active && 'opacity-60'
      )}
    >
      <div className="flex items-center gap-4 min-w-0 flex-1">
        <button
          onClick={onSelect}
          className={cn(
            'h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0',
            isSelected ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'
          )}
        >
          <Building2 className="h-5 w-5" />
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="font-medium text-gray-900 truncate">{client.name}</p>
            {client.client_number && (
              <span className="text-xs text-gray-500">#{client.client_number}</span>
            )}
            {!client.is_active && (
              <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded">
                Inaktiv
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
            <span>{client.validation_count} Validierungen</span>
            {client.last_validation_at && (
              <span>Letzte: {formatDateTime(client.last_validation_at)}</span>
            )}
          </div>
        </div>
      </div>
      <div className="relative ml-4">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="p-2 rounded hover:bg-gray-100"
        >
          <MoreVertical className="h-4 w-4 text-gray-400" />
        </button>
        {showMenu && (
          <>
            <div className="fixed inset-0" onClick={() => setShowMenu(false)} />
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
              <button
                onClick={() => {
                  onSelect()
                  setShowMenu(false)
                }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
              >
                <FileCheck className="h-4 w-4" />
                {isSelected ? 'Abwählen' : 'Auswählen'}
              </button>
              <button
                onClick={() => {
                  onEdit()
                  setShowMenu(false)
                }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
              >
                <Pencil className="h-4 w-4" />
                Bearbeiten
              </button>
              <button
                onClick={() => {
                  onToggle()
                  setShowMenu(false)
                }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
              >
                {client.is_active ? (
                  <>
                    <EyeOff className="h-4 w-4" />
                    Deaktivieren
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4" />
                    Aktivieren
                  </>
                )}
              </button>
              <hr className="my-1" />
              <button
                onClick={() => {
                  onDelete()
                  setShowMenu(false)
                }}
                className="w-full px-4 py-2 text-left text-sm text-error-600 hover:bg-error-50 flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Löschen
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function ClientFormModal({
  title,
  initialData,
  onClose,
  onSubmit,
  isLoading,
}: {
  title: string
  initialData?: Partial<Client>
  onClose: () => void
  onSubmit: (data: ClientCreateRequest) => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState<ClientCreateRequest>({
    name: initialData?.name || '',
    client_number: initialData?.client_number || '',
    tax_number: initialData?.tax_number || '',
    vat_id: initialData?.vat_id || '',
    contact_name: initialData?.contact_name || '',
    contact_email: initialData?.contact_email || '',
    contact_phone: initialData?.contact_phone || '',
    street: initialData?.street || '',
    postal_code: initialData?.postal_code || '',
    city: initialData?.city || '',
    country: initialData?.country || 'DE',
    notes: initialData?.notes || '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const updateField = (field: keyof ClientCreateRequest, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value || undefined }))
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto py-8">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Info */}
            <div className="md:col-span-2">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Grunddaten</h3>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Firmenname / Mandantenname *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                className="input"
                required
                maxLength={200}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mandantennummer
              </label>
              <input
                type="text"
                value={formData.client_number}
                onChange={(e) => updateField('client_number', e.target.value)}
                className="input"
                maxLength={50}
                placeholder="z.B. M-2024-001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Steuernummer
              </label>
              <input
                type="text"
                value={formData.tax_number}
                onChange={(e) => updateField('tax_number', e.target.value)}
                className="input"
                maxLength={50}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                USt-IdNr.
              </label>
              <input
                type="text"
                value={formData.vat_id}
                onChange={(e) => updateField('vat_id', e.target.value)}
                className="input"
                maxLength={20}
                placeholder="DE123456789"
              />
            </div>

            {/* Contact */}
            <div className="md:col-span-2 mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Kontakt</h3>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ansprechpartner
              </label>
              <input
                type="text"
                value={formData.contact_name}
                onChange={(e) => updateField('contact_name', e.target.value)}
                className="input"
                maxLength={200}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                E-Mail
              </label>
              <input
                type="email"
                value={formData.contact_email}
                onChange={(e) => updateField('contact_email', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Telefon
              </label>
              <input
                type="tel"
                value={formData.contact_phone}
                onChange={(e) => updateField('contact_phone', e.target.value)}
                className="input"
                maxLength={50}
              />
            </div>

            {/* Address */}
            <div className="md:col-span-2 mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Adresse</h3>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Straße
              </label>
              <input
                type="text"
                value={formData.street}
                onChange={(e) => updateField('street', e.target.value)}
                className="input"
                maxLength={255}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PLZ
              </label>
              <input
                type="text"
                value={formData.postal_code}
                onChange={(e) => updateField('postal_code', e.target.value)}
                className="input"
                maxLength={10}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ort
              </label>
              <input
                type="text"
                value={formData.city}
                onChange={(e) => updateField('city', e.target.value)}
                className="input"
                maxLength={100}
              />
            </div>

            {/* Notes */}
            <div className="md:col-span-2 mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notizen
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => updateField('notes', e.target.value)}
                className="input"
                rows={3}
                maxLength={2000}
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6 pt-4 border-t border-gray-200">
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
              disabled={isLoading || !formData.name.trim()}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : initialData ? (
                'Speichern'
              ) : (
                'Anlegen'
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
          <h2 className="text-lg font-semibold text-gray-900">Mandant löschen?</h2>
        </div>
        <p className="text-gray-600 mb-6">
          Diese Aktion kann nicht rückgängig gemacht werden. Alle zugehörigen
          Validierungen bleiben erhalten, werden aber nicht mehr diesem Mandanten
          zugeordnet.
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
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Löschen'}
          </button>
        </div>
      </div>
    </div>
  )
}
