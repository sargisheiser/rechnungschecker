import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FileUp,
  ArrowRight,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  FileText,
  Building2,
  User,
  CreditCard,
  Hash,
  AlertTriangle,
  RefreshCw,
  X,
  Info,
  Eye,
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { useUser } from '@/hooks/useAuth'
import { useUsage } from '@/hooks/useBilling'
import {
  useConversionStatus,
  usePreviewExtraction,
  useConvert,
  useDownloadConversion,
} from '@/hooks/useConversion'
import { cn } from '@/lib/utils'
import type { ExtractedData, OutputFormat, ZUGFeRDProfileType } from '@/types'

type ConversionStep = 'upload' | 'preview' | 'result'

// Helper to format amount values that can be string or number from backend
function formatAmount(value: string | number | undefined | null): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'number') return value.toFixed(2)
  // Already a string, try to format it
  const num = parseFloat(value)
  return isNaN(num) ? value : num.toFixed(2)
}

export function ConversionPage() {
  useUser() // Ensure user is loaded
  const { data: usage } = useUsage()
  const { data: status } = useConversionStatus()

  const [step, setStep] = useState<ConversionStep>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null)
  const [ocrUsed, setOcrUsed] = useState(false)
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('xrechnung')
  const [zugferdProfile, setZugferdProfile] = useState<ZUGFeRDProfileType>('EN16931')
  const [embedInPdf, setEmbedInPdf] = useState(true)
  const [conversionResult, setConversionResult] = useState<{
    conversionId: string
    filename: string
    warnings: string[]
  } | null>(null)

  // Overrides
  const [overrides, setOverrides] = useState<{
    invoice_number?: string
    seller_vat_id?: string
    buyer_reference?: string
    leitweg_id?: string
  }>({})

  const preview = usePreviewExtraction()
  const convert = useConvert()
  const download = useDownloadConversion()

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const pdfFile = acceptedFiles[0]
      if (!pdfFile) return

      setFile(pdfFile)
      setStep('preview')

      try {
        const result = await preview.mutateAsync(pdfFile)
        setExtractedData(result.extracted_data)
        setOcrUsed(result.ocr_used)
      } catch {
        // Error handled by mutation
      }
    },
    [preview]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  })

  const handleConvert = async () => {
    if (!file) return

    try {
      const result = await convert.mutateAsync({
        file,
        outputFormat,
        zugferdProfile,
        embedInPdf,
        overrides: Object.keys(overrides).length > 0 ? overrides : undefined,
      })

      if (result.success) {
        setConversionResult({
          conversionId: result.conversion_id,
          filename: result.filename,
          warnings: result.warnings,
        })
        setStep('result')
      }
    } catch {
      // Error handled by mutation
    }
  }

  const handleDownload = () => {
    if (!conversionResult) return
    download.mutate({
      conversionId: conversionResult.conversionId,
      filename: conversionResult.filename,
    })
  }

  const handleReset = () => {
    setStep('upload')
    setFile(null)
    setExtractedData(null)
    setOcrUsed(false)
    setConversionResult(null)
    setOverrides({})
    preview.reset()
    convert.reset()
  }

  // Check if user has reached conversion limit
  const isLimitReached = usage && usage.conversions_limit !== null && usage.conversions_used >= usage.conversions_limit

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">PDF Konvertierung</h1>
        <p className="text-gray-600 mt-1">
          Konvertieren Sie PDF-Rechnungen in XRechnung oder ZUGFeRD Format
        </p>
      </div>

      {/* Usage info */}
      {usage && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-gray-400" />
            <span className="text-sm text-gray-600">
              Konvertierungen diesen Monat:{' '}
              <span className="font-medium text-gray-900">
                {usage.conversions_used}
                {usage.conversions_limit !== null && ` / ${usage.conversions_limit}`}
              </span>
            </span>
          </div>
          {isLimitReached && (
            <Link to="/preise" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              Limit erhoeht? Jetzt upgraden
            </Link>
          )}
        </div>
      )}

      {/* OCR Status */}
      {status && (
        <div className={cn(
          'mb-6 p-3 rounded-lg flex items-center gap-2 text-sm',
          status.ocr_available ? 'bg-success-50 text-success-700' : 'bg-warning-50 text-warning-700'
        )}>
          <Info className="h-4 w-4" />
          {status.ocr_available
            ? 'OCR ist verfuegbar - auch gescannte PDFs koennen verarbeitet werden'
            : 'OCR nicht verfuegbar - nur digitale PDFs werden unterstuetzt'}
        </div>
      )}

      {/* Step indicator */}
      <div className="mb-8">
        <div className="flex items-center">
          <StepIndicator step={1} currentStep={step === 'upload' ? 1 : step === 'preview' ? 2 : 3} label="Upload" />
          <div className="flex-1 h-1 bg-gray-200 mx-2">
            <div className={cn('h-full bg-primary-500 transition-all', step !== 'upload' ? 'w-full' : 'w-0')} />
          </div>
          <StepIndicator step={2} currentStep={step === 'upload' ? 1 : step === 'preview' ? 2 : 3} label="Vorschau" />
          <div className="flex-1 h-1 bg-gray-200 mx-2">
            <div className={cn('h-full bg-primary-500 transition-all', step === 'result' ? 'w-full' : 'w-0')} />
          </div>
          <StepIndicator step={3} currentStep={step === 'upload' ? 1 : step === 'preview' ? 2 : 3} label="Download" />
        </div>
      </div>

      {/* Upload Step */}
      {step === 'upload' && (
        <div className="card p-8">
          {isLimitReached ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-warning-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Konvertierungslimit erreicht</h3>
              <p className="text-gray-600 mb-4">
                Sie haben Ihr monatliches Limit von {usage?.conversions_limit} Konvertierungen erreicht.
              </p>
              <Link to="/preise" className="btn-primary">
                Jetzt upgraden
              </Link>
            </div>
          ) : (
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors',
                isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
              )}
            >
              <input {...getInputProps()} />
              <FileUp className={cn('h-12 w-12 mx-auto mb-4', isDragActive ? 'text-primary-500' : 'text-gray-400')} />
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'PDF hier ablegen' : 'PDF-Rechnung hochladen'}
              </p>
              <p className="text-sm text-gray-500">
                Ziehen Sie eine PDF-Datei hierher oder klicken Sie zum Auswaehlen
              </p>
              <p className="text-xs text-gray-400 mt-2">Maximale Dateigroesse: 10 MB</p>
            </div>
          )}
        </div>
      )}

      {/* Preview Step */}
      {step === 'preview' && (
        <div className="space-y-6">
          {preview.isPending ? (
            <div className="card p-12 text-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary-500 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900">Daten werden extrahiert...</p>
              <p className="text-sm text-gray-500 mt-1">
                {ocrUsed ? 'OCR wird verwendet (kann etwas laenger dauern)' : 'Analysiere PDF...'}
              </p>
            </div>
          ) : preview.isError ? (
            <div className="card p-8 text-center">
              <AlertCircle className="h-12 w-12 text-error-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Fehler bei der Extraktion</h3>
              <p className="text-gray-600 mb-4">
                Die Daten konnten nicht aus der PDF extrahiert werden.
              </p>
              <button onClick={handleReset} className="btn-secondary">
                <RefreshCw className="h-4 w-4 mr-2" />
                Erneut versuchen
              </button>
            </div>
          ) : extractedData ? (
            <>
              {/* File info */}
              <div className="card p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-primary-500" />
                  <div>
                    <p className="font-medium text-gray-900">{file?.name}</p>
                    <p className="text-sm text-gray-500">
                      {((file?.size || 0) / 1024).toFixed(1)} KB
                      {ocrUsed && ' • OCR verwendet'}
                    </p>
                  </div>
                </div>
                <button onClick={handleReset} className="text-gray-400 hover:text-gray-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Warnings */}
              {extractedData.warnings.length > 0 && (
                <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-warning-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-warning-800">Hinweise zur Extraktion</h4>
                      <ul className="mt-1 text-sm text-warning-700 list-disc list-inside">
                        {extractedData.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Confidence indicator */}
              <div className="card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Erkennungsqualitaet</span>
                  <span className={cn(
                    'text-sm font-medium',
                    extractedData.confidence >= 0.8 ? 'text-success-600' :
                    extractedData.confidence >= 0.5 ? 'text-warning-600' : 'text-error-600'
                  )}>
                    {Math.round(extractedData.confidence * 100)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full',
                      extractedData.confidence >= 0.8 ? 'bg-success-500' :
                      extractedData.confidence >= 0.5 ? 'bg-warning-500' : 'bg-error-500'
                    )}
                    style={{ width: `${extractedData.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* Extracted Data Display */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Invoice Details */}
                <div className="card p-6">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
                    <Hash className="h-4 w-4 text-gray-400" />
                    Rechnungsdaten
                  </h3>
                  <div className="space-y-3">
                    <DataField
                      label="Rechnungsnummer"
                      value={extractedData.invoice_number}
                      editable
                      onChange={(v) => setOverrides({ ...overrides, invoice_number: v })}
                      override={overrides.invoice_number}
                    />
                    <DataField label="Rechnungsdatum" value={extractedData.invoice_date} />
                    <DataField label="Faelligkeitsdatum" value={extractedData.due_date} />
                    <DataField label="Lieferdatum" value={extractedData.delivery_date} />
                  </div>
                </div>

                {/* Amounts */}
                <div className="card p-6">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-gray-400" />
                    Betraege
                  </h3>
                  <div className="space-y-3">
                    <DataField
                      label="Nettobetrag"
                      value={formatAmount(extractedData.net_amount)}
                      suffix={extractedData.currency}
                    />
                    <DataField
                      label="MwSt."
                      value={formatAmount(extractedData.vat_amount)}
                      suffix={extractedData.currency}
                    />
                    <DataField
                      label="Bruttobetrag"
                      value={formatAmount(extractedData.gross_amount)}
                      suffix={extractedData.currency}
                      highlight
                    />
                  </div>
                </div>

                {/* Seller */}
                <div className="card p-6">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-gray-400" />
                    Verkaeufer
                  </h3>
                  <div className="space-y-3">
                    <DataField label="Name" value={extractedData.seller_name} />
                    <DataField label="Strasse" value={extractedData.seller_street} />
                    <DataField
                      label="PLZ / Ort"
                      value={
                        extractedData.seller_postal_code || extractedData.seller_city
                          ? `${extractedData.seller_postal_code || ''} ${extractedData.seller_city || ''}`.trim()
                          : undefined
                      }
                    />
                    <DataField
                      label="USt-IdNr."
                      value={extractedData.seller_vat_id}
                      editable
                      onChange={(v) => setOverrides({ ...overrides, seller_vat_id: v })}
                      override={overrides.seller_vat_id}
                    />
                  </div>
                </div>

                {/* Buyer */}
                <div className="card p-6">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-400" />
                    Kaeufer
                  </h3>
                  <div className="space-y-3">
                    <DataField label="Name" value={extractedData.buyer_name} />
                    <DataField label="Strasse" value={extractedData.buyer_street} />
                    <DataField
                      label="PLZ / Ort"
                      value={
                        extractedData.buyer_postal_code || extractedData.buyer_city
                          ? `${extractedData.buyer_postal_code || ''} ${extractedData.buyer_city || ''}`.trim()
                          : undefined
                      }
                    />
                    <DataField
                      label="Leitweg-ID"
                      value={extractedData.leitweg_id}
                      editable
                      onChange={(v) => setOverrides({ ...overrides, leitweg_id: v })}
                      override={overrides.leitweg_id}
                    />
                    <DataField
                      label="Kaeuferreferenz"
                      value={extractedData.buyer_reference}
                      editable
                      onChange={(v) => setOverrides({ ...overrides, buyer_reference: v })}
                      override={overrides.buyer_reference}
                    />
                  </div>
                </div>
              </div>

              {/* Output Options */}
              <div className="card p-6">
                <h3 className="font-medium text-gray-900 mb-4">Ausgabeformat</h3>
                <div className="grid sm:grid-cols-2 gap-4 mb-4">
                  <label
                    className={cn(
                      'flex items-center gap-3 p-4 border rounded-lg cursor-pointer transition-colors',
                      outputFormat === 'xrechnung'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <input
                      type="radio"
                      name="format"
                      value="xrechnung"
                      checked={outputFormat === 'xrechnung'}
                      onChange={() => setOutputFormat('xrechnung')}
                      className="text-primary-600"
                    />
                    <div>
                      <p className="font-medium text-gray-900">XRechnung</p>
                      <p className="text-sm text-gray-500">
                        Fuer oeffentliche Auftraggeber in Deutschland
                      </p>
                    </div>
                  </label>
                  <label
                    className={cn(
                      'flex items-center gap-3 p-4 border rounded-lg cursor-pointer transition-colors',
                      outputFormat === 'zugferd'
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <input
                      type="radio"
                      name="format"
                      value="zugferd"
                      checked={outputFormat === 'zugferd'}
                      onChange={() => setOutputFormat('zugferd')}
                      className="text-primary-600"
                    />
                    <div>
                      <p className="font-medium text-gray-900">ZUGFeRD / Factur-X</p>
                      <p className="text-sm text-gray-500">
                        Hybridformat mit eingebettetem XML
                      </p>
                    </div>
                  </label>
                </div>

                {outputFormat === 'zugferd' && (
                  <div className="space-y-4 pt-4 border-t">
                    <div>
                      <label className="label">ZUGFeRD Profil</label>
                      <select
                        value={zugferdProfile}
                        onChange={(e) => setZugferdProfile(e.target.value as ZUGFeRDProfileType)}
                        className="input"
                      >
                        <option value="MINIMUM">MINIMUM - Basisinformationen</option>
                        <option value="BASIC">BASIC - Grunddaten</option>
                        <option value="EN16931">EN16931 - Standard (empfohlen)</option>
                        <option value="EXTENDED">EXTENDED - Erweitert</option>
                      </select>
                    </div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={embedInPdf}
                        onChange={(e) => setEmbedInPdf(e.target.checked)}
                        className="rounded text-primary-600"
                      />
                      <span className="text-sm text-gray-700">XML in PDF einbetten (PDF/A-3)</span>
                    </label>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between">
                <button onClick={handleReset} className="btn-secondary">
                  <X className="h-4 w-4 mr-2" />
                  Abbrechen
                </button>
                <button
                  onClick={handleConvert}
                  disabled={convert.isPending}
                  className="btn-primary"
                >
                  {convert.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Konvertiere...
                    </>
                  ) : (
                    <>
                      Konvertieren
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </button>
              </div>

              {convert.isError && (
                <div className="flex items-center gap-2 p-4 bg-error-50 rounded-lg text-error-600">
                  <AlertCircle className="h-5 w-5 flex-shrink-0" />
                  <span>Konvertierung fehlgeschlagen. Bitte versuchen Sie es erneut.</span>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}

      {/* Result Step */}
      {step === 'result' && conversionResult && (
        <div className="card p-8 text-center">
          <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="h-8 w-8 text-success-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Konvertierung erfolgreich!</h2>
          <p className="text-gray-600 mb-6">
            Ihre Rechnung wurde erfolgreich in das {outputFormat === 'xrechnung' ? 'XRechnung' : 'ZUGFeRD'} Format konvertiert.
          </p>

          {conversionResult.warnings.length > 0 && (
            <div className="bg-warning-50 border border-warning-200 rounded-lg p-4 mb-6 text-left">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-warning-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-warning-800">Hinweise</h4>
                  <ul className="mt-1 text-sm text-warning-700 list-disc list-inside">
                    {conversionResult.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-center gap-3">
              <FileText className="h-8 w-8 text-primary-500" />
              <div className="text-left">
                <p className="font-medium text-gray-900">{conversionResult.filename}</p>
                <p className="text-sm text-gray-500">
                  {outputFormat === 'zugferd' && embedInPdf ? 'PDF mit eingebettetem XML' : 'XML-Datei'}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-4">
            <button onClick={handleReset} className="btn-secondary">
              <RefreshCw className="h-4 w-4 mr-2" />
              Weitere Konvertierung
            </button>
            <button
              onClick={handleDownload}
              disabled={download.isPending}
              className="btn-primary"
            >
              {download.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Wird heruntergeladen...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Herunterladen
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function StepIndicator({
  step,
  currentStep,
  label,
}: {
  step: number
  currentStep: number
  label: string
}) {
  const isActive = currentStep >= step
  const isCurrent = currentStep === step

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
          isActive ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-500'
        )}
      >
        {step}
      </div>
      <span
        className={cn(
          'text-sm font-medium hidden sm:block',
          isCurrent ? 'text-gray-900' : isActive ? 'text-gray-600' : 'text-gray-400'
        )}
      >
        {label}
      </span>
    </div>
  )
}

function DataField({
  label,
  value,
  suffix,
  highlight,
  editable,
  onChange,
  override,
}: {
  label: string
  value?: string | null
  suffix?: string
  highlight?: boolean
  editable?: boolean
  onChange?: (value: string) => void
  override?: string
}) {
  const [isEditing, setIsEditing] = useState(false)
  const displayValue = override || value

  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-500">{label}</span>
      <div className="flex items-center gap-2">
        {isEditing ? (
          <input
            type="text"
            value={override || value || ''}
            onChange={(e) => onChange?.(e.target.value)}
            onBlur={() => setIsEditing(false)}
            onKeyDown={(e) => e.key === 'Enter' && setIsEditing(false)}
            className="input py-1 px-2 text-sm w-40"
            autoFocus
          />
        ) : (
          <>
            <span
              className={cn(
                'text-sm',
                highlight ? 'font-semibold text-gray-900' : 'text-gray-700',
                !displayValue && 'text-gray-400 italic'
              )}
            >
              {displayValue || 'Nicht erkannt'}
              {suffix && displayValue && ` ${suffix}`}
            </span>
            {editable && (
              <button
                onClick={() => setIsEditing(true)}
                className="text-gray-400 hover:text-primary-500"
                title="Bearbeiten"
              >
                <Eye className="h-3.5 w-3.5" />
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
