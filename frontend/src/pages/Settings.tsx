import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowLeft,
  User,
  Lock,
  Trash2,
  Loader2,
  Check,
  AlertTriangle,
  Building,
  Mail,
  Shield,
  Bell,
} from 'lucide-react'
import {
  useUser,
  useUpdateProfile,
  useChangePassword,
  useDeleteAccount,
} from '@/hooks/useAuth'
import { cn as _cn } from '@/lib/utils'

export function SettingsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data: user } = useUser()
  const updateProfile = useUpdateProfile()
  const changePassword = useChangePassword()
  const deleteAccount = useDeleteAccount()

  // Profile form state
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [companyName, setCompanyName] = useState(user?.company_name || '')
  const [profileSaved, setProfileSaved] = useState(false)

  // Notification preferences state
  const [emailNotifications, setEmailNotifications] = useState(user?.email_notifications ?? true)
  const [notifyValidationResults, setNotifyValidationResults] = useState(user?.notify_validation_results ?? true)
  const [notifyWeeklySummary, setNotifyWeeklySummary] = useState(user?.notify_weekly_summary ?? false)
  const [notifyMarketing, setNotifyMarketing] = useState(user?.notify_marketing ?? false)
  const [notificationsSaved, setNotificationsSaved] = useState(false)

  // Update state when user data loads
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '')
      setCompanyName(user.company_name || '')
      setEmailNotifications(user.email_notifications)
      setNotifyValidationResults(user.notify_validation_results)
      setNotifyWeeklySummary(user.notify_weekly_summary)
      setNotifyMarketing(user.notify_marketing)
    }
  }, [user])

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordChanged, setPasswordChanged] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await updateProfile.mutateAsync({
        full_name: fullName || undefined,
        company_name: companyName || undefined,
      })
      setProfileSaved(true)
      setTimeout(() => setProfileSaved(false), 3000)
    } catch (error) {
      console.error('Failed to update profile:', error)
    }
  }

  const handleUpdateNotifications = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await updateProfile.mutateAsync({
        email_notifications: emailNotifications,
        notify_validation_results: notifyValidationResults,
        notify_weekly_summary: notifyWeeklySummary,
        notify_marketing: notifyMarketing,
      })
      setNotificationsSaved(true)
      setTimeout(() => setNotificationsSaved(false), 3000)
    } catch (error) {
      console.error('Failed to update notifications:', error)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')

    if (newPassword !== confirmPassword) {
      setPasswordError('Die Passwoerter stimmen nicht ueberein')
      return
    }

    if (newPassword.length < 8) {
      setPasswordError('Das Passwort muss mindestens 8 Zeichen lang sein')
      return
    }

    try {
      await changePassword.mutateAsync({ currentPassword, newPassword })
      setPasswordChanged(true)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => setPasswordChanged(false), 3000)
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Passwort konnte nicht geaendert werden'
      setPasswordError(message)
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'LOESCHEN') return

    try {
      await deleteAccount.mutateAsync()
      navigate('/')
    } catch (error) {
      console.error('Failed to delete account:', error)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          {t('settings.backToDashboard')}
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-gray-600 mt-1">
          {t('settings.subtitle')}
        </p>
      </div>

      {/* Profile Section */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-primary-100 rounded-lg">
            <User className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.profile')}</h2>
            <p className="text-sm text-gray-600">{t('settings.profileDesc')}</p>
          </div>
        </div>

        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Mail className="h-4 w-4 inline mr-1" />
              {t('settings.email')}
            </label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="input bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="text-xs text-gray-500 mt-1">
              {t('settings.emailHint')}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <User className="h-4 w-4 inline mr-1" />
              {t('settings.fullName')}
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t('settings.fullNamePlaceholder')}
              className="input"
              maxLength={255}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Building className="h-4 w-4 inline mr-1" />
              {t('settings.companyName')}
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder={t('settings.companyNamePlaceholder')}
              className="input"
              maxLength={255}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Shield className="h-4 w-4 inline mr-1" />
              {t('settings.plan')}
            </label>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg text-sm font-medium capitalize">
                {user?.plan}
              </span>
              <Link to="/preise" className="text-sm text-primary-600 hover:underline">
                {t('settings.changePlan')}
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={updateProfile.isPending}
              className="btn-primary"
            >
              {updateProfile.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                t('settings.save')
              )}
            </button>
            {profileSaved && (
              <span className="text-sm text-success-600 flex items-center gap-1">
                <Check className="h-4 w-4" />
                {t('settings.saved')}
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Notifications Section */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Bell className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.notifications')}</h2>
            <p className="text-sm text-gray-600">{t('settings.notificationsDesc')}</p>
          </div>
        </div>

        <form onSubmit={handleUpdateNotifications} className="space-y-4">
          <div className="space-y-3">
            {/* Main toggle */}
            <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
              <div>
                <span className="font-medium text-gray-900">{t('settings.emailNotifications')}</span>
                <p className="text-sm text-gray-500">{t('settings.emailNotificationsDesc')}</p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={emailNotifications}
                  onChange={(e) => setEmailNotifications(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </div>
            </label>

            {/* Sub-options - only show when email notifications are enabled */}
            {emailNotifications && (
              <div className="ml-4 pl-4 border-l-2 border-gray-200 space-y-3">
                <label className="flex items-center justify-between p-3 bg-white rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border border-gray-200">
                  <div>
                    <span className="font-medium text-gray-900">{t('settings.validationResults')}</span>
                    <p className="text-sm text-gray-500">{t('settings.validationResultsDesc')}</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={notifyValidationResults}
                      onChange={(e) => setNotifyValidationResults(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </div>
                </label>

                <label className="flex items-center justify-between p-3 bg-white rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border border-gray-200">
                  <div>
                    <span className="font-medium text-gray-900">{t('settings.weeklySummary')}</span>
                    <p className="text-sm text-gray-500">{t('settings.weeklySummaryDesc')}</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={notifyWeeklySummary}
                      onChange={(e) => setNotifyWeeklySummary(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </div>
                </label>

                <label className="flex items-center justify-between p-3 bg-white rounded-lg cursor-pointer hover:bg-gray-50 transition-colors border border-gray-200">
                  <div>
                    <span className="font-medium text-gray-900">{t('settings.productUpdates')}</span>
                    <p className="text-sm text-gray-500">{t('settings.productUpdatesDesc')}</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={notifyMarketing}
                      onChange={(e) => setNotifyMarketing(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </div>
                </label>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={updateProfile.isPending}
              className="btn-primary"
            >
              {updateProfile.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                t('settings.save')
              )}
            </button>
            {notificationsSaved && (
              <span className="text-sm text-success-600 flex items-center gap-1">
                <Check className="h-4 w-4" />
                {t('settings.saved')}
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Password Section */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-warning-100 rounded-lg">
            <Lock className="h-5 w-5 text-warning-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.changePassword')}</h2>
            <p className="text-sm text-gray-600">{t('settings.changePasswordDesc')}</p>
          </div>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Aktuelles Passwort
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Neues Passwort
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="input"
              required
              minLength={8}
            />
            <p className="text-xs text-gray-500 mt-1">
              Mindestens 8 Zeichen, mit Gross- und Kleinbuchstaben sowie einer Zahl
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Passwort bestaetigen
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input"
              required
            />
          </div>

          {passwordError && (
            <div className="p-3 bg-error-50 border border-error-200 rounded-lg text-sm text-error-700">
              {passwordError}
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={changePassword.isPending || !currentPassword || !newPassword || !confirmPassword}
              className="btn-primary"
            >
              {changePassword.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Passwort aendern'
              )}
            </button>
            {passwordChanged && (
              <span className="text-sm text-success-600 flex items-center gap-1">
                <Check className="h-4 w-4" />
                Passwort geaendert
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Danger Zone */}
      <div className="card p-6 border-error-200">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-error-100 rounded-lg">
            <Trash2 className="h-5 w-5 text-error-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Gefahrenzone</h2>
            <p className="text-sm text-gray-600">Unwiderrufliche Aktionen</p>
          </div>
        </div>

        <div className="p-4 bg-error-50 rounded-lg">
          <h3 className="font-medium text-error-900 mb-2">Konto loeschen</h3>
          <p className="text-sm text-error-700 mb-4">
            Wenn Sie Ihr Konto loeschen, werden alle Ihre Daten unwiderruflich entfernt.
            Diese Aktion kann nicht rueckgaengig gemacht werden.
          </p>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="btn-primary bg-error-600 hover:bg-error-700"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Konto loeschen
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowDeleteConfirm(false)} />
          <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-error-100 rounded-full">
                <AlertTriangle className="h-6 w-6 text-error-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">
                Konto wirklich loeschen?
              </h2>
            </div>

            <p className="text-gray-600 mb-4">
              Diese Aktion kann nicht rueckgaengig gemacht werden. Alle Ihre Daten,
              einschliesslich Validierungshistorie und Einstellungen, werden dauerhaft geloescht.
            </p>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Geben Sie <span className="font-mono font-bold">LOESCHEN</span> ein, um zu bestaetigen
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="LOESCHEN"
                className="input"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setDeleteConfirmText('')
                }}
                className="btn-secondary flex-1"
                disabled={deleteAccount.isPending}
              >
                Abbrechen
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== 'LOESCHEN' || deleteAccount.isPending}
                className="btn-primary bg-error-600 hover:bg-error-700 flex-1 disabled:opacity-50"
              >
                {deleteAccount.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Endgueltig loeschen'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
