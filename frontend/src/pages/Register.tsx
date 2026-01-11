import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileCheck, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { useRegister, useLogin } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

export function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [error, setError] = useState('')

  const register = useRegister()
  const login = useLogin()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Die Passwoerter stimmen nicht ueberein')
      return
    }

    if (password.length < 8) {
      setError('Das Passwort muss mindestens 8 Zeichen lang sein')
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

      // Auto-login after registration
      await login.mutateAsync({ email, password })
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registrierung fehlgeschlagen')
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
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="Mindestens 8 Zeichen"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label">
                Passwort bestaetigen *
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={cn(
                  'input',
                  confirmPassword && password !== confirmPassword && 'input-error'
                )}
                placeholder="Passwort wiederholen"
                required
                autoComplete="new-password"
              />
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
              disabled={register.isPending || login.isPending}
              className="btn-primary w-full"
            >
              {register.isPending || login.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Konto wird erstellt...
                </>
              ) : (
                'Kostenlos registrieren'
              )}
            </button>
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
