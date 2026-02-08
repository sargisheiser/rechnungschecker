import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Search,
  CheckCircle,
  XCircle,
  Download,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Filter,
  FileSpreadsheet,
  Check,
} from 'lucide-react'
import { useValidationHistory, useDownloadReport } from '@/hooks/useValidation'
import { useExportDATEV } from '@/hooks/useExport'
import { useAuthStore } from '@/hooks/useAuth'
import { cn, formatDateTime } from '@/lib/utils'
import { Skeleton, EmptyState, emptyStatePresets } from '@/components'

type StatusFilter = 'all' | 'valid' | 'invalid'
type TypeFilter = 'all' | 'xrechnung' | 'zugferd'

export function ValidationHistory() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectionMode, setSelectionMode] = useState(false)
  const pageSize = 20

  const { data: history, isLoading } = useValidationHistory(page, pageSize)
  const downloadReport = useDownloadReport()
  const exportDATEV = useExportDATEV()
  const { user } = useAuthStore()

  // Check if user has Steuerberater plan for DATEV export
  const canExportDATEV = user?.plan === 'steuerberater'

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (!filteredItems) return
    const validIds = filteredItems.filter((item) => item.is_valid).map((item) => item.id)
    if (selectedIds.size === validIds.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(validIds))
    }
  }

  const handleDATEVExport = () => {
    if (selectedIds.size === 0) return
    exportDATEV.mutate({
      validationIds: Array.from(selectedIds),
      kontenrahmen: 'SKR03',
    })
  }

  const exitSelectionMode = () => {
    setSelectionMode(false)
    setSelectedIds(new Set())
  }

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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Validierungsverlauf</h1>
            <p className="text-gray-600 mt-1">
              Alle Ihre vergangenen Validierungen
            </p>
          </div>

          {/* DATEV Export Button */}
          {canExportDATEV && (
            <div className="flex items-center gap-2">
              {selectionMode ? (
                <>
                  <span className="text-sm text-gray-500">
                    {selectedIds.size} ausgewaehlt
                  </span>
                  <button
                    onClick={handleDATEVExport}
                    disabled={selectedIds.size === 0 || exportDATEV.isPending}
                    className="btn-primary flex items-center gap-2"
                  >
                    {exportDATEV.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <FileSpreadsheet className="h-4 w-4" />
                    )}
                    DATEV Export
                  </button>
                  <button
                    onClick={exitSelectionMode}
                    className="btn-secondary"
                  >
                    Abbrechen
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setSelectionMode(true)}
                  className="btn-secondary flex items-center gap-2"
                  title="Rechnungen fuer DATEV-Export auswaehlen"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Export fuer DATEV
                </button>
              )}
            </div>
          )}
        </div>
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
          <>
            {/* Skeleton table header */}
            <div className="hidden md:grid md:grid-cols-[1fr_120px_100px_80px_80px_150px_80px] gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-12" />
              <Skeleton className="h-3 w-14" />
              <Skeleton className="h-3 w-12" />
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-3 w-12" />
              <Skeleton className="h-3 w-14" />
            </div>
            {/* Skeleton rows */}
            <div className="divide-y divide-gray-200">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="md:grid md:grid-cols-[1fr_120px_100px_80px_80px_150px_80px] gap-4 px-6 py-4 items-center"
                >
                  <div className="flex items-center gap-3 mb-2 md:mb-0">
                    <Skeleton className="h-5 w-5 rounded-full" />
                    <Skeleton className="h-4 w-48" />
                  </div>
                  <Skeleton className="h-6 w-20 rounded mb-2 md:mb-0" />
                  <Skeleton className="h-6 w-16 rounded mb-2 md:mb-0" />
                  <Skeleton className="h-4 w-8 mb-1 md:mb-0" />
                  <Skeleton className="h-4 w-8 mb-1 md:mb-0" />
                  <Skeleton className="h-4 w-28 mb-2 md:mb-0" />
                  <Skeleton className="h-8 w-8 rounded" />
                </div>
              ))}
            </div>
          </>
        ) : filteredItems.length === 0 ? (
          search || statusFilter !== 'all' || typeFilter !== 'all' ? (
            <EmptyState
              {...emptyStatePresets.noSearchResults}
              action={{
                label: 'Filter zurücksetzen',
                onClick: () => {
                  setSearch('')
                  setStatusFilter('all')
                  setTypeFilter('all')
                },
              }}
            />
          ) : (
            <EmptyState
              {...emptyStatePresets.noValidations}
              action={{
                label: 'Erste Rechnung validieren',
                href: '/dashboard',
              }}
            />
          )
        ) : (
          <>
            {/* Table header */}
            <div className={cn(
              "hidden md:grid gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wide",
              selectionMode
                ? "md:grid-cols-[40px_1fr_120px_100px_80px_80px_150px_80px]"
                : "md:grid-cols-[1fr_120px_100px_80px_80px_150px_80px]"
            )}>
              {selectionMode && (
                <div className="flex items-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleSelectAll()
                    }}
                    className="p-1 rounded hover:bg-gray-200"
                    title="Alle gueltigen auswaehlen"
                  >
                    <Check className={cn(
                      "h-4 w-4",
                      selectedIds.size > 0 ? "text-primary-600" : "text-gray-400"
                    )} />
                  </button>
                </div>
              )}
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
                  className={cn(
                    "md:grid gap-4 px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors items-center",
                    selectionMode
                      ? "md:grid-cols-[40px_1fr_120px_100px_80px_80px_150px_80px]"
                      : "md:grid-cols-[1fr_120px_100px_80px_80px_150px_80px]",
                    selectedIds.has(item.id) && "bg-primary-50"
                  )}
                  onClick={() => {
                    if (selectionMode && item.is_valid) {
                      toggleSelection(item.id)
                    } else if (!selectionMode) {
                      navigate(`/validierung/${item.id}`)
                    }
                  }}
                >
                  {/* Selection checkbox */}
                  {selectionMode && (
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(item.id)}
                        disabled={!item.is_valid}
                        onChange={(e) => {
                          e.stopPropagation()
                          if (item.is_valid) {
                            toggleSelection(item.id)
                          }
                        }}
                        className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500 disabled:opacity-50"
                        title={item.is_valid ? 'Auswaehlen' : 'Nur gueltige Rechnungen koennen exportiert werden'}
                      />
                    </div>
                  )}

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

export default ValidationHistory
