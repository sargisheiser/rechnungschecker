import { useState, useRef, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { FileCheck, Mail, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { useResendVerification, useVerifyEmail } from '@/hooks/useAuth'

export function EmailVerificationPending() {
  const location = useLocation()
  const navigate = useNavigate()
  const email = location.state?.email || ''
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [resendSuccess, setResendSuccess] = useState(false)
  const [verifyError, setVerifyError] = useState<string | null>(null)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  const resendVerification = useResendVerification()
  const verifyEmail = useVerifyEmail()

  // Focus first input on mount
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus()
    }
  }, [])

  const handleCodeChange = (index: number, value: string) => {
    // Only allow digits
    const digit = value.replace(/\D/g, '').slice(-1)

    const newCode = [...code]
    newCode[index] = digit
    setCode(newCode)
    setVerifyError(null)

    // Auto-focus next input
    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all 6 digits entered
    if (digit && index === 5) {
      const fullCode = newCode.join('')
      if (fullCode.length === 6) {
        handleVerify(fullCode)
      }
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)

    if (pastedData.length > 0) {
      const newCode = [...code]
      for (let i = 0; i < 6; i++) {
        newCode[i] = pastedData[i] || ''
      }
      setCode(newCode)
      setVerifyError(null)

      // Focus appropriate input
      const nextEmptyIndex = Math.min(pastedData.length, 5)
      inputRefs.current[nextEmptyIndex]?.focus()

      // Auto-submit if full code pasted
      if (pastedData.length === 6) {
        handleVerify(pastedData)
      }
    }
  }

  const handleVerify = async (verificationCode: string) => {
    if (!email || verificationCode.length !== 6) return

    try {
      await verifyEmail.mutateAsync({ email, code: verificationCode })
      // Success - redirect to login
      navigate('/login', {
        state: { message: 'E-Mail-Adresse erfolgreich verifiziert! Sie können sich jetzt anmelden.' }
      })
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      setVerifyError(err.response?.data?.detail || 'Verifizierung fehlgeschlagen. Bitte versuchen Sie es erneut.')
      // Clear code on error
      setCode(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    }
  }

  const handleResend = async () => {
    if (!email) return

    try {
      await resendVerification.mutateAsync(email)
      setResendSuccess(true)
      setVerifyError(null)
      setCode(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
      // Reset success message after 5 seconds
      setTimeout(() => setResendSuccess(false), 5000)
    } catch {
      // Error handled by mutation
    }
  }

  const fullCode = code.join('')
  const canSubmit = fullCode.length === 6 && email

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md text-center">
        <Link to="/" className="inline-flex items-center gap-2 mb-8">
          <FileCheck className="h-10 w-10 text-primary-600" />
          <span className="text-2xl font-bold text-gray-900">
            RechnungsChecker
          </span>
        </Link>

        <div className="card p-8">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="h-8 w-8 text-primary-600" />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            E-Mail bestaetigen
          </h1>

          <p className="text-gray-600 mb-6">
            Wir haben einen 6-stelligen Code an{' '}
            <strong className="text-gray-900">{email || 'Ihre E-Mail-Adresse'}</strong>{' '}
            gesendet. Bitte geben Sie den Code unten ein.
          </p>

          {/* 6-digit code input */}
          <div className="flex justify-center gap-2 mb-6" onPaste={handlePaste}>
            {code.map((digit, index) => (
              <input
                key={index}
                ref={(el) => { inputRefs.current[index] = el }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleCodeChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-colors"
                aria-label={`Code Ziffer ${index + 1}`}
              />
            ))}
          </div>

          {/* Error message */}
          {verifyError && (
            <div className="flex items-center justify-center gap-2 text-error-600 mb-4">
              <AlertCircle className="h-5 w-5" />
              <span className="text-sm">{verifyError}</span>
            </div>
          )}

          {/* Verify button */}
          <button
            onClick={() => handleVerify(fullCode)}
            disabled={!canSubmit || verifyEmail.isPending}
            className="btn-primary w-full mb-4"
          >
            {verifyEmail.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Wird verifiziert...
              </>
            ) : (
              'E-Mail verifizieren'
            )}
          </button>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600">
              <strong>Hinweis:</strong> Der Code ist 15 Minuten gueltig.
              Pruefen Sie auch Ihren Spam-Ordner, falls Sie die E-Mail nicht finden.
            </p>
          </div>

          {resendSuccess ? (
            <div className="flex items-center justify-center gap-2 text-success-600 mb-4">
              <CheckCircle className="h-5 w-5" />
              <span>Neuer Code wurde gesendet!</span>
            </div>
          ) : resendVerification.isError ? (
            <div className="flex items-center justify-center gap-2 text-error-600 mb-4">
              <AlertCircle className="h-5 w-5" />
              <span>Fehler beim Senden. Bitte versuchen Sie es erneut.</span>
            </div>
          ) : null}

          <button
            onClick={handleResend}
            disabled={resendVerification.isPending || !email}
            className="btn-secondary w-full mb-4"
          >
            {resendVerification.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Wird gesendet...
              </>
            ) : (
              'Code erneut senden'
            )}
          </button>

          <p className="text-sm text-gray-500">
            Falsche E-Mail-Adresse?{' '}
            <Link
              to="/registrieren"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Erneut registrieren
            </Link>
          </p>
        </div>

        <p className="mt-6 text-sm text-gray-500">
          Bereits verifiziert?{' '}
          <Link
            to="/login"
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Jetzt anmelden
          </Link>
        </p>
      </div>
    </div>
  )
}
