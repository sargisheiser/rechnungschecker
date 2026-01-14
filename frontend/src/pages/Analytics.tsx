import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts'
import {
  BarChart3,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  Users,
} from 'lucide-react'
import { useAnalyticsDashboard, useClientComparison } from '@/hooks/useAnalytics'
import { useAuth } from '@/hooks/useAuth'

const COLORS = {
  valid: '#22c55e',
  invalid: '#ef4444',
  xrechnung: '#3b82f6',
  zugferd: '#8b5cf6',
}

export default function Analytics() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [days, setDays] = useState(30)
  const [selectedClient, setSelectedClient] = useState<string | undefined>()

  const { data: analytics, isLoading, error } = useAnalyticsDashboard(days, selectedClient)
  const { data: clientComparison } = useClientComparison(days)

  const isSteuerberater = user?.plan === 'steuerberater'

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-600">{t('analytics.errorLoading')}</p>
      </div>
    )
  }

  if (!analytics) return null

  const pieData = [
    { name: 'XRechnung', value: analytics.by_type.xrechnung, color: COLORS.xrechnung },
    { name: 'ZUGFeRD', value: analytics.by_type.zugferd, color: COLORS.zugferd },
  ].filter((d) => d.value > 0)

  const validationPieData = [
    { name: t('analytics.valid'), value: analytics.summary.valid_count, color: COLORS.valid },
    { name: t('analytics.invalid'), value: analytics.summary.invalid_count, color: COLORS.invalid },
  ].filter((d) => d.value > 0)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BarChart3 className="h-7 w-7 text-blue-600" />
              {t('analytics.title')}
            </h1>
            <p className="text-gray-600 mt-1">{t('analytics.subtitle')}</p>
          </div>

          {/* Period Selector */}
          <div className="flex items-center gap-4">
            {isSteuerberater && clientComparison && clientComparison.length > 0 && (
              <select
                value={selectedClient || ''}
                onChange={(e) => setSelectedClient(e.target.value || undefined)}
                className="rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">{t('analytics.allClients')}</option>
                {clientComparison.map((client) => (
                  <option key={client.client_id} value={client.client_id}>
                    {client.client_name}
                  </option>
                ))}
              </select>
            )}
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value={7}>{t('analytics.last7Days')}</option>
              <option value={30}>{t('analytics.last30Days')}</option>
              <option value={90}>{t('analytics.last90Days')}</option>
              <option value={365}>{t('analytics.lastYear')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('analytics.totalValidations')}</p>
              <p className="text-3xl font-bold text-gray-900">{analytics.summary.total_validations}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('analytics.successRate')}</p>
              <p className="text-3xl font-bold text-green-600">{analytics.summary.success_rate}%</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('analytics.avgProcessingTime')}</p>
              <p className="text-3xl font-bold text-gray-900">{analytics.summary.avg_processing_time_ms}ms</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{t('analytics.totalErrors')}</p>
              <p className="text-3xl font-bold text-red-600">{analytics.summary.total_errors}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Daily Validations Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.validationsOverTime')}</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.by_day}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => {
                    const date = new Date(value)
                    return `${date.getDate()}.${date.getMonth() + 1}`
                  }}
                  fontSize={12}
                />
                <YAxis fontSize={12} />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  contentStyle={{ borderRadius: '8px' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="valid"
                  name={t('analytics.valid')}
                  stroke={COLORS.valid}
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="invalid"
                  name={t('analytics.invalid')}
                  stroke={COLORS.invalid}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* File Type Distribution */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.fileTypeDistribution')}</h3>
          <div className="h-80 flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500">{t('analytics.noData')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Second Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Validation Results Pie */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.validationResults')}</h3>
          <div className="h-80 flex items-center">
            {validationPieData.length > 0 ? (
              <div className="w-full flex items-center justify-around">
                <ResponsiveContainer width="60%" height={250}>
                  <PieChart>
                    <Pie
                      data={validationPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {validationPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="text-sm text-gray-500">{t('analytics.valid')}</p>
                      <p className="text-xl font-bold text-gray-900">{analytics.summary.valid_count}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <XCircle className="h-5 w-5 text-red-500" />
                    <div>
                      <p className="text-sm text-gray-500">{t('analytics.invalid')}</p>
                      <p className="text-xl font-bold text-gray-900">{analytics.summary.invalid_count}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 w-full text-center">{t('analytics.noData')}</p>
            )}
          </div>
        </div>

        {/* Top Errors */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.topErrors')}</h3>
          {analytics.top_errors.length > 0 ? (
            <div className="space-y-4">
              {analytics.top_errors.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-400">#{index + 1}</span>
                    <div>
                      <p className="font-medium text-gray-900 truncate max-w-xs">{item.file_name}</p>
                      <p className="text-xs text-gray-500">{item.file_type.toUpperCase()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-red-600 font-medium">
                      {item.error_count} {t('analytics.errors')}
                    </span>
                    <span className="text-sm text-yellow-600">
                      {item.warning_count} {t('analytics.warnings')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
                <p className="text-gray-500">{t('analytics.noErrors')}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Client Comparison (Steuerberater only) */}
      {isSteuerberater && clientComparison && clientComparison.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-600" />
            {t('analytics.clientComparison')}
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={clientComparison} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="client_name"
                  width={120}
                  fontSize={12}
                  tickFormatter={(value) => (value.length > 15 ? `${value.slice(0, 15)}...` : value)}
                />
                <Tooltip />
                <Legend />
                <Bar dataKey="valid_count" name={t('analytics.valid')} fill={COLORS.valid} stackId="a" />
                <Bar dataKey="invalid_count" name={t('analytics.invalid')} fill={COLORS.invalid} stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Usage Section */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.currentUsage')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">{t('analytics.validationsThisMonth')}</span>
              <span className="text-sm font-medium text-gray-900">
                {analytics.usage.validations_used}
                {analytics.usage.validations_limit ? ` / ${analytics.usage.validations_limit}` : ' / Unlimited'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all"
                style={{
                  width: analytics.usage.validations_limit
                    ? `${Math.min((analytics.usage.validations_used / analytics.usage.validations_limit) * 100, 100)}%`
                    : '10%',
                }}
              ></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">{t('analytics.conversionsThisMonth')}</span>
              <span className="text-sm font-medium text-gray-900">
                {analytics.usage.conversions_used}
                {analytics.usage.conversions_limit ? ` / ${analytics.usage.conversions_limit}` : ' / Unlimited'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-purple-600 h-2.5 rounded-full transition-all"
                style={{
                  width: analytics.usage.conversions_limit
                    ? `${Math.min((analytics.usage.conversions_used / analytics.usage.conversions_limit) * 100, 100)}%`
                    : '10%',
                }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
