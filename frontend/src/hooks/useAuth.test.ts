import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import {
  useAuthStore,
  useAuth,
  useUser,
  useLogin,
  useLogout,
  useRegister,
  useForgotPassword,
  useResetPassword,
  useVerifyEmail,
  useResendVerification,
  useUpdateProfile,
  useChangePassword,
  useDeleteAccount,
} from './useAuth'
import type { User } from '@/types'

// Mock the API module
vi.mock('@/lib/api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
    deleteAccount: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
  },
  setAccessToken: vi.fn(),
  setRefreshToken: vi.fn(),
  getAccessToken: vi.fn(),
}))

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  toastMessages: {
    loginSuccess: 'Login erfolgreich',
    loginError: 'Login fehlgeschlagen',
    logoutSuccess: 'Logout erfolgreich',
    updateSuccess: 'Aktualisiert',
    updateError: 'Fehler beim Aktualisieren',
  },
}))

import { authApi, setAccessToken, setRefreshToken, getAccessToken } from '@/lib/api'
import { toast } from '@/lib/toast'

// Test user data
const mockUser: User = {
  id: 'user-1',
  email: 'test@example.com',
  full_name: 'Test User',
  company_name: 'Test Company',
  is_active: true,
  is_verified: true,
  is_admin: false,
  plan: 'pro',
  created_at: '2024-01-01T00:00:00Z',
  email_notifications: true,
  notify_validation_results: true,
  notify_weekly_summary: false,
  notify_marketing: false,
}

// Helper to create a wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset the store state before each test
    useAuthStore.setState({ user: null, isAuthenticated: false })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with null user and not authenticated', () => {
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('setUser', () => {
    it('sets user and marks as authenticated', () => {
      const { setUser } = useAuthStore.getState()

      act(() => {
        setUser(mockUser)
      })

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.isAuthenticated).toBe(true)
    })

    it('clears user and marks as not authenticated when set to null', () => {
      // First set a user
      useAuthStore.setState({ user: mockUser, isAuthenticated: true })

      const { setUser } = useAuthStore.getState()

      act(() => {
        setUser(null)
      })

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('logout', () => {
    it('clears tokens and resets state', () => {
      // Set up authenticated state
      useAuthStore.setState({ user: mockUser, isAuthenticated: true })

      const { logout } = useAuthStore.getState()

      act(() => {
        logout()
      })

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(setAccessToken).toHaveBeenCalledWith(null)
      expect(setRefreshToken).toHaveBeenCalledWith(null)
    })
  })
})

describe('useAuth', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false })
  })

  it('returns current auth state', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true })

    const { result } = renderHook(() => useAuth())

    expect(result.current.user).toEqual(mockUser)
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('updates when store changes', () => {
    const { result } = renderHook(() => useAuth())

    expect(result.current.isAuthenticated).toBe(false)

    act(() => {
      useAuthStore.getState().setUser(mockUser)
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.user).toEqual(mockUser)
  })
})

describe('useUser', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false })
    vi.clearAllMocks()
  })

  it('does not fetch when no access token', () => {
    vi.mocked(getAccessToken).mockReturnValue(null)

    const { result } = renderHook(() => useUser(), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(false)
    expect(authApi.getMe).not.toHaveBeenCalled()
  })

  it('fetches user when access token exists', async () => {
    vi.mocked(getAccessToken).mockReturnValue('valid-token')
    vi.mocked(authApi.getMe).mockResolvedValue(mockUser)

    const { result } = renderHook(() => useUser(), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.getMe).toHaveBeenCalled()
    expect(result.current.data).toEqual(mockUser)
  })

  it('updates store when user is fetched', async () => {
    vi.mocked(getAccessToken).mockReturnValue('valid-token')
    vi.mocked(authApi.getMe).mockResolvedValue(mockUser)

    renderHook(() => useUser(), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(useAuthStore.getState().user).toEqual(mockUser)
    })

    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })
})

describe('useLogin', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false })
    vi.clearAllMocks()
  })

  it('logs in user and stores tokens', async () => {
    const tokens = { access_token: 'access-123', refresh_token: 'refresh-123', token_type: 'bearer' }
    vi.mocked(authApi.login).mockResolvedValue(tokens)
    vi.mocked(authApi.getMe).mockResolvedValue(mockUser)

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', password: 'password123' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.login).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' })
    expect(setAccessToken).toHaveBeenCalledWith('access-123')
    expect(setRefreshToken).toHaveBeenCalledWith('refresh-123')
    expect(authApi.getMe).toHaveBeenCalled()
  })

  it('shows success toast on login', async () => {
    const tokens = { access_token: 'access-123', refresh_token: 'refresh-123', token_type: 'bearer' }
    vi.mocked(authApi.login).mockResolvedValue(tokens)
    vi.mocked(authApi.getMe).mockResolvedValue(mockUser)

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', password: 'password123' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(toast.success).toHaveBeenCalled()
  })

  it('shows error toast on login failure', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', password: 'wrong' })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(toast.error).toHaveBeenCalled()
  })
})

