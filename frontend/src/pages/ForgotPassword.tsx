import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FileCheck, Loader2, AlertCircle, ArrowLeft, Mail } from 'lucide-react'
import { useForgotPassword } from '@/hooks/useAuth'

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const forgotPassword = useForgotPassword()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await forgotPassword.mutateAsync(email)
      setSubmitted(true)
    } catch {
      // Error handled by mutation
    }
  }

  if (submitted) {
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
              <Mail className="h-6 w-6 text-success-600" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">
              E-Mail gesendet
            </h1>
            <p className="text-gray-600 mb-6">
              Falls ein Konto mit <strong>{email}</strong> existiert, haben wir Ihnen
              einen Link zum Zurücksetzen des Passworts gesendet.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Bitte pruefen Sie auch Ihren Spam-Ordner.
            </p>
            <Link
              to="/login"
              className="btn-primary w-full inline-flex items-center justify-center"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Zurück zur Anmeldung
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
          <h1 className="text-2xl font-bold text-gray-900">
            Passwort vergessen?
          </h1>
          <p className="text-gray-600 mt-2">
            Geben Sie Ihre E-Mail Adresse ein und wir senden Ihnen einen Link zum Zurücksetzen.
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {forgotPassword.isError && (
              <div className="flex items-center gap-2 p-3 bg-error-50 rounded-lg text-error-600 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.</span>
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
                className="input"
                placeholder="ihre@email.de"
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={forgotPassword.isPending}
              className="btn-primary w-full"
            >
              {forgotPassword.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Wird gesendet...
                </>
              ) : (
                'Link senden'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Zurück zur Anmeldung
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
