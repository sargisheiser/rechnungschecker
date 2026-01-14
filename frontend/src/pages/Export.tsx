import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Download,
  ArrowLeft,
  Loader2,
  Shield,
  FileSpreadsheet,
  Users,
  Calendar,
  Filter,
  Check,
} from 'lucide-react'
import { useUser } from '@/hooks/useAuth'
import { useClients } from '@/hooks/useClients'
import { exportApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { ExportFormat, ExportValidationStatus } from '@/types'

export function ExportPage() {
  const { data: user } = useUser()
  const { data: clientsData } = useClients()

  const [activeTab, setActiveTab] = useState<'validations' | 'clients'>('validations')
  const [isExporting, setIsExporting] = useState(false)
  const [exportSuccess, setExportSuccess] = useState(false)

  // Validations export filters
  const [clientId, setClientId] = useState<string>('')
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')
  const [status, setStatus] = useState<ExportValidationStatus>('all')
  const [format, setFormat] = useState<ExportFormat>('datev')

  // Clients export filters
  const [includeInactive, setIncludeInactive] = useState(false)
  const [clientsDateFrom, setClientsDateFrom] = useState<string>('')
  const [clientsDateTo, setClientsDateTo] = useState<string>('')
  const [clientsFormat, setClientsFormat] = useState<ExportFormat>('datev')

  const canExport = user?.plan === 'steuerberater'

  if (!canExport) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Export nicht verfuegbar</h1>
          <p className="text-gray-600 mb-6">
            Der CSV-Export ist nur mit dem Steuerberater-Plan verfuegbar.
          </p>
          <Link to="/preise" className="btn-primary">
            Jetzt upgraden
          </Link>
        </div>
      </div>
    )
  }

  const handleExportValidations = async () => {
    setIsExporting(true)
    try {
      const blob = await exportApi.downloadValidations({
        client_id: clientId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        status: status,
        format: format,
      })

      // Download file
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `validierungen_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setExportSuccess(true)
      setTimeout(() => setExportSuccess(false), 3000)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportClients = async () => {
    setIsExporting(true)
    try {
      const blob = await exportApi.downloadClients({
        include_inactive: includeInactive,
        date_from: clientsDateFrom || undefined,
        date_to: clientsDateTo || undefined,
        format: clientsFormat,
      })

      // Download file
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mandanten_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setExportSuccess(true)
      setTimeout(() => setExportSuccess(false), 3000)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Zurueck zum Dashboard
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Datenexport</h1>
          <p className="text-gray-600 mt-1">
            Exportieren Sie Ihre Validierungen und Mandanten als CSV-Datei
          </p>
        </div>
      </div>

      {/* Success Banner */}
      {exportSuccess && (
        <div className="mb-6 p-4 bg-success-50 border border-success-200 rounded-lg flex items-center gap-3">
          <Check className="h-5 w-5 text-success-600" />
          <span className="text-success-700">Export erfolgreich! Die Datei wird heruntergeladen.</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('validations')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'validations'
              ? 'bg-primary-100 text-primary-700'
              : 'text-gray-600 hover:bg-gray-100'
          )}
        >
          <FileSpreadsheet className="h-5 w-5" />
          Validierungen
        </button>
        <button
          onClick={() => setActiveTab('clients')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'clients'
              ? 'bg-primary-100 text-primary-700'
              : 'text-gray-600 hover:bg-gray-100'
          )}
        >
          <Users className="h-5 w-5" />
          Mandanten
        </button>
      </div>

      {/* Validations Export */}
      {activeTab === 'validations' && (
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <FileSpreadsheet className="h-8 w-8 text-primary-500" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Validierungen exportieren</h2>
              <p className="text-sm text-gray-600">
                Exportieren Sie Ihre Validierungshistorie als CSV-Datei
              </p>
            </div>
          </div>

          <div className="space-y-6">
            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Users className="h-4 w-4 inline mr-1" />
                  Mandant
                </label>
                <select
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  className="input"
                >
                  <option value="">Alle Mandanten</option>
                  {clientsData?.items.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name} {client.client_number && `(${client.client_number})`}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Filter className="h-4 w-4 inline mr-1" />
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as ExportValidationStatus)}
                  className="input"
                >
                  <option value="all">Alle</option>
                  <option value="valid">Nur gueltig</option>
                  <option value="invalid">Nur ungueltig</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="h-4 w-4 inline mr-1" />
                  Von Datum
                </label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="h-4 w-4 inline mr-1" />
                  Bis Datum
                </label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="input"
                />
              </div>
            </div>

            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export-Format
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="format"
                    value="datev"
                    checked={format === 'datev'}
                    onChange={() => setFormat('datev')}
                    className="text-primary-600"
                  />
                  <span className="text-sm">DATEV (Semikolon-getrennt)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="format"
                    value="excel"
                    checked={format === 'excel'}
                    onChange={() => setFormat('excel')}
                    className="text-primary-600"
                  />
                  <span className="text-sm">Excel (Komma-getrennt)</span>
                </label>
              </div>
            </div>

            {/* Export Button */}
            <button
              onClick={handleExportValidations}
              disabled={isExporting}
              className="btn-primary w-full md:w-auto"
            >
              {isExporting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Validierungen exportieren
            </button>
          </div>
        </div>
      )}

      {/* Clients Export */}
      {activeTab === 'clients' && (
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <Users className="h-8 w-8 text-primary-500" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Mandanten exportieren</h2>
              <p className="text-sm text-gray-600">
                Exportieren Sie Ihre Mandantenliste mit Validierungsstatistiken
              </p>
            </div>
          </div>

          <div className="space-y-6">
            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeInactive}
                    onChange={(e) => setIncludeInactive(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Inaktive Mandanten einschliessen</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="h-4 w-4 inline mr-1" />
                  Statistik von Datum
                </label>
                <input
                  type="date"
                  value={clientsDateFrom}
                  onChange={(e) => setClientsDateFrom(e.target.value)}
                  className="input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Filtert Validierungsstatistiken ab diesem Datum
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Calendar className="h-4 w-4 inline mr-1" />
                  Statistik bis Datum
                </label>
                <input
                  type="date"
                  value={clientsDateTo}
                  onChange={(e) => setClientsDateTo(e.target.value)}
                  className="input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Filtert Validierungsstatistiken bis zu diesem Datum
                </p>
              </div>
            </div>

            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export-Format
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="clientsFormat"
                    value="datev"
                    checked={clientsFormat === 'datev'}
                    onChange={() => setClientsFormat('datev')}
                    className="text-primary-600"
                  />
                  <span className="text-sm">DATEV (Semikolon-getrennt)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="clientsFormat"
                    value="excel"
                    checked={clientsFormat === 'excel'}
                    onChange={() => setClientsFormat('excel')}
                    className="text-primary-600"
                  />
                  <span className="text-sm">Excel (Komma-getrennt)</span>
                </label>
              </div>
            </div>

            {/* Export Button */}
            <button
              onClick={handleExportClients}
              disabled={isExporting}
              className="btn-primary w-full md:w-auto"
            >
              {isExporting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              Mandanten exportieren
            </button>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-2">Hinweise zum Export</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>
            <strong>DATEV-Format:</strong> Verwendet Semikolon als Trennzeichen, optimiert fuer
            den Import in DATEV-Software.
          </li>
          <li>
            <strong>Excel-Format:</strong> Verwendet Komma als Trennzeichen, kompatibel mit
            Microsoft Excel und Google Sheets.
          </li>
          <li>Alle Exporte enthalten deutsche Spaltenueberschriften und UTF-8-Kodierung.</li>
        </ul>
      </div>
    </div>
  )
}
