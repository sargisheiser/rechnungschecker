import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowLeft,
  Search,
  Filter,
  MoreVertical,
  UserCheck,
  UserX,
  Shield,
  ShieldOff,
  Trash2,
  Loader2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useAdminUsers, useUpdateAdminUser, useDeleteAdminUser } from '@/hooks/useAdmin'
import { formatDistanceToNow } from 'date-fns'
import { de, enUS } from 'date-fns/locale'
import type { AdminUserListItem, PlanTier } from '@/types'

export function AdminUsers() {
  const { t, i18n } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const dateLocale = i18n.language === 'de' ? de : enUS

  const page = parseInt(searchParams.get('page') || '1')
  const search = searchParams.get('search') || ''
  const planFilter = searchParams.get('plan') as PlanTier | undefined
  const statusFilter = searchParams.get('status')

  const [searchInput, setSearchInput] = useState(search)
  const [selectedUser, setSelectedUser] = useState<AdminUserListItem | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const isActive = statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined

  const { data, isLoading, isError } = useAdminUsers(page, 20, search || undefined, planFilter, isActive)
  const updateUser = useUpdateAdminUser()
  const deleteUser = useDeleteAdminUser()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const params = new URLSearchParams(searchParams)
    if (searchInput) {
      params.set('search', searchInput)
    } else {
      params.delete('search')
    }
    params.set('page', '1')
    setSearchParams(params)
  }

  const handleFilterChange = (key: string, value: string | undefined) => {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    params.set('page', '1')
    setSearchParams(params)
  }

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams)
    params.set('page', newPage.toString())
    setSearchParams(params)
  }

  const handleToggleActive = async (user: AdminUserListItem) => {
    await updateUser.mutateAsync({
      userId: user.id,
      data: { is_active: !user.is_active },
    })
  }

  const handleToggleAdmin = async (user: AdminUserListItem) => {
    await updateUser.mutateAsync({
      userId: user.id,
      data: { is_admin: !user.is_admin },
    })
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return
    await deleteUser.mutateAsync(selectedUser.id)
    setShowDeleteConfirm(false)
    setSelectedUser(null)
  }

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-error-500 mx-auto mb-4" />
          <p className="text-gray-600">{t('admin.errorLoading')}</p>
        </div>
      </div>
    )
  }

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/admin"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          {t('admin.backToDashboard')}
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{t('admin.userManagement')}</h1>
        <p className="text-gray-600 mt-1">{t('admin.userManagementSubtitle')}</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder={t('admin.searchUsers')}
                className="input pl-10"
              />
            </div>
          </form>

          {/* Plan Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={planFilter || ''}
              onChange={(e) => handleFilterChange('plan', e.target.value || undefined)}
              className="input w-auto"
            >
              <option value="">{t('admin.allPlans')}</option>
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="pro">Pro</option>
              <option value="steuerberater">Steuerberater</option>
            </select>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter || ''}
            onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
            className="input w-auto"
          >
            <option value="">{t('admin.allStatus')}</option>
            <option value="active">{t('common.active')}</option>
            <option value="inactive">{t('common.inactive')}</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.email')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.name')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.plan')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.status')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.validations')}
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.lastLogin')}
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                  {t('admin.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((user) => (
                <tr key={user.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {user.is_admin && (
                        <span title="Admin">
                          <Shield className="h-4 w-4 text-primary-600" />
                        </span>
                      )}
                      <span className="text-gray-900">{user.email}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-gray-600">
                    {user.full_name || '-'}
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
                    {!user.is_verified && (
                      <span className="ml-1 px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">
                        {t('admin.unverified')}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-gray-600">
                    {user.validations_this_month}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {user.last_login_at
                      ? formatDistanceToNow(new Date(user.last_login_at), {
                          addSuffix: true,
                          locale: dateLocale,
                        })
                      : t('admin.never')}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <div className="relative group">
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <MoreVertical className="h-4 w-4 text-gray-500" />
                        </button>
                        <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                          <button
                            onClick={() => handleToggleActive(user)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                          >
                            {user.is_active ? (
                              <>
                                <UserX className="h-4 w-4" />
                                {t('admin.suspend')}
                              </>
                            ) : (
                              <>
                                <UserCheck className="h-4 w-4" />
                                {t('admin.activate')}
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => handleToggleAdmin(user)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                          >
                            {user.is_admin ? (
                              <>
                                <ShieldOff className="h-4 w-4" />
                                {t('admin.removeAdmin')}
                              </>
                            ) : (
                              <>
                                <Shield className="h-4 w-4" />
                                {t('admin.makeAdmin')}
                              </>
                            )}
                          </button>
                          <hr className="my-1" />
                          <button
                            onClick={() => {
                              setSelectedUser(user)
                              setShowDeleteConfirm(true)
                            }}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                          >
                            <Trash2 className="h-4 w-4" />
                            {t('admin.deleteUser')}
                          </button>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              {t('admin.showingUsers', {
                from: (page - 1) * 20 + 1,
                to: Math.min(page * 20, data?.total || 0),
                total: data?.total || 0,
              })}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1}
                className="p-2 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-600">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page >= totalPages}
                className="p-2 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowDeleteConfirm(false)} />
          <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {t('admin.confirmDelete')}
            </h2>
            <p className="text-gray-600 mb-6">
              {t('admin.confirmDeleteMessage', { email: selectedUser.email })}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary flex-1"
                disabled={deleteUser.isPending}
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleDeleteUser}
                disabled={deleteUser.isPending}
                className="btn-primary bg-error-600 hover:bg-error-700 flex-1"
              >
                {deleteUser.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  t('common.delete')
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