describe('useLogout', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true })
    vi.clearAllMocks()
  })

  it('calls logout API and clears state', async () => {
    vi.mocked(authApi.logout).mockResolvedValue()

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.logout).toHaveBeenCalled()
    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('clears state even if API call fails', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // State should still be cleared
    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('shows success toast on logout', async () => {
    vi.mocked(authApi.logout).mockResolvedValue()

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(toast.success).toHaveBeenCalled()
  })
})

describe('useRegister', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls register API with user data', async () => {
    vi.mocked(authApi.register).mockResolvedValue(mockUser)

    const { result } = renderHook(() => useRegister(), { wrapper: createWrapper() })

    const registerData = {
      email: 'new@example.com',
      password: 'password123',
      full_name: 'New User',
    }

    await act(async () => {
      result.current.mutate(registerData)
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.register).toHaveBeenCalledWith(registerData)
  })
})

describe('useForgotPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls forgot password API with email', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValue()

    const { result } = renderHook(() => useForgotPassword(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate('test@example.com')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.forgotPassword).toHaveBeenCalledWith('test@example.com')
  })
})

describe('useResetPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls reset password API with token and new password', async () => {
    vi.mocked(authApi.resetPassword).mockResolvedValue()

    const { result } = renderHook(() => useResetPassword(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ token: 'reset-token', password: 'newpassword123' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.resetPassword).toHaveBeenCalledWith('reset-token', 'newpassword123')
  })
})

describe('useVerifyEmail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls verify email API with email and code', async () => {
    vi.mocked(authApi.verifyEmail).mockResolvedValue({ message: 'Email verified' })

    const { result } = renderHook(() => useVerifyEmail(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', code: '123456' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.verifyEmail).toHaveBeenCalledWith({ email: 'test@example.com', code: '123456' })
  })
})

describe('useResendVerification', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls resend verification API with email', async () => {
    vi.mocked(authApi.resendVerification).mockResolvedValue({ message: 'Code sent' })

    const { result } = renderHook(() => useResendVerification(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate('test@example.com')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.resendVerification).toHaveBeenCalledWith('test@example.com')
  })
})

describe('useUpdateProfile', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true })
    vi.clearAllMocks()
  })

  it('updates profile and refreshes user data', async () => {
    const updatedUser = { ...mockUser, full_name: 'Updated Name' }
    vi.mocked(authApi.updateProfile).mockResolvedValue(updatedUser)

    const { result } = renderHook(() => useUpdateProfile(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ full_name: 'Updated Name' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.updateProfile).toHaveBeenCalledWith({ full_name: 'Updated Name' })
    expect(useAuthStore.getState().user?.full_name).toBe('Updated Name')
  })

  it('shows success toast on profile update', async () => {
    vi.mocked(authApi.updateProfile).mockResolvedValue(mockUser)

    const { result } = renderHook(() => useUpdateProfile(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ full_name: 'New Name' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(toast.success).toHaveBeenCalled()
  })

  it('shows error toast on profile update failure', async () => {
    vi.mocked(authApi.updateProfile).mockRejectedValue(new Error('Update failed'))

    const { result } = renderHook(() => useUpdateProfile(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ full_name: 'New Name' })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(toast.error).toHaveBeenCalled()
  })
})

describe('useChangePassword', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls change password API', async () => {
    vi.mocked(authApi.changePassword).mockResolvedValue()

    const { result } = renderHook(() => useChangePassword(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ currentPassword: 'oldpass', newPassword: 'newpass' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.changePassword).toHaveBeenCalledWith('oldpass', 'newpass')
  })

  it('shows success toast on password change', async () => {
    vi.mocked(authApi.changePassword).mockResolvedValue()

    const { result } = renderHook(() => useChangePassword(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ currentPassword: 'old', newPassword: 'new' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(toast.success).toHaveBeenCalled()
  })

  it('shows error toast on password change failure', async () => {
    vi.mocked(authApi.changePassword).mockRejectedValue(new Error('Wrong password'))

    const { result } = renderHook(() => useChangePassword(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate({ currentPassword: 'wrong', newPassword: 'new' })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(toast.error).toHaveBeenCalled()
  })
})

describe('useDeleteAccount', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true })
    vi.clearAllMocks()
  })

  it('deletes account and logs out user', async () => {
    vi.mocked(authApi.deleteAccount).mockResolvedValue()

    const { result } = renderHook(() => useDeleteAccount(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(authApi.deleteAccount).toHaveBeenCalled()
    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
