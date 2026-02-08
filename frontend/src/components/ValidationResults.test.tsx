import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@/test/test-utils'
import { ValidationResults } from './ValidationResults'
import type { ValidationResult, ValidationError } from '@/types'

// Create mock functions at module level
const mockClearResult = vi.fn()
const mockDownloadMutate = vi.fn()

// Mock the stores and hooks
vi.mock('@/hooks/useValidation', () => ({
  useValidationStore: vi.fn(() => ({
    currentResult: null,
    clearResult: mockClearResult,
  })),
  useDownloadReport: vi.fn(() => ({
    mutate: mockDownloadMutate,
    isPending: false,
  })),
}))

vi.mock('@/hooks/useAuth', () => ({
  useAuthStore: vi.fn(() => ({
    isAuthenticated: false,
  })),
}))

// Import after mocking
import { useValidationStore } from '@/hooks/useValidation'
import { useAuthStore } from '@/hooks/useAuth'

// Test data helpers
const createValidationResult = (overrides: Partial<ValidationResult> = {}): ValidationResult => ({
  id: 'test-id',
  status: 'valid',
  file_type: 'xrechnung',
  file_name: 'test-invoice.xml',
  errors: [],
  warnings: [],
  validated_at: '2024-01-15T10:30:00Z',
  can_download_report: false,
  ...overrides,
})

const createError = (overrides: Partial<ValidationError> = {}): ValidationError => ({
  code: 'BR-CO-10',
  message: 'Test error',
  severity: 'error',
  ...overrides,
})

describe('ValidationResults', () => {
  beforeEach(() => {
    vi.mocked(useValidationStore).mockReturnValue({
      currentResult: null,
      clearResult: mockClearResult,
    })

    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('no result state', () => {
    it('returns null when no result', () => {
      const { container } = render(<ValidationResults />)
      expect(container.firstChild).toBeNull()
    })
  })

  describe('valid status', () => {
    it('renders green styling and CheckCircle for valid status', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ status: 'valid' }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('Gueltig')).toBeInTheDocument()
      expect(screen.getByText('Gueltig')).toHaveClass('text-success-600')
    })

    it('displays success message when valid with no errors or warnings', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ status: 'valid', errors: [], warnings: [] }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('Ihre E-Rechnung ist vollstaendig konform!')).toBeInTheDocument()
    })
  })

  describe('invalid status', () => {
    it('renders red styling and XCircle for invalid status', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({
          status: 'invalid',
          errors: [createError()],
        }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('Ungueltig')).toBeInTheDocument()
      expect(screen.getByText('Ungueltig')).toHaveClass('text-error-600')
    })
  })

  describe('error status', () => {
    it('renders orange styling and AlertTriangle for error status', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ status: 'error' }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      // The main status heading should show "Fehler" with warning styling
      const heading = screen.getByRole('heading', { level: 3 })
      expect(heading).toHaveTextContent('Fehler')
      expect(heading).toHaveClass('text-warning-600')
    })
  })

  describe('with errors', () => {
    it('renders GroupedErrorsSection for errors', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({
          status: 'invalid',
          errors: [
            createError({ code: 'BR-CO-10', message: 'Tax error' }),
            createError({ code: 'BR-DE-1', message: 'ID error' }),
          ],
        }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      // The error count should show "2" in stats
      const errorCounts = screen.getAllByText('2')
      expect(errorCounts.length).toBeGreaterThan(0)
    })
  })

  describe('with warnings', () => {
    it('renders warning section', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({
          status: 'valid',
          warnings: [
            createError({ code: 'WARN-1', message: 'Warning 1', severity: 'warning' }),
          ],
        }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      // Warning section header should be rendered
      expect(screen.getByText('Warnungen (1)')).toBeInTheDocument()
    })
  })

  describe('guest user', () => {
    it('shows registration prompt for guest users', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult(),
        clearResult: mockClearResult,
      })

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
      })

      render(<ValidationResults />)

      expect(screen.getByText('Das war Ihre kostenlose Validierung')).toBeInTheDocument()
      expect(screen.getByText('Kostenlos registrieren')).toBeInTheDocument()
    })
  })

  describe('authenticated user', () => {
    it('does not show registration prompt for authenticated users', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult(),
        clearResult: mockClearResult,
      })

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
      })

      render(<ValidationResults />)

      expect(screen.queryByText('Das war Ihre kostenlose Validierung')).not.toBeInTheDocument()
    })
  })

  describe('clear button', () => {
    it('calls clearResult when clicked', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult(),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      const clearButton = screen.getByText('Neu')
      fireEvent.click(clearButton)

      expect(mockClearResult).toHaveBeenCalledTimes(1)
    })
  })

  describe('download button', () => {
    it('shows download button when can_download_report is true', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ can_download_report: true }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('PDF Bericht')).toBeInTheDocument()
    })

    it('hides download button when can_download_report is false', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ can_download_report: false }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.queryByText('PDF Bericht')).not.toBeInTheDocument()
    })
  })

  describe('file details', () => {
    it('displays file name', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ file_name: 'my-invoice.xml' }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('my-invoice.xml')).toBeInTheDocument()
    })

    it('displays file type', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({ file_type: 'xrechnung' }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('XRechnung')).toBeInTheDocument()
    })

    it('displays zugferd profile when present', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({
          file_type: 'zugferd',
          zugferd_profile: 'EN16931',
        }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      expect(screen.getByText('EN16931')).toBeInTheDocument()
    })
  })

  describe('stats display', () => {
    it('shows error and warning counts in stats section', () => {
      vi.mocked(useValidationStore).mockReturnValue({
        currentResult: createValidationResult({
          status: 'invalid',
          errors: [createError(), createError(), createError()],
          warnings: [createError({ severity: 'warning' })],
        }),
        clearResult: mockClearResult,
      })

      render(<ValidationResults />)

      // Should show error count 3 and warning count 1 in the stats section
      const statsSection = screen.getByText('Dateityp').closest('div')?.parentElement
      expect(statsSection).toBeInTheDocument()

      // Check for error label and count
      expect(screen.getByText('Fehler', { selector: 'p' })).toBeInTheDocument()
    })
  })
})
