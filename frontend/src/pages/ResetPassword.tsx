import { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { FileCheck, Loader2, AlertCircle, CheckCircle, ArrowLeft, Eye, EyeOff, KeyRound } from 'lucide-react'
import { useResetPassword } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

export function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [success, setSuccess] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const resetPassword = useResetPassword()

  // Redirect if no token
  useEffect(() => {
    if (!token) {
      navigate('/passwort-vergessen', { replace: true })
    }
  }, [token, navigate])

  const validatePassword = () => {
    if (password.length < 8) {
      setValidationError('Das Passwort muss mindestens 8 Zeichen lang sein.')
      return false
    }
    if (password !== confirmPassword) {
      setValidationError('Die Passwoerter stimmen nicht ueberein.')
      return false
    }
    setValidationError(null)
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validatePassword() || !token) return

    try {
      await resetPassword.mutateAsync({ token, password })
      setSuccess(true)
    } catch {
      // Error handled by mutation
    }
  }

  if (!token) {
    return null // Will redirect
  }

  if (success) {
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
          </div>

          <div className="card p-6 text-center">
            <div className="w-12 h-12 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-6 w-6 text-success-600" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">
              Passwort geaendert
            </h1>
            <p className="text-gray-600 mb-6">
              Ihr Passwort wurde erfolgreich zurueckgesetzt. Sie koennen sich jetzt mit Ihrem neuen Passwort anmelden.
            </p>
            <Link
              to="/login"
              className="btn-primary w-full inline-flex items-center justify-center"
            >
              Zur Anmeldung
            </Link>
          </div>
        </div>
      </div>
    )
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
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <KeyRound className="h-6 w-6 text-primary-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Neues Passwort festlegen
          </h1>
          <p className="text-gray-600 mt-2">
            Geben Sie Ihr neues Passwort ein.
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {resetPassword.isError && (
              <div className="flex items-center gap-2 p-3 bg-error-50 rounded-lg text-error-600 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>Der Link ist ungueltig oder abgelaufen. Bitte fordern Sie einen neuen an.</span>
              </div>
            )}

            {validationError && (
              <div className="flex items-center gap-2 p-3 bg-error-50 rounded-lg text-error-600 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}

            <div>
              <label htmlFor="password" className="label">
                Neues Passwort
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setValidationError(null)
                  }}
                  className={cn('input pr-10', validationError && 'input-error')}
                  placeholder="Mindestens 8 Zeichen"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label">
                Passwort bestaetigen
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value)
                    setValidationError(null)
                  }}
                  className={cn('input pr-10', validationError && 'input-error')}
                  placeholder="Passwort wiederholen"
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={resetPassword.isPending}
              className="btn-primary w-full"
            >
              {resetPassword.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Wird gespeichert...
                </>
              ) : (
                'Passwort speichern'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/passwort-vergessen"
              className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Neuen Link anfordern
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
