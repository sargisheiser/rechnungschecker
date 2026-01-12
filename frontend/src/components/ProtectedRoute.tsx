import { Navigate, useLocation } from 'react-router-dom'
import { useUser, useAuthStore } from '@/hooks/useAuth'
import { getAccessToken } from '@/lib/api'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireVerified?: boolean
}

export function ProtectedRoute({ children, requireVerified = true }: ProtectedRouteProps) {
  const location = useLocation()
  const { isAuthenticated, user } = useAuthStore()
  const { isLoading, isError } = useUser()
  const hasToken = !!getAccessToken()

  // If we have a token but haven't loaded user yet, show loading
  if (hasToken && isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  // If no token or error loading user, redirect to login
  if (!hasToken || isError || !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // If email verification is required and user is not verified, redirect to verification pending
  if (requireVerified && user && !user.is_verified) {
    return (
      <Navigate
        to="/email-bestaetigung"
        state={{ email: user.email }}
        replace
      />
    )
  }

  return <>{children}</>
}
