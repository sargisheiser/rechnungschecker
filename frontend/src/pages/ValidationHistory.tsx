import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Search,
  FileCheck,
  CheckCircle,
  XCircle,
  Download,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react'
import { useValidationHistory, useDownloadReport } from '@/hooks/useValidation'
import { cn, formatDateTime } from '@/lib/utils'

type StatusFilter = 'all' | 'valid' | 'invalid'
type TypeFilter = 'all' | 'xrechnung' | 'zugferd'

export function ValidationHistory() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const pageSize = 20

  const { data: history, isLoading } = useValidationHistory(page, pageSize)
  const downloadReport = useDownloadReport()

  // Client-side filtering (backend doesn't support these filters yet)
  const filteredItems = useMemo(() => {
    if (!history?.items) return []

    return history.items.filter((item) => {
      // Search filter
      if (search && !item.file_name?.toLowerCase().includes(search.toLowerCase())) {
        return false
      }
      // Status filter
      if (statusFilter === 'valid' && !item.is_valid) return false
      if (statusFilter === 'invalid' && item.is_valid) return false
      // Type filter
      if (typeFilter !== 'all' && item.file_type !== typeFilter) return false

      return true
    })
  }, [history?.items, search, statusFilter, typeFilter])

  const totalPages = history ? Math.ceil(history.total / pageSize) : 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Zurück zum Dashboard
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Validierungsverlauf</h1>
        <p className="text-gray-600 mt-1">
          Alle Ihre vergangenen Validierungen
        </p>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="p-4 flex flex-wrap gap-4 items-center">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Dateiname suchen..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">Alle Status</option>
              <option value="valid">Gueltig</option>
              <option value="invalid">Ungueltig</option>
            </select>
          </div>

          {/* Type filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="all">Alle Typen</option>
            <option value="xrechnung">XRechnung</option>
            <option value="zugferd">ZUGFeRD</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-12 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center">
            <FileCheck className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {search || statusFilter !== 'all' || typeFilter !== 'all'
                ? 'Keine Ergebnisse'
                : 'Keine Validierungen'}
            </h3>
            <p className="text-gray-500">
              {search || statusFilter !== 'all' || typeFilter !== 'all'
                ? 'Versuchen Sie andere Filterkriterien.'
                : 'Laden Sie eine Datei hoch, um Ihre erste Validierung durchzufuehren.'}
            </p>
            {!search && statusFilter === 'all' && typeFilter === 'all' && (
              <Link to="/dashboard" className="btn-primary mt-4 inline-flex">
                Zur Validierung
              </Link>
            )}
          </div>
        ) : (
          <>
            {/* Table header */}
            <div className="hidden md:grid md:grid-cols-[1fr_120px_100px_80px_80px_150px_80px] gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wide">
              <div>Dateiname</div>
              <div>Typ</div>
              <div>Status</div>
              <div>Fehler</div>
              <div>Warnungen</div>
              <div>Datum</div>
              <div>Aktionen</div>
            </div>

            {/* Table rows */}
            <div className="divide-y divide-gray-200">
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className="md:grid md:grid-cols-[1fr_120px_100px_80px_80px_150px_80px] gap-4 px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors items-center"
                  onClick={() => navigate(`/validierung/${item.id}`)}
                >
                  {/* Filename */}
                  <div className="flex items-center gap-3 mb-2 md:mb-0">
                    {item.is_valid ? (
                      <CheckCircle className="h-5 w-5 text-success-500 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-5 w-5 text-error-500 flex-shrink-0" />
                    )}
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {item.file_name || 'Unbekannte Datei'}
                    </span>
                  </div>

                  {/* Type */}
                  <div className="mb-2 md:mb-0">
                    <span
                      className={cn(
                        'inline-flex px-2 py-1 text-xs font-medium rounded',
                        item.file_type === 'xrechnung'
                          ? 'bg-blue-50 text-blue-700'
                          : 'bg-purple-50 text-purple-700'
                      )}
                    >
                      {item.file_type === 'xrechnung' ? 'XRechnung' : 'ZUGFeRD'}
                    </span>
                  </div>

                  {/* Status */}
                  <div className="mb-2 md:mb-0">
                    <span
                      className={cn(
                        'inline-flex px-2 py-1 text-xs font-medium rounded',
                        item.is_valid
                          ? 'bg-success-50 text-success-700'
                          : 'bg-error-50 text-error-700'
                      )}
                    >
                      {item.is_valid ? 'Gueltig' : 'Ungueltig'}
                    </span>
                  </div>

                  {/* Errors */}
                  <div className="text-sm text-gray-600 mb-1 md:mb-0">
                    <span className="md:hidden text-gray-400">Fehler: </span>
                    {item.error_count}
                  </div>

                  {/* Warnings */}
                  <div className="text-sm text-gray-600 mb-1 md:mb-0">
                    <span className="md:hidden text-gray-400">Warnungen: </span>
                    {item.warning_count}
                  </div>

                  {/* Date */}
                  <div className="text-sm text-gray-500 mb-2 md:mb-0">
                    {formatDateTime(item.validated_at)}
                  </div>

                  {/* Actions */}
                  <div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        downloadReport.mutate(item.id)
                      }}
                      disabled={downloadReport.isPending}
                      className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="Bericht herunterladen"
                    >
                      {downloadReport.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Seite {page} von {totalPages} ({history?.total} Eintraege)
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
