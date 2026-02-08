import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { AdminRoute } from './AdminRoute'

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
    useLocation: vi.fn(() => ({ pathname: '/admin', state: null })),
  }
})

import { useUser, useAuthStore } from '@/hooks/useAuth'
import { getAccessToken } from '@/lib/api'

describe('AdminRoute', () => {
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
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
      )

      expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/login')
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })

    it('redirects to login when not authenticated', () => {
      vi.mocked(getAccessToken).mockReturnValue('some-token')
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
      })

      render(
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
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
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
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
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
      )

      // Should show loading spinner
      expect(container.querySelector('.animate-spin')).toBeInTheDocument()
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })
  })

  describe('non-admin user', () => {
    it('redirects to dashboard when user is not admin', () => {
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
        data: { id: '1', email: 'test@example.com', is_admin: false },
        error: null,
      } as ReturnType<typeof useUser>)

      render(
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
      )

      expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/dashboard')
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })
  })

  describe('admin user', () => {
    it('renders children when user is admin', () => {
      vi.mocked(getAccessToken).mockReturnValue('valid-token')
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: {
          id: '1',
          email: 'admin@example.com',
          is_verified: true,
          is_active: true,
          is_admin: true,
          plan: 'pro',
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
        data: { id: '1', email: 'admin@example.com', is_admin: true },
        error: null,
      } as ReturnType<typeof useUser>)

      render(
        <AdminRoute>
          <div>Admin Content</div>
        </AdminRoute>
      )

      expect(screen.getByText('Admin Content')).toBeInTheDocument()
    })
  })
})
