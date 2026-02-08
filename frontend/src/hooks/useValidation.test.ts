import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import {
  useValidationStore,
  useValidate,
  useValidationHistory,
  useValidationResult,
  useDownloadReport,
} from './useValidation'
import { useAuthStore } from './useAuth'
import type { ValidationResult } from '@/types'

// Mock the API module
vi.mock('@/lib/api', () => ({
  validationApi: {
    validate: vi.fn(),
    validateGuest: vi.fn(),
    getHistory: vi.fn(),
    getResult: vi.fn(),
    downloadReport: vi.fn(),
  },
}))

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
  toastMessages: {
    validationSuccess: 'Validierung erfolgreich',
    validationWarning: 'Validierung mit Warnungen',
    validationError: 'Validierung fehlgeschlagen',
    downloadSuccess: 'Download erfolgreich',
    downloadError: 'Download fehlgeschlagen',
  },
}))

// Mock utils
vi.mock('@/lib/utils', () => ({
  getGuestId: vi.fn(),
  cn: (...args: unknown[]) => args.filter(Boolean).join(' '),
}))

import { validationApi } from '@/lib/api'
import { toast } from '@/lib/toast'
import { getGuestId } from '@/lib/utils'

// Mock validation result
const mockValidResult: ValidationResult = {
  id: 'val-1',
  status: 'valid',
  file_type: 'xrechnung',
  file_name: 'invoice.xml',
  errors: [],
  warnings: [],
  validated_at: '2024-01-15T10:30:00Z',
  can_download_report: true,
}

const mockInvalidResult: ValidationResult = {
  id: 'val-2',
  status: 'invalid',
  file_type: 'xrechnung',
  file_name: 'invoice.xml',
  errors: [
    { code: 'BR-CO-10', message: 'Tax error', severity: 'error' },
    { code: 'BR-DE-1', message: 'ID error', severity: 'error' },
  ],
  warnings: [],
  validated_at: '2024-01-15T10:30:00Z',
  can_download_report: true,
}

