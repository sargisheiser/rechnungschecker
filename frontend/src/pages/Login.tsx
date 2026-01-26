import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { FileCheck, Loader2, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useLogin } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import { GoogleAuthButton } from '@/components/GoogleAuthButton'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const login = useLogin()
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard'
  const justVerified = (location.state as { verified?: boolean })?.verified

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login.mutateAsync({ email, password })
      navigate(from, { replace: true })
    } catch {
      // Error handled by mutation
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <FileCheck className="h-10 w-10 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900">
              RechnungsChecker
            </span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            {t('auth.login.title')}
          </h1>
          <p className="text-gray-600 mt-2">
            {t('auth.login.subtitle')}
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {justVerified && (
              <div className="flex items-center gap-2 p-3 bg-success-50 rounded-lg text-success-600 text-sm">
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
                <span>{t('auth.login.emailVerified')}</span>
              </div>
            )}

            {login.isError && (
              <div className="flex items-center gap-2 p-3 bg-error-50 rounded-lg text-error-600 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{t('auth.login.invalidCredentials')}</span>
              </div>
            )}

            <div>
              <label htmlFor="email" className="label">
                {t('auth.email')}
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={cn('input', login.isError && 'input-error')}
                placeholder={t('auth.emailPlaceholder')}
                required
                autoComplete="email"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="password" className="label mb-0">
                  {t('auth.password')}
                </label>
                <Link
                  to="/passwort-vergessen"
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  {t('auth.login.forgotPassword')}
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={cn('input pr-10', login.isError && 'input-error')}
                  placeholder={t('auth.passwordPlaceholder')}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={login.isPending}
              className="btn-primary w-full"
            >
              {login.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t('auth.login.loggingIn')}
                </>
              ) : (
                t('nav.login')
              )}
            </button>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">oder</span>
              </div>
            </div>

            {/* Google OAuth */}
            <GoogleAuthButton mode="login" />
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            {t('auth.login.noAccount')}{' '}
            <Link
              to="/registrieren"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              {t('auth.login.registerNow')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
