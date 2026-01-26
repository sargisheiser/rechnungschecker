import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  FileText,
  Clock,
  Hash,
  Download,
  Save,
  Loader2,
  AlertTriangle,
  Info,
} from 'lucide-react'
import { validationApi } from '@/lib/api'
import { cn, formatDateTime } from '@/lib/utils'
import { useDownloadReport } from '@/hooks/useValidation'
import type { ValidationDetail } from '@/types'

export function ValidationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState('')
  const [hasChanges, setHasChanges] = useState(false)
  const downloadReport = useDownloadReport()

  const { data: validation, isLoading, error } = useQuery<ValidationDetail>({
    queryKey: ['validation-detail', id],
    queryFn: () => validationApi.getValidationDetail(id!),
    enabled: !!id,
  })

  const updateNotes = useMutation({
    mutationFn: (newNotes: string | null) => validationApi.updateNotes(id!, newNotes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['validation-detail', id] })
      setHasChanges(false)
    },
  })

  useEffect(() => {
    if (validation?.notes !== undefined) {
      setNotes(validation.notes || '')
    }
  }, [validation?.notes])

  const handleNotesChange = (value: string) => {
    setNotes(value)
    setHasChanges(value !== (validation?.notes || ''))
  }

  const handleSaveNotes = () => {
    updateNotes.mutate(notes || null)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error || !validation) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <XCircle className="h-12 w-12 text-error-500 mx-auto mb-4" />
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Validierung nicht gefunden
            </h1>
            <p className="text-gray-600 mb-4">
              Die angeforderte Validierung existiert nicht oder Sie haben keinen Zugriff.
            </p>
            <Link to="/dashboard" className="btn-primary">
              Zurück zum Dashboard
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const isValid = validation.is_valid

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            to="/dashboard"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Zurück zum Dashboard
          </Link>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {validation.file_name || 'Unbekannte Datei'}
              </h1>
              <p className="text-gray-600 mt-1">
                Validiert am {formatDateTime(validation.validated_at)}
              </p>
            </div>
            <button
              onClick={() => downloadReport.mutate(validation.id)}
              disabled={downloadReport.isPending}
              className="btn-secondary"
            >
              {downloadReport.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              PDF Bericht
            </button>
          </div>
        </div>

        <div className="grid gap-6">
          {/* Status Card */}
          <div
            className={cn(
              'rounded-xl p-6',
              isValid ? 'bg-success-50 border border-success-200' : 'bg-error-50 border border-error-200'
            )}
          >
            <div className="flex items-center gap-4">
              {isValid ? (
                <CheckCircle className="h-12 w-12 text-success-600" />
              ) : (
                <XCircle className="h-12 w-12 text-error-600" />
              )}
              <div>
                <h2 className={cn('text-2xl font-bold', isValid ? 'text-success-700' : 'text-error-700')}>
                  {isValid ? 'Gueltig' : 'Ungueltig'}
                </h2>
                <p className={cn('text-sm', isValid ? 'text-success-600' : 'text-error-600')}>
                  {validation.error_count} Fehler, {validation.warning_count} Warnungen, {validation.info_count} Hinweise
                </p>
              </div>
            </div>
          </div>

          {/* Details Card */}
          <div className="bg-white rounded-xl shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Details</h3>
            </div>
            <div className="p-6">
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <dt className="text-sm text-gray-500 flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Dateityp
                  </dt>
                  <dd className="text-sm font-medium text-gray-900 mt-1">
                    {validation.file_type === 'xrechnung' ? 'XRechnung' : 'ZUGFeRD'}
                    {validation.xrechnung_version && ` (v${validation.xrechnung_version})`}
                    {validation.zugferd_profile && ` (${validation.zugferd_profile})`}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Verarbeitungszeit
                  </dt>
                  <dd className="text-sm font-medium text-gray-900 mt-1">
                    {validation.processing_time_ms} ms
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500 flex items-center gap-2">
                    <Hash className="h-4 w-4" />
                    Datei-Hash (SHA256)
                  </dt>
                  <dd className="text-sm font-mono text-gray-900 mt-1 break-all">
                    {validation.file_hash}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Validator Version</dt>
                  <dd className="text-sm font-medium text-gray-900 mt-1">
                    KoSIT {validation.validator_version}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Summary Card */}
          <div className="bg-white rounded-xl shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Zusammenfassung</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-3 gap-4">
                <div className={cn('p-4 rounded-lg', validation.error_count > 0 ? 'bg-error-50' : 'bg-gray-50')}>
                  <div className="flex items-center gap-2 mb-1">
                    <XCircle className={cn('h-5 w-5', validation.error_count > 0 ? 'text-error-500' : 'text-gray-400')} />
                    <span className="text-sm font-medium text-gray-700">Fehler</span>
                  </div>
                  <p className={cn('text-2xl font-bold', validation.error_count > 0 ? 'text-error-600' : 'text-gray-900')}>
                    {validation.error_count}
                  </p>
                </div>
                <div className={cn('p-4 rounded-lg', validation.warning_count > 0 ? 'bg-warning-50' : 'bg-gray-50')}>
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className={cn('h-5 w-5', validation.warning_count > 0 ? 'text-warning-500' : 'text-gray-400')} />
                    <span className="text-sm font-medium text-gray-700">Warnungen</span>
                  </div>
                  <p className={cn('text-2xl font-bold', validation.warning_count > 0 ? 'text-warning-600' : 'text-gray-900')}>
                    {validation.warning_count}
                  </p>
                </div>
                <div className={cn('p-4 rounded-lg', validation.info_count > 0 ? 'bg-primary-50' : 'bg-gray-50')}>
                  <div className="flex items-center gap-2 mb-1">
                    <Info className={cn('h-5 w-5', validation.info_count > 0 ? 'text-primary-500' : 'text-gray-400')} />
                    <span className="text-sm font-medium text-gray-700">Hinweise</span>
                  </div>
                  <p className={cn('text-2xl font-bold', validation.info_count > 0 ? 'text-primary-600' : 'text-gray-900')}>
                    {validation.info_count}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Notes Card */}
          <div className="bg-white rounded-xl shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Notizen</h3>
              {hasChanges && (
                <button
                  onClick={handleSaveNotes}
                  disabled={updateNotes.isPending}
                  className="btn-primary btn-sm"
                >
                  {updateNotes.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  ) : (
                    <Save className="h-4 w-4 mr-1" />
                  )}
                  Speichern
                </button>
              )}
            </div>
            <div className="p-6">
              <textarea
                value={notes}
                onChange={(e) => handleNotesChange(e.target.value)}
                placeholder="Fuegen Sie hier Ihre Notizen zu dieser Validierung hinzu..."
                rows={5}
                maxLength={2000}
                className="input w-full resize-none"
              />
              <p className="text-xs text-gray-500 mt-2 text-right">
                {notes.length} / 2000 Zeichen
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
