import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useDropzone } from 'react-dropzone'
import { Link } from 'react-router-dom'
import {
  Upload,
  FolderUp,
  X,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  AlertCircle,
  Loader2,
  Trash2,
  FileText,
  Eye,
  Download,
} from 'lucide-react'
import { useBatchJobs, useCreateBatch, useCancelBatch, useDeleteBatch, useBatchJob } from '@/hooks/useBatch'
import { cn } from '@/lib/utils'
import type { BatchJob, BatchJobStatus } from '@/lib/api'

const MAX_FILES = 50

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getStatusIcon(status: BatchJobStatus) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />
    case 'cancelled':
      return <XCircle className="h-5 w-5 text-gray-400" />
    case 'processing':
      return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
    case 'pending':
    default:
      return <Clock className="h-5 w-5 text-yellow-500" />
  }
}

function getStatusBadge(status: BatchJobStatus, t: (key: string) => string) {
  const styles: Record<BatchJobStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }

  return (
    <span className={cn('px-2 py-1 rounded-full text-xs font-medium', styles[status])}>
      {t(`batch.status.${status}`)}
    </span>
  )
}

export default function BatchUpload() {
  const { t } = useTranslation()
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [jobName, setJobName] = useState('')
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: jobs, isLoading: jobsLoading } = useBatchJobs()
  const { data: selectedJob } = useBatchJob(selectedJobId || undefined)
  const createBatch = useCreateBatch()
  const cancelBatch = useCancelBatch()
  const deleteBatch = useDeleteBatch()

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = [...selectedFiles, ...acceptedFiles].slice(0, MAX_FILES)
      setSelectedFiles(newFiles)
    },
    [selectedFiles]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/xml': ['.xml'],
      'text/xml': ['.xml'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: MAX_FILES,
  })

  const removeFile = (index: number) => {
    setSelectedFiles((files) => files.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) return

    try {
      setError(null)
      const result = await createBatch.mutateAsync({
        files: selectedFiles,
        name: jobName || `Batch ${new Date().toLocaleDateString()}`,
      })
      setSelectedFiles([])
      setJobName('')
      setSelectedJobId(result.id)
    } catch (err) {
      setError('Batch konnte nicht erstellt werden')
    }
  }

  const handleCancel = async (jobId: string) => {
    try {
      setError(null)
      await cancelBatch.mutateAsync(jobId)
    } catch (err) {
      setError('Batch konnte nicht abgebrochen werden')
    }
  }

  const handleDelete = async (jobId: string) => {
    try {
      setError(null)
      await deleteBatch.mutateAsync(jobId)
      if (selectedJobId === jobId) {
        setSelectedJobId(null)
      }
    } catch (err) {
      setError('Batch konnte nicht gelöscht werden')
    }
  }

  const handleExportCSV = () => {
    if (!selectedJob) return

    // CSV header
    const headers = ['Dateiname', 'Status', 'Größe (Bytes)', 'Fehler', 'Validierungs-ID']

    // CSV rows
    const rows = selectedJob.files.map((file) => [
      file.filename,
      file.status,
      file.file_size_bytes.toString(),
      file.error_message || '',
      file.validation_id || '',
    ])

    // Combine header and rows
    const csvContent = [
      headers.join(';'),
      ...rows.map((row) => row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(';')),
    ].join('\n')

    // Create and download file
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${selectedJob.name.replace(/[^a-zA-Z0-9]/g, '_')}_ergebnisse.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FolderUp className="h-7 w-7 text-blue-600" />
          {t('batch.title')}
        </h1>
        <p className="text-gray-600 mt-1">{t('batch.subtitle')}</p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-red-700">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto text-red-600 hover:text-red-700">
            ×
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('batch.uploadFiles')}</h2>

            {/* Job Name Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('batch.jobName')}</label>
              <input
                type="text"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder={t('batch.jobNamePlaceholder')}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
              )}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              {isDragActive ? (
                <p className="text-blue-600 font-medium">{t('batch.dropHere')}</p>
              ) : (
                <>
                  <p className="text-gray-600">{t('batch.dragAndDrop')}</p>
                  <p className="text-sm text-gray-500 mt-1">{t('batch.orClick')}</p>
                </>
              )}
              <p className="text-xs text-gray-400 mt-2">
                {t('batch.maxFiles', { max: MAX_FILES })}
              </p>
            </div>

            {/* Selected Files List */}
            {selectedFiles.length > 0 && (
              <div className="mt-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {t('batch.selectedFiles', { count: selectedFiles.length })}
                  </span>
                  <button onClick={() => setSelectedFiles([])} className="text-sm text-red-600 hover:text-red-700">
                    {t('batch.clearAll')}
                  </button>
                </div>
                <div className="max-h-48 overflow-y-auto space-y-2">
                  {selectedFiles.map((file, index) => (
                    <div
                      key={`${file.name}-${index}`}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="text-sm text-gray-700 truncate">{file.name}</span>
                        <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="p-1 text-gray-400 hover:text-red-500"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={selectedFiles.length === 0 || createBatch.isPending}
              className={cn(
                'mt-4 w-full py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2',
                selectedFiles.length === 0 || createBatch.isPending
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              )}
            >
              {createBatch.isPending ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  {t('batch.uploading')}
                </>
              ) : (
                <>
                  <Upload className="h-5 w-5" />
                  {t('batch.startValidation')}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('batch.recentJobs')}</h2>

          {jobsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
            </div>
          ) : jobs && jobs.items.length > 0 ? (
            <div className="space-y-4">
              {jobs.items.map((job: BatchJob) => (
                <div
                  key={job.id}
                  className={cn(
                    'p-4 rounded-lg border transition-colors cursor-pointer',
                    selectedJobId === job.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  )}
                  onClick={() => setSelectedJobId(job.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(job.status)}
                      <span className="font-medium text-gray-900">{job.name}</span>
                    </div>
                    {getStatusBadge(job.status, t)}
                  </div>

                  {/* Progress indicator for processing jobs */}
                  {job.status === 'processing' && (
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">
                          <span className="font-semibold text-gray-900">{job.processed_files}</span> von{' '}
                          <span className="font-semibold text-gray-900">{job.total_files}</span> Dateien verarbeitet
                        </span>
                        <span className="font-medium text-blue-600">{job.progress_percent}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress_percent}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500">
                        Wird verarbeitet... Bitte warten.
                      </p>
                    </div>
                  )}

                  {/* Info for pending/other status */}
                  {(job.status === 'pending' || job.status === 'cancelled' || job.status === 'failed') && (
                    <div className="mt-2 flex items-center justify-between text-sm text-gray-600">
                      <span>
                        {job.processed_files} / {job.total_files} {t('batch.files')}
                      </span>
                      <span>
                        {new Date(job.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}

                  {/* Results Summary for completed jobs */}
                  {job.status === 'completed' && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Ergebnis</span>
                        <span className="text-xs text-gray-500">
                          {new Date(job.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="flex items-center gap-1.5 text-green-600 font-medium">
                          <CheckCircle className="h-4 w-4" />
                          {job.successful_count} gültig
                        </span>
                        {job.failed_count > 0 && (
                          <span className="flex items-center gap-1.5 text-red-600 font-medium">
                            <XCircle className="h-4 w-4" />
                            {job.failed_count} ungültig
                          </span>
                        )}
                        {job.total_files - job.successful_count - job.failed_count > 0 && (
                          <span className="flex items-center gap-1.5 text-gray-500">
                            <AlertTriangle className="h-4 w-4" />
                            {job.total_files - job.successful_count - job.failed_count} übersprungen
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="mt-3 flex items-center gap-2">
                    {job.status === 'processing' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleCancel(job.id)
                        }}
                        className="text-sm text-yellow-600 hover:text-yellow-700"
                      >
                        {t('batch.cancel')}
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(job.id)
                      }}
                      className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                    >
                      <Trash2 className="h-3 w-3" />
                      {t('common.delete')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FolderUp className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">{t('batch.noJobs')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Selected Job Details */}
      {selectedJob && (
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {t('batch.jobDetails')}: {selectedJob.name}
            </h2>
            <button
              onClick={handleExportCSV}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Als CSV exportieren
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    {t('batch.fileName')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    {t('batch.fileStatus')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    {t('batch.fileSize')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    {t('batch.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {selectedJob.files.map((file) => (
                  <tr key={file.id}>
                    <td className="px-4 py-3 text-sm text-gray-900">{file.filename}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {file.status === 'completed' && <CheckCircle className="h-4 w-4 text-green-500" />}
                        {file.status === 'failed' && <XCircle className="h-4 w-4 text-red-500" />}
                        {file.status === 'processing' && <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />}
                        {file.status === 'pending' && <Clock className="h-4 w-4 text-yellow-500" />}
                        {file.status === 'skipped' && <AlertTriangle className="h-4 w-4 text-gray-400" />}
                        <span className="text-sm text-gray-700">{t(`batch.fileStatus.${file.status}`)}</span>
                      </div>
                      {file.error_message && (
                        <p className="text-xs text-red-600 mt-1">{file.error_message}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatFileSize(file.file_size_bytes)}</td>
                    <td className="px-4 py-3">
                      {file.validation_id && (
                        <Link
                          to={`/validierung/${file.validation_id}`}
                          className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                        >
                          <Eye className="h-4 w-4" />
                          {t('batch.viewResult')}
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
