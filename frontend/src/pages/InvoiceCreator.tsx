import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import {
  FileText,
  Plus,
  Trash2,
  Download,
  Check,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Building2,
  User,
  Package,
  CreditCard,
  FileCode,
} from 'lucide-react'
import { invoiceApi } from '@/lib/api'
import type { InvoiceData, InvoiceLineItem, PartyInfo } from '@/types'
import { Alert } from '@/components/Alert'
import { SkeletonDraftItem } from '@/components/ui/Skeleton'

const WIZARD_STEPS = [
  { id: 1, name: 'Grunddaten', icon: FileText },
  { id: 2, name: 'Verkäufer', icon: Building2 },
  { id: 3, name: 'Käufer', icon: User },
  { id: 4, name: 'Positionen', icon: Package },
  { id: 5, name: 'Zahlung', icon: CreditCard },
  { id: 6, name: 'Generieren', icon: FileCode },
]

export function InvoiceCreatorPage() {
  const navigate = useNavigate()
  const { draftId } = useParams<{ draftId: string }>()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  // Fetch drafts list if no draftId
  const { data: draftsData, isLoading: draftsLoading } = useQuery({
    queryKey: ['invoice-drafts'],
    queryFn: invoiceApi.listDrafts,
    enabled: !draftId,
  })

  // Create new draft mutation
  const createDraftMutation = useMutation({
    mutationFn: invoiceApi.createDraft,
    onSuccess: (draft) => {
      navigate(`/rechnung-erstellen/${draft.id}`)
    },
    onError: (err: Error) => {
      setError(err.message || 'Fehler beim Erstellen des Entwurfs')
    },
  })

  // Delete draft mutation
  const deleteDraftMutation = useMutation({
    mutationFn: invoiceApi.deleteDraft,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice-drafts'] })
    },
  })

  if (!draftId) {
    // Show drafts list
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Rechnung erstellen</h1>
            <p className="text-gray-600 mt-1">
              Erstellen Sie XRechnung-konforme Rechnungen
            </p>
          </div>
          <button
            onClick={() => createDraftMutation.mutate({})}
            disabled={createDraftMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            {createDraftMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            Neue Rechnung
          </button>
        </div>

        {error && (
          <Alert variant="error" className="mb-6" onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}

        {draftsLoading ? (
          <div className="card divide-y">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonDraftItem key={i} />
            ))}
          </div>
        ) : draftsData?.drafts.length === 0 ? (
          <div className="card p-12 text-center">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h2 className="text-lg font-medium text-gray-900 mb-2">
              Keine Entwuerfe vorhanden
            </h2>
            <p className="text-gray-600 mb-6">
              Erstellen Sie Ihre erste XRechnung mit unserem Wizard.
            </p>
            <button
              onClick={() => createDraftMutation.mutate({})}
              className="btn-primary"
            >
              Jetzt starten
            </button>
          </div>
        ) : (
          <div className="card divide-y">
            {draftsData?.drafts.map((draft) => (
              <div
                key={draft.id}
                className="p-4 flex items-center justify-between hover:bg-gray-50"
              >
                <button
                  onClick={() => navigate(`/rechnung-erstellen/${draft.id}`)}
                  className="flex items-center gap-4 text-left flex-1"
                >
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <FileText className="h-5 w-5 text-primary-600" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{draft.name}</div>
                    <div className="text-sm text-gray-500">
                      {draft.is_complete ? (
                        <span className="text-success-600">Fertig</span>
                      ) : (
                        `Schritt ${draft.current_step} von 6`
                      )}
                      {' · '}
                      {new Date(draft.updated_at).toLocaleDateString('de-DE')}
                    </div>
                  </div>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (confirm('Entwurf wirklich löschen?')) {
                      deleteDraftMutation.mutate(draft.id)
                    }
                  }}
                  className="p-2 text-gray-400 hover:text-error-600"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Show wizard for specific draft
  return <InvoiceWizard draftId={draftId} />
}

function InvoiceWizard({ draftId }: { draftId: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [generatedXml, setGeneratedXml] = useState<string | null>(null)

  // Fetch draft
  const { data: draft, isLoading } = useQuery({
    queryKey: ['invoice-draft', draftId],
    queryFn: () => invoiceApi.getDraft(draftId),
  })

  const [formData, setFormData] = useState<InvoiceData>({
    currency: 'EUR',
    line_items: [],
  })

  const [currentStep, setCurrentStep] = useState(1)

  // Initialize form data from draft
  useEffect(() => {
    if (draft) {
      setFormData(draft.invoice_data || { currency: 'EUR', line_items: [] })
      setCurrentStep(draft.current_step)
    }
  }, [draft])

  // Update draft mutation
  const updateDraftMutation = useMutation({
    mutationFn: (data: { step: number; invoice_data: InvoiceData }) =>
      invoiceApi.updateDraft(draftId, {
        current_step: data.step,
        invoice_data: data.invoice_data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice-draft', draftId] })
    },
  })

  // Generate invoice mutation
  const generateMutation = useMutation({
    mutationFn: () => invoiceApi.generateInvoice(draftId),
    onSuccess: (result) => {
      setGeneratedXml(result.xml)
      queryClient.invalidateQueries({ queryKey: ['invoice-draft', draftId] })
    },
    onError: (err: Error) => {
      setError(err.message || 'Fehler bei der Generierung')
    },
  })

  const handleNext = () => {
    const nextStep = currentStep + 1
    setCurrentStep(nextStep)
    updateDraftMutation.mutate({ step: nextStep, invoice_data: formData })
  }

  const handleBack = () => {
    const prevStep = currentStep - 1
    setCurrentStep(prevStep)
  }

  const downloadXml = () => {
    if (!generatedXml) return
    const blob = new Blob([generatedXml], { type: 'application/xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${draft?.name || 'rechnung'}.xml`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <button
          onClick={() => navigate('/rechnung-erstellen')}
          className="text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          &larr; Zurück zur Übersicht
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{draft?.name}</h1>
      </div>

      {/* Step indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {WIZARD_STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <button
                onClick={() => setCurrentStep(step.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                  currentStep === step.id
                    ? 'bg-primary-100 text-primary-700'
                    : currentStep > step.id
                    ? 'text-success-600'
                    : 'text-gray-400'
                }`}
              >
                <step.icon className="h-5 w-5" />
                <span className="hidden sm:inline text-sm font-medium">{step.name}</span>
              </button>
              {index < WIZARD_STEPS.length - 1 && (
                <ChevronRight className="h-4 w-4 text-gray-300 mx-1" />
              )}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <Alert variant="error" className="mb-6" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      <div className="card p-6">
        {/* Step 1: Basic info */}
        {currentStep === 1 && (
          <BasicInfoStep formData={formData} setFormData={setFormData} />
        )}

        {/* Step 2: Seller */}
        {currentStep === 2 && (
          <PartyStep
            title="Verkäufer"
            party={formData.seller}
            setParty={(seller) => setFormData({ ...formData, seller })}
          />
        )}

        {/* Step 3: Buyer */}
        {currentStep === 3 && (
          <PartyStep
            title="Käufer"
            party={formData.buyer}
            setParty={(buyer) => setFormData({ ...formData, buyer })}
            showLeitwegId
          />
        )}

        {/* Step 4: Line items */}
        {currentStep === 4 && (
          <LineItemsStep
            items={formData.line_items}
            setItems={(line_items) => setFormData({ ...formData, line_items })}
          />
        )}

        {/* Step 5: Payment */}
        {currentStep === 5 && (
          <PaymentStep formData={formData} setFormData={setFormData} />
        )}

        {/* Step 6: Generate */}
        {currentStep === 6 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Rechnung generieren</h2>

            {generatedXml ? (
              <div className="space-y-4">
                <Alert variant="success">
                  XRechnung wurde erfolgreich generiert!
                </Alert>
                <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                    {generatedXml.slice(0, 2000)}
                    {generatedXml.length > 2000 && '...'}
                  </pre>
                </div>
                <button onClick={downloadXml} className="btn-primary flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  XML herunterladen
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <FileCode className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-600 mb-6">
                  Klicken Sie auf "Generieren", um Ihre XRechnung zu erstellen.
                </p>
                <button
                  onClick={() => generateMutation.mutate()}
                  disabled={generateMutation.isPending}
                  className="btn-primary flex items-center gap-2 mx-auto"
                >
                  {generateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4" />
                  )}
                  XRechnung generieren
                </button>
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className="btn-secondary flex items-center gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Zurück
          </button>
          {currentStep < 6 && (
            <button onClick={handleNext} className="btn-primary flex items-center gap-2">
              Weiter
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// Step components
function BasicInfoStep({
  formData,
  setFormData,
}: {
  formData: InvoiceData
  setFormData: (data: InvoiceData) => void
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Grunddaten</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="label">Rechnungsnummer *</label>
          <input
            type="text"
            value={formData.invoice_number || ''}
            onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
            className="input"
            placeholder="RE-2026-001"
          />
        </div>
        <div>
          <label className="label">Rechnungsdatum *</label>
          <input
            type="date"
            value={formData.invoice_date || ''}
            onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
            className="input"
          />
        </div>
        <div>
          <label className="label">Faelligkeitsdatum</label>
          <input
            type="date"
            value={formData.due_date || ''}
            onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            className="input"
          />
        </div>
        <div>
          <label className="label">Waehrung</label>
          <select
            value={formData.currency}
            onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
            className="input"
          >
            <option value="EUR">EUR - Euro</option>
            <option value="USD">USD - US Dollar</option>
            <option value="CHF">CHF - Schweizer Franken</option>
          </select>
        </div>
      </div>
      <div>
        <label className="label">Notiz / Bemerkung</label>
        <textarea
          value={formData.note || ''}
          onChange={(e) => setFormData({ ...formData, note: e.target.value })}
          className="input"
          rows={3}
          placeholder="Optionale Bemerkung zur Rechnung..."
        />
      </div>
    </div>
  )
}

function PartyStep({
  title,
  party,
  setParty,
  showLeitwegId: _showLeitwegId = false,
}: {
  title: string
  party?: PartyInfo
  setParty: (party: PartyInfo) => void
  showLeitwegId?: boolean
}) {
  const data = party || { name: '' }

  const updateField = (field: string, value: string) => {
    setParty({ ...data, [field]: value })
  }

  const updateAddress = (field: string, value: string) => {
    setParty({
      ...data,
      address: { ...data.address, country: 'DE', [field]: value },
    })
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="label">Name / Firma *</label>
          <input
            type="text"
            value={data.name}
            onChange={(e) => updateField('name', e.target.value)}
            className="input"
            placeholder="Musterfirma GmbH"
          />
        </div>
        <div className="md:col-span-2">
          <label className="label">Straße</label>
          <input
            type="text"
            value={data.address?.street || ''}
            onChange={(e) => updateAddress('street', e.target.value)}
            className="input"
            placeholder="Musterstrasse 123"
          />
        </div>
        <div>
          <label className="label">PLZ</label>
          <input
            type="text"
            value={data.address?.postal_code || ''}
            onChange={(e) => updateAddress('postal_code', e.target.value)}
            className="input"
            placeholder="12345"
          />
        </div>
        <div>
          <label className="label">Stadt</label>
          <input
            type="text"
            value={data.address?.city || ''}
            onChange={(e) => updateAddress('city', e.target.value)}
            className="input"
            placeholder="Berlin"
          />
        </div>
        <div>
          <label className="label">USt-IdNr.</label>
          <input
            type="text"
            value={data.vat_id || ''}
            onChange={(e) => updateField('vat_id', e.target.value)}
            className="input"
            placeholder="DE123456789"
          />
        </div>
        <div>
          <label className="label">Steuernummer</label>
          <input
            type="text"
            value={data.tax_id || ''}
            onChange={(e) => updateField('tax_id', e.target.value)}
            className="input"
            placeholder="12/345/67890"
          />
        </div>
        <div>
          <label className="label">E-Mail</label>
          <input
            type="email"
            value={data.email || ''}
            onChange={(e) => updateField('email', e.target.value)}
            className="input"
            placeholder="kontakt@beispiel.de"
          />
        </div>
        <div>
          <label className="label">Telefon</label>
          <input
            type="tel"
            value={data.phone || ''}
            onChange={(e) => updateField('phone', e.target.value)}
            className="input"
            placeholder="+49 30 12345678"
          />
        </div>
      </div>
    </div>
  )
}

function LineItemsStep({
  items,
  setItems,
}: {
  items: InvoiceLineItem[]
  setItems: (items: InvoiceLineItem[]) => void
}) {
  const addItem = () => {
    setItems([
      ...items,
      {
        id: String(Date.now()),
        description: '',
        quantity: 1,
        unit: 'STK',
        unit_price: 0,
        tax_rate: 19,
        tax_category: 'S',
      },
    ])
  }

  const updateItem = (index: number, field: string, value: string | number) => {
    const updated = [...items]
    updated[index] = { ...updated[index], [field]: value }
    setItems(updated)
  }

  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index))
  }

  const total = items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Rechnungspositionen</h2>
        <button onClick={addItem} className="btn-secondary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Position hinzufuegen
        </button>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Package className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>Noch keine Positionen vorhanden.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item, index) => (
            <div key={item.id || index} className="p-4 bg-gray-50 rounded-lg space-y-3">
              <div className="flex items-start justify-between">
                <span className="text-sm font-medium text-gray-500">Position {index + 1}</span>
                <button
                  onClick={() => removeItem(index)}
                  className="text-gray-400 hover:text-error-600"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="md:col-span-4">
                  <input
                    type="text"
                    value={item.description}
                    onChange={(e) => updateItem(index, 'description', e.target.value)}
                    className="input"
                    placeholder="Beschreibung"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Menge</label>
                  <input
                    type="number"
                    value={item.quantity}
                    onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value) || 0)}
                    className="input"
                    min="0"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Einheit</label>
                  <select
                    value={item.unit}
                    onChange={(e) => updateItem(index, 'unit', e.target.value)}
                    className="input"
                  >
                    <option value="STK">Stueck</option>
                    <option value="H">Stunde</option>
                    <option value="DAY">Tag</option>
                    <option value="KGM">Kilogramm</option>
                    <option value="MTR">Meter</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Einzelpreis</label>
                  <input
                    type="number"
                    value={item.unit_price}
                    onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                    className="input"
                    min="0"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">MwSt %</label>
                  <select
                    value={item.tax_rate}
                    onChange={(e) => updateItem(index, 'tax_rate', parseFloat(e.target.value))}
                    className="input"
                  >
                    <option value="19">19%</option>
                    <option value="7">7%</option>
                    <option value="0">0%</option>
                  </select>
                </div>
              </div>
              <div className="text-right text-sm">
                <span className="text-gray-500">Summe: </span>
                <span className="font-medium">
                  {(item.quantity * item.unit_price).toFixed(2)} EUR
                </span>
              </div>
            </div>
          ))}

          <div className="text-right pt-4 border-t">
            <span className="text-gray-500">Gesamtsumme netto: </span>
            <span className="text-xl font-bold">{total.toFixed(2)} EUR</span>
          </div>
        </div>
      )}
    </div>
  )
}

function PaymentStep({
  formData,
  setFormData,
}: {
  formData: InvoiceData
  setFormData: (data: InvoiceData) => void
}) {
  const payment = formData.payment || { payment_means_code: '58' }
  const references = formData.references || {}

  const updatePayment = (field: string, value: string) => {
    setFormData({
      ...formData,
      payment: { ...payment, [field]: value },
    })
  }

  const updateReferences = (field: string, value: string) => {
    setFormData({
      ...formData,
      references: { ...references, [field]: value },
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">Zahlungsinformationen</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="label">IBAN</label>
            <input
              type="text"
              value={payment.iban || ''}
              onChange={(e) => updatePayment('iban', e.target.value)}
              className="input"
              placeholder="DE89 3704 0044 0532 0130 00"
            />
          </div>
          <div>
            <label className="label">BIC</label>
            <input
              type="text"
              value={payment.bic || ''}
              onChange={(e) => updatePayment('bic', e.target.value)}
              className="input"
              placeholder="COBADEFFXXX"
            />
          </div>
          <div>
            <label className="label">Bank</label>
            <input
              type="text"
              value={payment.bank_name || ''}
              onChange={(e) => updatePayment('bank_name', e.target.value)}
              className="input"
              placeholder="Commerzbank AG"
            />
          </div>
          <div className="md:col-span-2">
            <label className="label">Zahlungsbedingungen</label>
            <input
              type="text"
              value={payment.payment_terms || ''}
              onChange={(e) => updatePayment('payment_terms', e.target.value)}
              className="input"
              placeholder="Zahlbar innerhalb von 14 Tagen ohne Abzug"
            />
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Referenzen</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Leitweg-ID (für öffentliche Auftraggeber)</label>
            <input
              type="text"
              value={references.buyer_reference || ''}
              onChange={(e) => updateReferences('buyer_reference', e.target.value)}
              className="input"
              placeholder="04011000-1234512345-12"
            />
          </div>
          <div>
            <label className="label">Bestellnummer</label>
            <input
              type="text"
              value={references.order_reference || ''}
              onChange={(e) => updateReferences('order_reference', e.target.value)}
              className="input"
              placeholder="PO-2026-001"
            />
          </div>
          <div>
            <label className="label">Vertragsnummer</label>
            <input
              type="text"
              value={references.contract_reference || ''}
              onChange={(e) => updateReferences('contract_reference', e.target.value)}
              className="input"
              placeholder="V-2026-001"
            />
          </div>
          <div>
            <label className="label">Projektnummer</label>
            <input
              type="text"
              value={references.project_reference || ''}
              onChange={(e) => updateReferences('project_reference', e.target.value)}
              className="input"
              placeholder="P-2026-001"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default InvoiceCreatorPage
