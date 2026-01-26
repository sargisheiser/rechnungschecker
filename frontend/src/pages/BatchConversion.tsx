import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  FileUp,
  X,
  CheckCircle,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Loader2,
  FileText,
  Download,
  RefreshCw,
  ShieldCheck,
  ShieldX,
  FolderUp,
} from 'lucide-react'
import { useUser } from '@/hooks/useAuth'
import { useUsage } from '@/hooks/useBilling'
import { useConversionStatus, useBatchConvert, useDownloadConversion } from '@/hooks/useConversion'
import { cn } from '@/lib/utils'
import type { OutputFormat, ZUGFeRDProfileType, ConversionResponse } from '@/types'

const MAX_FILES = 10

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function BatchConversionPage() {
  const { data: user } = useUser()
  const { data: usage } = useUsage()
  useConversionStatus() // Preload status for cache

  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('xrechnung')
  const [zugferdProfile, setZugferdProfile] = useState<ZUGFeRDProfileType>('EN16931')
  const [results, setResults] = useState<ConversionResponse[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const batchConvert = useBatchConvert()
  const download = useDownloadConversion()

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const pdfFiles = acceptedFiles.filter((f) => f.name.toLowerCase().endsWith('.pdf'))
      const newFiles = [...selectedFiles, ...pdfFiles].slice(0, MAX_FILES)
      setSelectedFiles(newFiles)
    },
    [selectedFiles]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: MAX_FILES,
    maxSize: 10 * 1024 * 1024, // 10MB
  })

  const removeFile = (index: number) => {
    setSelectedFiles((files) => files.filter((_, i) => i !== index))
  }

  const handleConvert = async () => {
    if (selectedFiles.length === 0) return

    try {
      setError(null)
      const response = await batchConvert.mutateAsync({
        files: selectedFiles,
        outputFormat,
        zugferdProfile,
      })
      setResults(response)
    } catch (err) {
      setError('Batch-Konvertierung fehlgeschlagen. Bitte versuchen Sie es erneut.')
    }
  }

  const handleDownload = (conversionId: string, filename: string) => {
    download.mutate({ conversionId, filename })
  }

  const handleReset = () => {
    setSelectedFiles([])
    setResults(null)
    batchConvert.reset()
  }

  // Check if user plan allows batch conversion
  const isPlanAllowed = user && user.plan !== 'free'
  const successCount = results?.filter((r) => r.success).length || 0
  const failedCount = results?.filter((r) => !r.success).length || 0

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FolderUp className="h-7 w-7 text-primary-600" />
          Batch PDF Konvertierung
        </h1>
        <p className="text-gray-600 mt-1">
          Konvertieren Sie mehrere PDF-Rechnungen gleichzeitig in XRechnung oder ZUGFeRD Format
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
        </div>
      )}

      {/* Plan restriction notice */}
      {!isPlanAllowed && (
        <div className="mb-6 bg-warning-50 border border-warning-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-warning-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-warning-800">Starter-Plan erforderlich</h4>
              <p className="text-sm text-warning-700 mt-1">
                Die Batch-Konvertierung ist ab dem Starter-Plan verfügbar.
              </p>
              <Link to="/preise" className="text-sm text-primary-600 hover:text-primary-700 font-medium mt-2 inline-block">
                Jetzt wechseln
              </Link>
            </div>
          </div>
        </div>
      )}

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

      {/* Results View */}
      {results ? (
        <div className="space-y-6">
          {/* Summary */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Ergebnisse</h2>
              <button onClick={handleReset} className="btn-secondary text-sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Neue Konvertierung
              </button>
            </div>

            <div className="flex items-center gap-6 mb-6">
              <div className="flex items-center gap-2 text-success-600">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">{successCount} erfolgreich</span>
              </div>
              {failedCount > 0 && (
                <div className="flex items-center gap-2 text-error-600">
                  <XCircle className="h-5 w-5" />
                  <span className="font-medium">{failedCount} fehlgeschlagen</span>
                </div>
              )}
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Datei
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Validierung
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Aktion
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.map((result, index) => (
                    <tr key={index}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-900">{result.filename}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {result.success ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-700">
                            <CheckCircle className="h-3 w-3" />
                            Erfolgreich
                          </span>
                        ) : (
                          <div>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-error-100 text-error-700">
                              <XCircle className="h-3 w-3" />
                              Fehler
                            </span>
                            {result.error && (
                              <p className="text-xs text-error-600 mt-1">{result.error}</p>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {result.success && result.validation_result ? (
                          result.validation_result.is_valid ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-700">
                              <ShieldCheck className="h-3 w-3" />
                              Gueltig
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-error-100 text-error-700">
                              <ShieldX className="h-3 w-3" />
                              {result.validation_result.error_count} Fehler
                            </span>
                          )
                        ) : result.success && result.validation_result === undefined ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-warning-100 text-warning-700">
                            <AlertTriangle className="h-3 w-3" />
                            Nicht validiert
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {result.success && result.conversion_id && (
                          <button
                            onClick={() => handleDownload(result.conversion_id, result.filename)}
                            disabled={download.isPending}
                            className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                          >
                            <Download className="h-4 w-4" />
                            Download
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Upload View */
        <div className="space-y-6">
          <div className="card p-6">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors',
                isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400',
                !isPlanAllowed && 'opacity-50 cursor-not-allowed'
              )}
            >
              <input {...getInputProps()} disabled={!isPlanAllowed} />
              <FileUp className={cn('h-12 w-12 mx-auto mb-4', isDragActive ? 'text-primary-500' : 'text-gray-400')} />
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'PDFs hier ablegen' : 'PDF-Rechnungen hochladen'}
              </p>
              <p className="text-sm text-gray-500">
                Ziehen Sie PDF-Dateien hierher oder klicken Sie zum Auswaehlen
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Maximal {MAX_FILES} Dateien, je 10 MB
              </p>
            </div>

            {/* Selected Files List */}
            {selectedFiles.length > 0 && (
              <div className="mt-6">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-sm font-medium text-gray-700">
                    Ausgewaehlte Dateien ({selectedFiles.length})
                  </span>
                  <button
                    onClick={() => setSelectedFiles([])}
                    className="text-sm text-error-600 hover:text-error-700"
                  >
                    Alle entfernen
                  </button>
                </div>
                <div className="max-h-48 overflow-y-auto space-y-2">
                  {selectedFiles.map((file, index) => (
                    <div
                      key={`${file.name}-${index}`}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="text-sm text-gray-700 truncate">{file.name}</span>
                        <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                      </div>
                      <button onClick={() => removeFile(index)} className="p-1 text-gray-400 hover:text-error-500">
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Output Options */}
          {selectedFiles.length > 0 && (
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
                    <p className="text-sm text-gray-500">Fuer oeffentliche Auftraggeber</p>
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
                    <p className="text-sm text-gray-500">Hybridformat mit XML</p>
                  </div>
                </label>
              </div>

              {outputFormat === 'zugferd' && (
                <div className="pt-4 border-t">
                  <label className="label">ZUGFeRD Profil</label>
                  <select
                    value={zugferdProfile}
                    onChange={(e) => setZugferdProfile(e.target.value as ZUGFeRDProfileType)}
                    className="input max-w-xs"
                  >
                    <option value="MINIMUM">MINIMUM - Basisinformationen</option>
                    <option value="BASIC">BASIC - Grunddaten</option>
                    <option value="EN16931">EN16931 - Standard (empfohlen)</option>
                    <option value="EXTENDED">EXTENDED - Erweitert</option>
                  </select>
                </div>
              )}
            </div>
          )}

          {/* Convert Button */}
          {selectedFiles.length > 0 && (
            <div className="flex justify-end">
              <button
                onClick={handleConvert}
                disabled={!isPlanAllowed || batchConvert.isPending}
                className={cn(
                  'btn-primary px-8',
                  (!isPlanAllowed || batchConvert.isPending) && 'opacity-50 cursor-not-allowed'
                )}
              >
                {batchConvert.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Konvertiere {selectedFiles.length} Dateien...
                  </>
                ) : (
                  <>
                    <FileUp className="h-4 w-4 mr-2" />
                    Alle konvertieren ({selectedFiles.length})
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Display */}
          {batchConvert.isError && (
            <div className="flex items-center gap-2 p-4 bg-error-50 rounded-lg text-error-600">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <span>Batch-Konvertierung fehlgeschlagen. Bitte versuchen Sie es erneut.</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default BatchConversionPage
