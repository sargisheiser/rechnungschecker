import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Clock,
  Cloud,
  Plus,
  Play,
  Pause,
  Trash2,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileText,
  Loader2,
} from 'lucide-react'
import { scheduledValidationsApi } from '@/lib/api'
import type {
  ScheduledValidationJob,
  ScheduledValidationRun,
  CreateScheduledJobRequest,
  CloudStorageProvider,
} from '@/types'

// Common cron presets
const cronPresets = [
  { label: 'Stündlich', value: '0 * * * *', description: 'Jede volle Stunde' },
  { label: 'Täglich 8:00', value: '0 8 * * *', description: 'Jeden Tag um 8:00 Uhr' },
  { label: 'Täglich 18:00', value: '0 18 * * *', description: 'Jeden Tag um 18:00 Uhr' },
  { label: 'Wöchentlich Mo', value: '0 8 * * 1', description: 'Jeden Montag um 8:00 Uhr' },
  { label: 'Monatlich', value: '0 8 1 * *', description: 'Am 1. jeden Monats um 8:00 Uhr' },
]

const providerOptions: { value: CloudStorageProvider; label: string }[] = [
  { value: 's3', label: 'Amazon S3' },
  { value: 'gcs', label: 'Google Cloud Storage (bald)' },
  { value: 'azure_blob', label: 'Azure Blob Storage (bald)' },
]

function ScheduledValidationsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null)

  // Fetch jobs
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['scheduled-validations'],
    queryFn: () => scheduledValidationsApi.list(),
  })

  // Create job mutation
  const createMutation = useMutation({
    mutationFn: scheduledValidationsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-validations'] })
      setShowCreateModal(false)
    },
  })

  // Delete job mutation
  const deleteMutation = useMutation({
    mutationFn: scheduledValidationsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-validations'] })
    },
  })

  // Toggle enabled mutation
  const toggleMutation = useMutation({
    mutationFn: ({ jobId, enabled }: { jobId: string; enabled: boolean }) =>
      scheduledValidationsApi.update(jobId, { is_enabled: enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-validations'] })
    },
  })

  // Trigger run mutation
  const triggerMutation = useMutation({
    mutationFn: scheduledValidationsApi.triggerRun,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-validations'] })
    },
  })

  const getStatusBadge = (job: ScheduledValidationJob) => {
    if (!job.is_enabled) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
          <Pause className="h-3 w-3" />
          Pausiert
        </span>
      )
    }
    if (job.status === 'error') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
          <XCircle className="h-3 w-3" />
          Fehler
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
        <CheckCircle className="h-3 w-3" />
        Aktiv
      </span>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Clock className="h-6 w-6 text-primary-600" />
            Geplante Validierungen
          </h1>
          <p className="text-gray-600 mt-1">
            Automatische Validierung von Rechnungen aus Cloud-Speicher
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Neuer Job
        </button>
      </div>

      {/* Info banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Cloud className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900">Cloud-Validierung</h3>
            <p className="text-sm text-blue-700 mt-1">
              Verbinden Sie Ihren S3-Bucket und lassen Sie Rechnungen automatisch nach einem
              Zeitplan validieren. Ideal für Steuerberater und Unternehmen mit automatisierten
              Rechnungseingangs-Pipelines.
            </p>
          </div>
        </div>
      </div>

      {/* Jobs list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Keine geplanten Jobs</h3>
          <p className="text-gray-600 mb-4">
            Erstellen Sie Ihren ersten geplanten Validierungs-Job, um automatisch Rechnungen aus
            Ihrem Cloud-Speicher zu validieren.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            Job erstellen
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              expanded={expandedJobId === job.id}
              onToggleExpand={() =>
                setExpandedJobId(expandedJobId === job.id ? null : job.id)
              }
              onToggleEnabled={(enabled) =>
                toggleMutation.mutate({ jobId: job.id, enabled })
              }
              onTriggerRun={() => triggerMutation.mutate(job.id)}
              onDelete={() => {
                if (confirm('Job wirklich löschen?')) {
                  deleteMutation.mutate(job.id)
                }
              }}
              getStatusBadge={getStatusBadge}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateJobModal
          onClose={() => setShowCreateModal(false)}
          onCreate={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
          error={createMutation.error?.message}
        />
      )}
    </div>
  )
}

interface JobCardProps {
  job: ScheduledValidationJob
  expanded: boolean
  onToggleExpand: () => void
  onToggleEnabled: (enabled: boolean) => void
  onTriggerRun: () => void
  onDelete: () => void
  getStatusBadge: (job: ScheduledValidationJob) => React.ReactNode
}

function JobCard({
  job,
  expanded,
  onToggleExpand,
  onToggleEnabled,
  onTriggerRun,
  onDelete,
  getStatusBadge,
}: JobCardProps) {
  const { data: runs = [] } = useQuery({
    queryKey: ['scheduled-validation-runs', job.id],
    queryFn: () => scheduledValidationsApi.getRuns(job.id, 5),
    enabled: expanded,
  })

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Job header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <Cloud className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{job.name}</h3>
              <p className="text-sm text-gray-500">
                {job.bucket_name}
                {job.prefix && `/${job.prefix}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {getStatusBadge(job)}
            <button
              onClick={onToggleExpand}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {expanded ? (
                <ChevronUp className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              )}
            </button>
          </div>
        </div>

        {/* Quick stats */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase">Zeitplan</p>
            <p className="font-medium">{job.schedule_cron}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Ausführungen</p>
            <p className="font-medium">{job.total_runs}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Gültig</p>
            <p className="font-medium text-green-600">{job.total_files_valid}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Ungültig</p>
            <p className="font-medium text-red-600">{job.total_files_invalid}</p>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 flex items-center gap-2 pt-4 border-t border-gray-100">
          <button
            onClick={() => onToggleEnabled(!job.is_enabled)}
            className={`btn btn-sm ${job.is_enabled ? 'btn-secondary' : 'btn-primary'}`}
          >
            {job.is_enabled ? (
              <>
                <Pause className="h-3 w-3" /> Pausieren
              </>
            ) : (
              <>
                <Play className="h-3 w-3" /> Aktivieren
              </>
            )}
          </button>
          <button
            onClick={onTriggerRun}
            disabled={!job.is_enabled}
            className="btn btn-sm btn-secondary"
          >
            <RefreshCw className="h-3 w-3" /> Jetzt ausführen
          </button>
          <div className="flex-1" />
          <button onClick={onDelete} className="btn btn-sm btn-ghost text-red-600 hover:text-red-700">
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Letzte Ausführungen</h4>
          {runs.length === 0 ? (
            <p className="text-sm text-gray-500">Noch keine Ausführungen</p>
          ) : (
            <div className="space-y-2">
              {runs.map((run) => (
                <RunRow key={run.id} run={run} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RunRow({ run }: { run: ScheduledValidationRun }) {
  const getStatusIcon = () => {
    switch (run.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <div className="flex items-center gap-4 p-3 bg-white rounded-lg border border-gray-200">
      {getStatusIcon()}
      <div className="flex-1">
        <p className="text-sm font-medium">
          {new Date(run.started_at).toLocaleString('de-DE')}
        </p>
        {run.error_message && (
          <p className="text-xs text-red-600 mt-1">{run.error_message}</p>
        )}
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-500">{run.files_found} Dateien</span>
        <span className="text-green-600">{run.files_valid} gültig</span>
        <span className="text-red-600">{run.files_invalid} ungültig</span>
        {run.files_failed > 0 && (
          <span className="text-orange-600">{run.files_failed} Fehler</span>
        )}
      </div>
    </div>
  )
}

interface CreateJobModalProps {
  onClose: () => void
  onCreate: (data: CreateScheduledJobRequest) => void
  isLoading: boolean
  error?: string
}

function CreateJobModal({ onClose, onCreate, isLoading, error }: CreateJobModalProps) {
  const [formData, setFormData] = useState<CreateScheduledJobRequest>({
    name: '',
    provider: 's3',
    credentials: {
      s3: {
        access_key_id: '',
        secret_access_key: '',
        region: 'eu-central-1',
      },
    },
    bucket_name: '',
    prefix: '',
    file_pattern: '*.xml',
    schedule_cron: '0 8 * * *',
    timezone: 'Europe/Berlin',
    delete_after_validation: false,
    move_to_folder: '',
  })

  const [connectionTested, setConnectionTested] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [testingConnection, setTestingConnection] = useState(false)

  const testConnection = async () => {
    setTestingConnection(true)
    setConnectionError(null)
    try {
      const result = await scheduledValidationsApi.testConnection({
        provider: formData.provider,
        credentials: formData.credentials,
        bucket_name: formData.bucket_name,
      })
      if (result.success) {
        setConnectionTested(true)
      } else {
        setConnectionError(result.message)
      }
    } catch (err: unknown) {
      setConnectionError(err instanceof Error ? err.message : 'Verbindungsfehler')
    } finally {
      setTestingConnection(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold">Neuen Job erstellen</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input w-full"
              placeholder="z.B. Tägliche Rechnungsvalidierung"
              required
            />
          </div>

          {/* Provider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cloud-Anbieter
            </label>
            <select
              value={formData.provider}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  provider: e.target.value as CloudStorageProvider,
                })
              }
              className="input w-full"
            >
              {providerOptions.map((opt) => (
                <option
                  key={opt.value}
                  value={opt.value}
                  disabled={opt.value !== 's3'}
                >
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* S3 Credentials */}
          {formData.provider === 's3' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AWS Access Key ID
                </label>
                <input
                  type="text"
                  value={formData.credentials.s3?.access_key_id || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      credentials: {
                        ...formData.credentials,
                        s3: { ...formData.credentials.s3!, access_key_id: e.target.value },
                      },
                    })
                  }
                  className="input w-full font-mono text-sm"
                  placeholder="AKIA..."
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AWS Secret Access Key
                </label>
                <input
                  type="password"
                  value={formData.credentials.s3?.secret_access_key || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      credentials: {
                        ...formData.credentials,
                        s3: { ...formData.credentials.s3!, secret_access_key: e.target.value },
                      },
                    })
                  }
                  className="input w-full font-mono text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Region
                </label>
                <input
                  type="text"
                  value={formData.credentials.s3?.region || 'eu-central-1'}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      credentials: {
                        ...formData.credentials,
                        s3: { ...formData.credentials.s3!, region: e.target.value },
                      },
                    })
                  }
                  className="input w-full"
                  placeholder="eu-central-1"
                />
              </div>
            </>
          )}

          {/* Bucket */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bucket-Name
            </label>
            <input
              type="text"
              value={formData.bucket_name}
              onChange={(e) => {
                setFormData({ ...formData, bucket_name: e.target.value })
                setConnectionTested(false)
              }}
              className="input w-full"
              placeholder="my-invoices-bucket"
              required
            />
          </div>

          {/* Test connection */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={testConnection}
              disabled={testingConnection || !formData.bucket_name}
              className="btn btn-secondary btn-sm"
            >
              {testingConnection ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Verbindung testen'
              )}
            </button>
            {connectionTested && (
              <span className="text-sm text-green-600 flex items-center gap-1">
                <CheckCircle className="h-4 w-4" /> Verbunden
              </span>
            )}
            {connectionError && (
              <span className="text-sm text-red-600">{connectionError}</span>
            )}
          </div>

          {/* Prefix */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ordner-Prefix (optional)
            </label>
            <input
              type="text"
              value={formData.prefix || ''}
              onChange={(e) => setFormData({ ...formData, prefix: e.target.value })}
              className="input w-full"
              placeholder="invoices/incoming/"
            />
          </div>

          {/* File pattern */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Datei-Muster
            </label>
            <input
              type="text"
              value={formData.file_pattern}
              onChange={(e) => setFormData({ ...formData, file_pattern: e.target.value })}
              className="input w-full"
              placeholder="*.xml"
            />
            <p className="text-xs text-gray-500 mt-1">
              Glob-Pattern zum Filtern der Dateien (z.B. *.xml, *.pdf)
            </p>
          </div>

          {/* Schedule */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Zeitplan
            </label>
            <select
              value={formData.schedule_cron}
              onChange={(e) => setFormData({ ...formData, schedule_cron: e.target.value })}
              className="input w-full"
            >
              {cronPresets.map((preset) => (
                <option key={preset.value} value={preset.value}>
                  {preset.label} - {preset.description}
                </option>
              ))}
            </select>
          </div>

          {/* Post-validation actions */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Nach Validierung
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.delete_after_validation}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    delete_after_validation: e.target.checked,
                    move_to_folder: e.target.checked ? '' : formData.move_to_folder,
                  })
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm">Dateien nach Validierung löschen</span>
            </label>
            {!formData.delete_after_validation && (
              <div className="ml-6">
                <input
                  type="text"
                  value={formData.move_to_folder || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, move_to_folder: e.target.value })
                  }
                  className="input w-full"
                  placeholder="invoices/validated/ (optional: verschieben nach)"
                />
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={isLoading}
            >
              Abbrechen
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading || !connectionTested}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Job erstellen'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ScheduledValidationsPage
