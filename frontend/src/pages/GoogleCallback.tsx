import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, AlertCircle } from 'lucide-react'
import { authApi, setAccessToken, setRefreshToken } from '@/lib/api'
import { useAuthStore } from '@/hooks/useAuth'

export function GoogleCallback() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setUser } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const code = searchParams.get('code')
    const errorParam = searchParams.get('error')

    if (errorParam) {
      setError('Google-Anmeldung wurde abgebrochen oder fehlgeschlagen.')
      return
    }

    if (!code) {
      setError('Kein Autorisierungscode erhalten.')
      return
    }

    const handleCallback = async () => {
      try {
        const tokens = await authApi.googleCallback(code)
        setAccessToken(tokens.access_token)
        setRefreshToken(tokens.refresh_token)

        const user = await authApi.getMe()
        setUser(user)

        navigate('/dashboard', { replace: true })
      } catch {
        setError('Anmeldung fehlgeschlagen. Bitte versuchen Sie es erneut.')
      }
    }

    handleCallback()
  }, [searchParams, navigate, setUser])

  if (error) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="mx-auto w-16 h-16 bg-error-100 rounded-full flex items-center justify-center mb-4">
            <AlertCircle className="h-8 w-8 text-error-600" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Anmeldung fehlgeschlagen
          </h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => navigate('/login')}
              className="btn-primary"
            >
              Zur Anmeldung
            </button>
            <button
              onClick={() => authApi.googleLogin()}
              className="btn-secondary"
            >
              Erneut versuchen
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary-600 mx-auto mb-4" />
        <h1 className="text-xl font-semibold text-gray-900 mb-2">
          Anmeldung wird verarbeitet...
        </h1>
        <p className="text-gray-600">
          Bitte warten Sie einen Moment.
        </p>
      </div>
    </div>
  )
}
