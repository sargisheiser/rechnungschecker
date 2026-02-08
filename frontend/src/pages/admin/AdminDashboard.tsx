import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Users,
  UserCheck,
  FileCheck,
  ArrowUpDown,
  TrendingUp,
  Clock,
  Calendar,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { useAdminStats } from '@/hooks/useAdmin'
import { formatDistanceToNow } from 'date-fns'
import { de, enUS } from 'date-fns/locale'

export function AdminDashboard() {
  const { t, i18n } = useTranslation()
  const { data: stats, isLoading, isError } = useAdminStats()
  const dateLocale = i18n.language === 'de' ? de : enUS

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (isError || !stats) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-error-500 mx-auto mb-4" />
          <p className="text-gray-600">{t('admin.errorLoading')}</p>
        </div>
      </div>
    )
  }

  const statCards = [
    {
      label: t('admin.totalUsers'),
      value: stats.total_users,
      icon: Users,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      label: t('admin.activeUsers'),
      value: stats.active_users,
      icon: UserCheck,
      color: 'bg-green-100 text-green-600',
    },
    {
      label: t('admin.totalValidations'),
      value: stats.total_validations,
      icon: FileCheck,
      color: 'bg-purple-100 text-purple-600',
    },
    {
      label: t('admin.totalConversions'),
      value: stats.total_conversions,
      icon: ArrowUpDown,
      color: 'bg-orange-100 text-orange-600',
    },
  ]

  const timeStats = [
    {
      label: t('admin.validationsToday'),
      value: stats.validations_today,
      icon: Clock,
    },
    {
      label: t('admin.validationsThisWeek'),
      value: stats.validations_this_week,
      icon: Calendar,
    },
    {
      label: t('admin.validationsThisMonth'),
      value: stats.validations_this_month,
      icon: TrendingUp,
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">{t('admin.dashboard')}</h1>
        <p className="text-gray-600 mt-1">{t('admin.dashboardSubtitle')}</p>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => (
          <div key={stat.label} className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {stat.value.toLocaleString()}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Time-based Stats & Users by Plan */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Validation Stats */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {t('admin.validationStats')}
          </h2>
          <div className="space-y-4">
            {timeStats.map((stat) => (
              <div
                key={stat.label}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <stat.icon className="h-5 w-5 text-gray-500" />
                  <span className="text-gray-700">{stat.label}</span>
                </div>
                <span className="font-semibold text-gray-900">
                  {stat.value.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Users by Plan */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {t('admin.usersByPlan')}
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.users_by_plan).map(([plan, count]) => {
              const percentage = stats.total_users > 0
                ? Math.round((count / stats.total_users) * 100)
                : 0
              return (
                <div key={plan}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {plan}
                    </span>
                    <span className="text-sm text-gray-600">
                      {count} ({percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Recent Registrations */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {t('admin.recentRegistrations')}
          </h2>
          <Link
            to="/admin/users"
            className="text-sm text-primary-600 hover:underline"
          >
            {t('common.viewAll')}
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.email')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.plan')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.status')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.registeredAt')}
                </th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_registrations.map((user) => (
                <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <Link
                      to={`/admin/users?search=${encodeURIComponent(user.email)}`}
                      className="text-primary-600 hover:underline"
                    >
                      {user.email}
                    </Link>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700 capitalize">
                      {user.plan}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    {user.is_active ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                        {t('common.active')}
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">
                        {t('common.inactive')}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {formatDistanceToNow(new Date(user.created_at), {
                      addSuffix: true,
                      locale: dateLocale,
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
