import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { FileCheck, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { useLogin } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()
  const navigate = useNavigate()
  const location = useLocation()

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
            Willkommen zurueck
          </h1>
          <p className="text-gray-600 mt-2">
            Melden Sie sich bei Ihrem Konto an
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {justVerified && (
              <div className="flex items-center gap-2 p-3 bg-success-50 rounded-lg text-success-600 text-sm">
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
                <span>E-Mail erfolgreich verifiziert! Sie koennen sich jetzt anmelden.</span>
              </div>
            )}

            {login.isError && (
              <div className="flex items-center gap-2 p-3 bg-error-50 rounded-lg text-error-600 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>E-Mail oder Passwort ist falsch</span>
              </div>
            )}

            <div>
              <label htmlFor="email" className="label">
                E-Mail Adresse
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={cn('input', login.isError && 'input-error')}
                placeholder="ihre@email.de"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="password" className="label mb-0">
                  Passwort
                </label>
                <Link
                  to="/passwort-vergessen"
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  Passwort vergessen?
                </Link>
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={cn('input', login.isError && 'input-error')}
                placeholder="Ihr Passwort"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={login.isPending}
              className="btn-primary w-full"
            >
              {login.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Anmelden...
                </>
              ) : (
                'Anmelden'
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Noch kein Konto?{' '}
            <Link
              to="/registrieren"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Jetzt registrieren
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