const mockWarningResult: ValidationResult = {
  id: 'val-3',
  status: 'warning' as ValidationResult['status'], // Non-valid status to trigger warning toast path
  file_type: 'xrechnung',
  file_name: 'invoice.xml',
  errors: [],
  warnings: [
    { code: 'WARN-1', message: 'Minor issue', severity: 'warning' },
  ],
  validated_at: '2024-01-15T10:30:00Z',
  can_download_report: true,
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

// Helper to create a mock file
function createMockFile(name = 'invoice.xml'): File {
  return new File(['<Invoice></Invoice>'], name, { type: 'application/xml' })
}

describe('useValidationStore', () => {
  beforeEach(() => {
    // Reset the store state before each test
    useValidationStore.setState({
      currentResult: null,
      isValidating: false,
      guestLimitReached: false,
    })
  })

  describe('initial state', () => {
    it('starts with null result and not validating', () => {
      const state = useValidationStore.getState()
      expect(state.currentResult).toBeNull()
      expect(state.isValidating).toBe(false)
      expect(state.guestLimitReached).toBe(false)
    })
  })

  describe('setResult', () => {
    it('sets result and stops validating', () => {
      const { setResult, setValidating } = useValidationStore.getState()

      // Start validating first
      act(() => {
        setValidating(true)
      })
      expect(useValidationStore.getState().isValidating).toBe(true)

      // Set result
      act(() => {
        setResult(mockValidResult)
      })

      const state = useValidationStore.getState()
      expect(state.currentResult).toEqual(mockValidResult)
      expect(state.isValidating).toBe(false)
    })

    it('clears result when set to null', () => {
      // First set a result
      useValidationStore.setState({ currentResult: mockValidResult })

      const { setResult } = useValidationStore.getState()

      act(() => {
        setResult(null)
      })

      expect(useValidationStore.getState().currentResult).toBeNull()
    })
  })

  describe('setValidating', () => {
    it('sets validating state', () => {
      const { setValidating } = useValidationStore.getState()

      act(() => {
        setValidating(true)
      })
      expect(useValidationStore.getState().isValidating).toBe(true)

      act(() => {
        setValidating(false)
      })
      expect(useValidationStore.getState().isValidating).toBe(false)
    })
  })

  describe('setGuestLimitReached', () => {
    it('sets guest limit reached state', () => {
      const { setGuestLimitReached } = useValidationStore.getState()

      act(() => {
        setGuestLimitReached(true)
      })
      expect(useValidationStore.getState().guestLimitReached).toBe(true)

      act(() => {
        setGuestLimitReached(false)
      })
      expect(useValidationStore.getState().guestLimitReached).toBe(false)
    })
  })

  describe('clearResult', () => {
    it('clears result and guest limit reached', () => {
      // Set up state
      useValidationStore.setState({
        currentResult: mockValidResult,
        guestLimitReached: true,
      })

      const { clearResult } = useValidationStore.getState()

      act(() => {
        clearResult()
      })

      const state = useValidationStore.getState()
      expect(state.currentResult).toBeNull()
      expect(state.guestLimitReached).toBe(false)
    })
  })
})

describe('useValidate', () => {
  beforeEach(() => {
    useValidationStore.setState({
      currentResult: null,
      isValidating: false,
      guestLimitReached: false,
    })
    useAuthStore.setState({ user: null, isAuthenticated: false })
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('authenticated user', () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com' } as any,
        isAuthenticated: true,
      })
    })

    it('calls validate API for authenticated users', async () => {
      vi.mocked(validationApi.validate).mockResolvedValue(mockValidResult)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })
      const file = createMockFile()

      await act(async () => {
        result.current.mutate(file)
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(validationApi.validate).toHaveBeenCalledWith(file)
      expect(validationApi.validateGuest).not.toHaveBeenCalled()
    })

    it('sets validating state during validation', async () => {
      vi.mocked(validationApi.validate).mockResolvedValue(mockValidResult)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Should stop validating after success
      expect(useValidationStore.getState().isValidating).toBe(false)
    })

    it('shows success toast for valid result', async () => {
      vi.mocked(validationApi.validate).mockResolvedValue(mockValidResult)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(toast.success).toHaveBeenCalled()
    })

    it('shows error toast for invalid result', async () => {
      vi.mocked(validationApi.validate).mockResolvedValue(mockInvalidResult)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(toast.error).toHaveBeenCalled()
    })

    it('shows warning toast for result with warnings only', async () => {
      vi.mocked(validationApi.validate).mockResolvedValue(mockWarningResult)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(toast.warning).toHaveBeenCalled()
    })
  })

  describe('guest user', () => {
    beforeEach(() => {
      useAuthStore.setState({ user: null, isAuthenticated: false })
    })

    it('calls validateGuest API for guest users', async () => {
      vi.mocked(getGuestId).mockReturnValue('guest-123')
      vi.mocked(validationApi.validateGuest).mockResolvedValue({
        ...mockValidResult,
        guest_id: 'guest-123',
      })

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })
      const file = createMockFile()

      await act(async () => {
        result.current.mutate(file)
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(validationApi.validateGuest).toHaveBeenCalledWith(file, 'guest-123')
      expect(validationApi.validate).not.toHaveBeenCalled()
    })

    it('stores guest_id in localStorage when returned', async () => {
      vi.mocked(getGuestId).mockReturnValue(undefined)
      vi.mocked(validationApi.validateGuest).mockResolvedValue({
        ...mockValidResult,
        guest_id: 'new-guest-456',
      } as any)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Verify the guest_id was stored
      expect(localStorage.getItem('guest_id')).toBe('new-guest-456')
    })

    it('sets guestLimitReached on 403 with GUEST_LIMIT_REACHED code', async () => {
      const error = {
        response: {
          status: 403,
          data: { detail: { code: 'GUEST_LIMIT_REACHED' } },
        },
      }
      vi.mocked(validationApi.validateGuest).mockRejectedValue(error)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(useValidationStore.getState().guestLimitReached).toBe(true)
    })

    it('does not set guestLimitReached for other errors', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Server error' },
        },
      }
      vi.mocked(validationApi.validateGuest).mockRejectedValue(error)

      const { result } = renderHook(() => useValidate(), { wrapper: createWrapper() })

      await act(async () => {
        result.current.mutate(createMockFile())
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(useValidationStore.getState().guestLimitReached).toBe(false)
    })
  })
})

