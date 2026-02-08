import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ProtectedRoute } from './ProtectedRoute'

// Mock the hooks
vi.mock('@/hooks/useAuth', () => ({
  useUser: vi.fn(),
  useAuthStore: vi.fn(),
}))

vi.mock('@/lib/api', () => ({
  getAccessToken: vi.fn(),
}))

// Mock Navigate component
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Navigate: vi.fn(({ to }) => <div data-testid="navigate" data-to={to} />),
    useLocation: vi.fn(() => ({ pathname: '/dashboard', state: null })),
  }
})

import { useUser, useAuthStore } from '@/hooks/useAuth'
import { getAccessToken } from '@/lib/api'

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.mocked(getAccessToken).mockReturnValue(null)
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
      user: null,
    })
    vi.mocked(useUser).mockReturnValue({
      isLoading: false,
      isError: false,
      data: undefined,
      error: null,
    } as ReturnType<typeof useUser>)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('no authentication', () => {
    it('redirects to login when no token', () => {
      vi.mocked(getAccessToken).mockReturnValue(null)

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/login')
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('redirects to login when not authenticated', () => {
      vi.mocked(getAccessToken).mockReturnValue('some-token')
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
      })

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/login')
    })

    it('redirects to login on user loading error', () => {
      vi.mocked(getAccessToken).mockReturnValue('some-token')
      vi.mocked(useUser).mockReturnValue({
        isLoading: false,
        isError: true,
        data: undefined,
        error: new Error('Failed'),
      } as ReturnType<typeof useUser>)

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/login')
    })
  })

  describe('loading state', () => {
    it('shows loading spinner when token exists but user is loading', () => {
      vi.mocked(getAccessToken).mockReturnValue('some-token')
      vi.mocked(useUser).mockReturnValue({
        isLoading: true,
        isError: false,
        data: undefined,
        error: null,
      } as ReturnType<typeof useUser>)

      const { container } = render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should show loading spinner
      expect(container.querySelector('.animate-spin')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })

  describe('authenticated state', () => {
    it('renders children when authenticated and verified', () => {
      vi.mocked(getAccessToken).mockReturnValue('valid-token')
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: {
          id: '1',
          email: 'test@example.com',
          is_verified: true,
          is_active: true,
          is_admin: false,
          plan: 'free',
          created_at: '2024-01-01',
          email_notifications: true,
          notify_validation_results: true,
          notify_weekly_summary: true,
          notify_marketing: false,
        },
      })
      vi.mocked(useUser).mockReturnValue({
        isLoading: false,
        isError: false,
        data: { id: '1', email: 'test@example.com' },
        error: null,
      } as ReturnType<typeof useUser>)

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })

  describe('email verification', () => {
    it('redirects to verification page when user is not verified', () => {
      vi.mocked(getAccessToken).mockReturnValue('valid-token')
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: {
          id: '1',
          email: 'test@example.com',
          is_verified: false,
          is_active: true,
          is_admin: false,
          plan: 'free',
          created_at: '2024-01-01',
          email_notifications: true,
          notify_validation_results: true,
          notify_weekly_summary: true,
          notify_marketing: false,
        },
      })
      vi.mocked(useUser).mockReturnValue({
        isLoading: false,
        isError: false,
        data: { id: '1', email: 'test@example.com', is_verified: false },
        error: null,
      } as ReturnType<typeof useUser>)

      render(
        <ProtectedRoute requireVerified>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/email-bestaetigung')
    })

    it('allows unverified user when requireVerified is false', () => {
      vi.mocked(getAccessToken).mockReturnValue('valid-token')
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: {
          id: '1',
          email: 'test@example.com',
          is_verified: false,
          is_active: true,
          is_admin: false,
          plan: 'free',
          created_at: '2024-01-01',
          email_notifications: true,
          notify_validation_results: true,
          notify_weekly_summary: true,
          notify_marketing: false,
        },
      })
      vi.mocked(useUser).mockReturnValue({
        isLoading: false,
        isError: false,
        data: { id: '1', email: 'test@example.com', is_verified: false },
        error: null,
      } as ReturnType<typeof useUser>)

      render(
        <ProtectedRoute requireVerified={false}>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })
})
