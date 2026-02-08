import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText,
  Plus,
  ArrowLeft,
  Loader2,
  MoreVertical,
  Pencil,
  Trash2,
  Star,
  Building2,
  User,
  AlertTriangle,
  AlertCircle,
  MapPin,
} from 'lucide-react'
import {
  useTemplates,
  useTemplate,
  useCreateTemplate,
  useDeleteTemplate,
  useUpdateTemplate,
  useSetDefaultTemplate,
} from '@/hooks/useTemplates'
import { cn } from '@/lib/utils'
import { AddressInput } from '@/components'
import type { Template, TemplateListItem, TemplateCreateRequest, TemplateType } from '@/types'

export function TemplatesPage() {
  const [activeTab, setActiveTab] = useState<TemplateType>('sender')
  const { data: templatesData, isLoading } = useTemplates(activeTab)
  const createTemplate = useCreateTemplate()
  const deleteTemplate = useDeleteTemplate()
  const updateTemplate = useUpdateTemplate()
  const setDefaultTemplate = useSetDefaultTemplate()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch full template data when editing
  const { data: editingTemplate, isLoading: isLoadingTemplate } = useTemplate(editingTemplateId)

  const handleCreateTemplate = async (data: TemplateCreateRequest) => {
    try {
      setError(null)
      await createTemplate.mutateAsync(data)
      setShowCreateModal(false)
    } catch (err) {
      setError('Vorlage konnte nicht erstellt werden')
    }
  }

  const handleUpdateTemplate = async (id: string, data: Partial<TemplateCreateRequest>) => {
    try {
      setError(null)
      await updateTemplate.mutateAsync({ id, data })
      setEditingTemplateId(null)
    } catch (err) {
      setError('Vorlage konnte nicht aktualisiert werden')
    }
  }

  const handleDeleteTemplate = async (id: string) => {
    try {
      setError(null)
      await deleteTemplate.mutateAsync(id)
      setShowDeleteConfirm(null)
    } catch (err) {
      setError('Vorlage konnte nicht gelöscht werden')
    }
  }

  const handleSetDefault = async (id: string) => {
    try {
      setError(null)
      await setDefaultTemplate.mutateAsync(id)
    } catch (err) {
      setError('Standard konnte nicht gesetzt werden')
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
            <h1 className="text-2xl font-bold text-gray-900">Vorlagen</h1>
            <p className="text-gray-600 mt-1">
              Speichern Sie häufig verwendete Absender- und Empfängerdaten
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Neue Vorlage
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

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit mb-6">
        <button
          onClick={() => setActiveTab('sender')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
            activeTab === 'sender'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <Building2 className="h-4 w-4" />
          Absender
        </button>
        <button
          onClick={() => setActiveTab('receiver')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
            activeTab === 'receiver'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <User className="h-4 w-4" />
          Empfänger
        </button>
      </div>

      {/* Templates Grid */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">
            {activeTab === 'sender' ? 'Absender-Vorlagen' : 'Empfänger-Vorlagen'}
          </h2>
        </div>

        {isLoading ? (
          <div className="p-8 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : templatesData?.items.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              Noch keine {activeTab === 'sender' ? 'Absender' : 'Empfänger'}-Vorlagen angelegt
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 btn-secondary"
            >
              Erste Vorlage anlegen
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
            {templatesData?.items.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onEdit={() => setEditingTemplateId(template.id)}
                onSetDefault={() => handleSetDefault(template.id)}
                onDelete={() => setShowDeleteConfirm(template.id)}
                isSettingDefault={setDefaultTemplate.isPending}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <TemplateFormModal
          title={`Neue ${activeTab === 'sender' ? 'Absender' : 'Empfänger'}-Vorlage`}
          templateType={activeTab}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateTemplate}
          isLoading={createTemplate.isPending}
        />
      )}

      {/* Edit Modal */}
      {editingTemplateId && editingTemplate && (
        <TemplateFormModal
          title="Vorlage bearbeiten"
          templateType={editingTemplate.template_type}
          initialData={editingTemplate}
          onClose={() => setEditingTemplateId(null)}
          onSubmit={(data) => handleUpdateTemplate(editingTemplate.id, data)}
          isLoading={updateTemplate.isPending || isLoadingTemplate}
        />
      )}
      {/* Loading state for edit modal */}
      {editingTemplateId && isLoadingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setEditingTemplateId(null)} />
          <div className="relative bg-white rounded-xl shadow-xl p-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        </div>
      )}

      {/* Delete Confirm Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          onClose={() => setShowDeleteConfirm(null)}
          onConfirm={() => handleDeleteTemplate(showDeleteConfirm)}
          isLoading={deleteTemplate.isPending}
        />
      )}
    </div>
  )
}

function TemplateCard({
  template,
  onEdit,
  onSetDefault,
  onDelete,
  isSettingDefault,
}: {
  template: TemplateListItem
  onEdit: () => void
  onSetDefault: () => void
  onDelete: () => void
  isSettingDefault: boolean
}) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div
      className={cn(
        'border rounded-lg p-4 hover:shadow-md transition-shadow relative',
        template.is_default ? 'border-primary-300 bg-primary-50' : 'border-gray-200'
      )}
    >
      {template.is_default && (
        <div className="absolute -top-2 -right-2 bg-primary-500 text-white rounded-full p-1">
          <Star className="h-4 w-4 fill-current" />
        </div>
      )}

      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {template.template_type === 'sender' ? (
            <Building2 className="h-5 w-5 text-gray-400" />
          ) : (
            <User className="h-5 w-5 text-gray-400" />
          )}
          <h3 className="font-medium text-gray-900">{template.name}</h3>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 rounded hover:bg-gray-100"
          >
            <MoreVertical className="h-4 w-4 text-gray-400" />
          </button>
          {showMenu && (
            <>
              <div className="fixed inset-0" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
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
                {!template.is_default && (
                  <button
                    onClick={() => {
                      onSetDefault()
                      setShowMenu(false)
                    }}
                    disabled={isSettingDefault}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Star className="h-4 w-4" />
                    Als Standard
                  </button>
                )}
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

      <p className="text-sm font-medium text-gray-700 mb-1">{template.company_name}</p>
      {template.city && (
        <p className="text-sm text-gray-500 flex items-center gap-1">
          <MapPin className="h-3 w-3" />
          {template.city}
        </p>
      )}

      {template.is_default && (
        <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-primary-100 text-primary-700 rounded">
          Standard
        </span>
      )}
    </div>
  )
}

function TemplateFormModal({
  title,
  templateType,
  initialData,
  onClose,
  onSubmit,
  isLoading,
}: {
  title: string
  templateType: TemplateType
  initialData?: Partial<Template>
  onClose: () => void
  onSubmit: (data: TemplateCreateRequest) => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState<TemplateCreateRequest>({
    name: initialData?.name || '',
    template_type: templateType,
    company_name: initialData?.company_name || '',
    street: initialData?.street || '',
    postal_code: initialData?.postal_code || '',
    city: initialData?.city || '',
    country_code: initialData?.country_code || 'DE',
    vat_id: initialData?.vat_id || '',
    tax_id: initialData?.tax_id || '',
    email: initialData?.email || '',
    phone: initialData?.phone || '',
    iban: initialData?.iban || '',
    bic: initialData?.bic || '',
    is_default: initialData?.is_default || false,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const updateField = (field: keyof TemplateCreateRequest, value: string | boolean) => {
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
            {/* Template Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Vorlagenname *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                className="input"
                required
                maxLength={100}
                placeholder="z.B. Meine Firma GmbH"
              />
            </div>

            {/* Company Info */}
            <div className="md:col-span-2 mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Firmendaten</h3>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Firmenname *
              </label>
              <input
                type="text"
                value={formData.company_name}
                onChange={(e) => updateField('company_name', e.target.value)}
                className="input"
                required
                maxLength={200}
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Steuernummer
              </label>
              <input
                type="text"
                value={formData.tax_id}
                onChange={(e) => updateField('tax_id', e.target.value)}
                className="input"
                maxLength={30}
              />
            </div>

            {/* Address */}
            <div className="md:col-span-2 mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Adresse</h3>
            </div>
            <div className="md:col-span-2">
              <AddressInput
                values={{
                  street: formData.street,
                  postalCode: formData.postal_code,
                  city: formData.city,
                  countryCode: formData.country_code,
                }}
                onChange={(fields) => {
                  setFormData((prev) => ({
                    ...prev,
                    street: fields.street || '',
                    postal_code: fields.postalCode || '',
                    city: fields.city || '',
                    country_code: fields.countryCode || 'DE',
                  }))
                }}
              />
            </div>

            {/* Contact */}
            <div className="md:col-span-2 mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Kontakt</h3>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                E-Mail
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => updateField('email', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Telefon
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                className="input"
                maxLength={50}
              />
            </div>

            {/* Bank Details (for sender) */}
            {templateType === 'sender' && (
              <>
                <div className="md:col-span-2 mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Bankverbindung</h3>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    IBAN
                  </label>
                  <input
                    type="text"
                    value={formData.iban}
                    onChange={(e) => updateField('iban', e.target.value)}
                    className="input"
                    maxLength={34}
                    placeholder="DE89370400440532013000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    BIC
                  </label>
                  <input
                    type="text"
                    value={formData.bic}
                    onChange={(e) => updateField('bic', e.target.value)}
                    className="input"
                    maxLength={11}
                    placeholder="COBADEFFXXX"
                  />
                </div>
              </>
            )}

            {/* Default checkbox */}
            <div className="md:col-span-2 mt-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => updateField('is_default', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-gray-700">Als Standard-Vorlage verwenden</span>
              </label>
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
              disabled={isLoading || !formData.name.trim() || !formData.company_name.trim()}
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
          <h2 className="text-lg font-semibold text-gray-900">Vorlage löschen?</h2>
        </div>
        <p className="text-gray-600 mb-6">
          Diese Aktion kann nicht rückgängig gemacht werden.
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

export default TemplatesPage