describe('useValidationHistory', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false })
    vi.clearAllMocks()
  })

  it('does not fetch when not authenticated', () => {
    useAuthStore.setState({ isAuthenticated: false })

    const { result } = renderHook(() => useValidationHistory(), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(false)
    expect(validationApi.getHistory).not.toHaveBeenCalled()
  })

  it('fetches history when authenticated', async () => {
    useAuthStore.setState({ isAuthenticated: true })
    vi.mocked(validationApi.getHistory).mockResolvedValue({
      items: [mockValidResult],
      total: 1,
      page: 1,
      page_size: 10,
    })

    const { result } = renderHook(() => useValidationHistory(1, 10), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(validationApi.getHistory).toHaveBeenCalledWith(1, 10)
  })

  it('uses provided page and limit', async () => {
    useAuthStore.setState({ isAuthenticated: true })
    vi.mocked(validationApi.getHistory).mockResolvedValue({
      items: [],
      total: 0,
      page: 2,
      page_size: 20,
    })

    const { result } = renderHook(() => useValidationHistory(2, 20), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(validationApi.getHistory).toHaveBeenCalledWith(2, 20)
  })
})

describe('useValidationResult', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not fetch when id is empty', () => {
    const { result } = renderHook(() => useValidationResult(''), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(false)
    expect(validationApi.getResult).not.toHaveBeenCalled()
  })

  it('fetches result when id is provided', async () => {
    vi.mocked(validationApi.getResult).mockResolvedValue(mockValidResult)

    const { result } = renderHook(() => useValidationResult('val-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(validationApi.getResult).toHaveBeenCalledWith('val-1')
    expect(result.current.data).toEqual(mockValidResult)
  })
})

describe('useDownloadReport', () => {
  let originalCreateObjectURL: typeof URL.createObjectURL
  let originalRevokeObjectURL: typeof URL.revokeObjectURL

  beforeEach(() => {
    vi.clearAllMocks()
    // Save original methods
    originalCreateObjectURL = URL.createObjectURL
    originalRevokeObjectURL = URL.revokeObjectURL
    // Mock URL methods
    URL.createObjectURL = vi.fn().mockReturnValue('blob:mock-url')
    URL.revokeObjectURL = vi.fn()
  })

  afterEach(() => {
    // Restore original methods
    URL.createObjectURL = originalCreateObjectURL
    URL.revokeObjectURL = originalRevokeObjectURL
  })

  it('calls downloadReport API with correct id', async () => {
    const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' })
    vi.mocked(validationApi.downloadReport).mockResolvedValue(mockBlob)

    const { result } = renderHook(() => useDownloadReport(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate('val-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(validationApi.downloadReport).toHaveBeenCalledWith('val-1')
  })

  it('creates blob URL for download', async () => {
    const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' })
    vi.mocked(validationApi.downloadReport).mockResolvedValue(mockBlob)

    const { result } = renderHook(() => useDownloadReport(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate('val-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(URL.createObjectURL).toHaveBeenCalledWith(mockBlob)
    expect(URL.revokeObjectURL).toHaveBeenCalled()
  })

  it('shows success toast on successful download', async () => {
    const mockBlob = new Blob(['PDF'], { type: 'application/pdf' })
    vi.mocked(validationApi.downloadReport).mockResolvedValue(mockBlob)

    const { result } = renderHook(() => useDownloadReport(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate('val-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(toast.success).toHaveBeenCalled()
  })

  it('shows error toast on download failure', async () => {
    vi.mocked(validationApi.downloadReport).mockRejectedValue(new Error('Download failed'))

    const { result } = renderHook(() => useDownloadReport(), { wrapper: createWrapper() })

    await act(async () => {
      result.current.mutate('val-1')
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(toast.error).toHaveBeenCalled()
  })
})
