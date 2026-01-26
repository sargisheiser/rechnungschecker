import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileCheck, Loader2, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react'
import { useRegister } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'
import { GoogleAuthButton } from '@/components/GoogleAuthButton'

export function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const register = useRegister()
  const navigate = useNavigate()

  const validatePassword = (pwd: string): string | null => {
    if (pwd.length < 8) {
      return 'Das Passwort muss mindestens 8 Zeichen lang sein'
    }
    if (!/[A-Z]/.test(pwd)) {
      return 'Das Passwort muss mindestens einen Grossbuchstaben enthalten'
    }
    if (!/[a-z]/.test(pwd)) {
      return 'Das Passwort muss mindestens einen Kleinbuchstaben enthalten'
    }
    if (!/[0-9]/.test(pwd)) {
      return 'Das Passwort muss mindestens eine Zahl enthalten'
    }
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Die Passwoerter stimmen nicht ueberein')
      return
    }

    const passwordError = validatePassword(password)
    if (passwordError) {
      setError(passwordError)
      return
    }

    if (!acceptTerms) {
      setError('Bitte akzeptieren Sie die AGB')
      return
    }

    try {
      await register.mutateAsync({
        email,
        password,
        company_name: companyName || undefined,
      })

      // Redirect to email verification pending page
      navigate('/email-bestaetigung', { state: { email } })
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string | Array<{ msg?: string }> } } }
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail[0]?.msg || 'Registrierung fehlgeschlagen')
      } else {
        setError(detail || 'Registrierung fehlgeschlagen')
      }
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
            Konto erstellen
          </h1>
          <p className="text-gray-600 mt-2">
            Starten Sie kostenlos mit 5 Validierungen pro Monat
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 p-3 bg-error-50 rounded-lg text-error-600 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label htmlFor="email" className="label">
                E-Mail Adresse *
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="ihre@email.de"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="company" className="label">
                Firmenname (optional)
              </label>
              <input
                id="company"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="input"
                placeholder="Ihre Firma GmbH"
                autoComplete="organization"
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Passwort *
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Min. 8 Zeichen, Gross-/Kleinbuchstaben, Zahl"
                  required
                  minLength={8}
                  autoComplete="new-password"
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
              <p className="text-xs text-gray-500 mt-1">
                Mindestens 8 Zeichen mit Gross-, Kleinbuchstaben und einer Zahl
              </p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label">
                Passwort bestaetigen *
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={cn(
                    'input pr-10',
                    confirmPassword && password !== confirmPassword && 'input-error'
                  )}
                  placeholder="Passwort wiederholen"
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <input
                id="terms"
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <label htmlFor="terms" className="text-sm text-gray-600">
                Ich akzeptiere die{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  AGB
                </a>{' '}
                und{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  Datenschutzerklaerung
                </a>
              </label>
            </div>

            <button
              type="submit"
              disabled={register.isPending}
              className="btn-primary w-full"
            >
              {register.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Konto wird erstellt...
                </>
              ) : (
                'Kostenlos registrieren'
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
            <GoogleAuthButton mode="register" />
          </form>

          {/* Benefits */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-900 mb-3">
              Im kostenlosen Plan enthalten:
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-success-500" />
                5 Validierungen pro Monat
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-success-500" />
                XRechnung & ZUGFeRD Pruefung
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-success-500" />
                Detaillierte Fehlerberichte
              </li>
            </ul>
          </div>

          <div className="mt-6 text-center text-sm text-gray-600">
            Bereits ein Konto?{' '}
            <Link
              to="/login"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Jetzt anmelden
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
