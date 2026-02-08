import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import {
  GroupedErrorsSection,
  groupErrorsByCode,
  type GroupableError,
} from './GroupedErrors'

// Test data helpers
const createError = (overrides: Partial<GroupableError> = {}): GroupableError => ({
  code: 'BR-CO-10',
  message: 'Test error message',
  message_de: 'Testfehlermeldung',
  location: '/Invoice/TaxTotal',
  severity: 'error',
  ...overrides,
})

describe('groupErrorsByCode', () => {
  it('groups errors by code', () => {
    const errors: GroupableError[] = [
      createError({ code: 'BR-CO-10', location: 'line 1' }),
      createError({ code: 'BR-CO-10', location: 'line 2' }),
      createError({ code: 'BR-DE-1', location: 'line 3' }),
    ]

    const grouped = groupErrorsByCode(errors)

    expect(grouped).toHaveLength(2)
    expect(grouped[0].code).toBe('BR-CO-10')
    expect(grouped[0].count).toBe(2)
    expect(grouped[1].code).toBe('BR-DE-1')
    expect(grouped[1].count).toBe(1)
  })

  it('falls back to message_de when code is empty', () => {
    const errors: GroupableError[] = [
      createError({ code: '', message_de: 'Gleiche Nachricht' }),
      createError({ code: '', message_de: 'Gleiche Nachricht' }),
      createError({ code: '', message_de: 'Andere Nachricht' }),
    ]

    const grouped = groupErrorsByCode(errors)

    expect(grouped).toHaveLength(2)
    expect(grouped[0].count).toBe(2)
    expect(grouped[1].count).toBe(1)
  })

  it('falls back to message when code and message_de are empty', () => {
    const errors: GroupableError[] = [
      createError({ code: '', message_de: '', message: 'Same message' }),
      createError({ code: '', message_de: '', message: 'Same message' }),
    ]

    const grouped = groupErrorsByCode(errors)

    expect(grouped).toHaveLength(1)
    expect(grouped[0].count).toBe(2)
  })

  it('returns empty array for empty input', () => {
    const grouped = groupErrorsByCode([])
    expect(grouped).toHaveLength(0)
  })

  it('extracts line numbers from "line X" format', () => {
    const errors: GroupableError[] = [
      createError({ code: 'TEST', location: 'line 5' }),
      createError({ code: 'TEST', location: 'Error at line: 10' }),
    ]

    const grouped = groupErrorsByCode(errors)

    expect(grouped[0].locations).toContain('Zeile 5')
    expect(grouped[0].locations).toContain('Zeile 10')
  })

  it('extracts line numbers from "[X]" format', () => {
    const errors: GroupableError[] = [
      createError({ code: 'TEST', location: 'InvoiceLine[3]' }),
      createError({ code: 'TEST', location: 'Something[7]' }),
    ]

    const grouped = groupErrorsByCode(errors)

    expect(grouped[0].locations).toContain('Zeile 3')
    expect(grouped[0].locations).toContain('Zeile 7')
  })
})

describe('GroupedErrorsSection', () => {
  describe('error type rendering', () => {
    it('renders with red styling for error type', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[createError()]}
          type="error"
        />
      )

      const container = screen.getByText('Fehler (1)').closest('div')
      expect(container).toBeInTheDocument()
      // XCircle icon should have error color
      const icon = container?.querySelector('svg')
      expect(icon).toHaveClass('text-error-500')
    })

    it('renders with amber styling for warning type', () => {
      render(
        <GroupedErrorsSection
          title="Warnungen"
          errors={[createError()]}
          type="warning"
        />
      )

      const container = screen.getByText('Warnungen (1)').closest('div')
      expect(container).toBeInTheDocument()
      // AlertTriangle icon should have warning color
      const icon = container?.querySelector('svg')
      expect(icon).toHaveClass('text-warning-500')
    })
  })

  describe('single error display', () => {
    it('renders single error without grouping', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[createError({ code: 'BR-CO-10' })]}
          type="error"
        />
      )

      // Should show error code badge
      expect(screen.getByText('BR-CO-10')).toBeInTheDocument()
      // Should not show count badge since it's a single error
      expect(screen.queryByText(/× betroffen/)).not.toBeInTheDocument()
    })

    it('displays known error explanation for BR-CO-10', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[createError({ code: 'BR-CO-10' })]}
          type="error"
        />
      )

      expect(screen.getByText('Steuersumme stimmt nicht überein')).toBeInTheDocument()
    })

    it('displays fix suggestion for known error codes', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[createError({ code: 'BR-CO-10' })]}
          type="error"
        />
      )

      expect(screen.getByText(/Prüfen Sie: Nettosumme/)).toBeInTheDocument()
    })

    it('shows raw message for unknown error codes', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[createError({ code: 'UNKNOWN-CODE', message_de: 'Unbekannte Fehlermeldung' })]}
          type="error"
        />
      )

      expect(screen.getByText('Unbekannte Fehlermeldung')).toBeInTheDocument()
    })
  })

  describe('grouped errors display', () => {
    it('shows count badge for multiple errors with same code', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'BR-CO-10', location: 'line 1' }),
            createError({ code: 'BR-CO-10', location: 'line 2' }),
            createError({ code: 'BR-CO-10', location: 'line 3' }),
          ]}
          type="error"
        />
      )

      expect(screen.getByText('3× betroffen')).toBeInTheDocument()
    })

    it('shows group count when there are duplicates', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'BR-CO-10' }),
            createError({ code: 'BR-CO-10' }),
            createError({ code: 'BR-DE-1' }),
          ]}
          type="error"
        />
      )

      expect(screen.getByText('2 Typen')).toBeInTheDocument()
    })
  })

  describe('location extraction', () => {
    it('displays extracted line numbers', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'TEST', location: 'line 5' }),
            createError({ code: 'TEST', location: 'line 10' }),
          ]}
          type="error"
        />
      )

      expect(screen.getByText('Zeile 5')).toBeInTheDocument()
      expect(screen.getByText('Zeile 10')).toBeInTheDocument()
    })

    it('extracts line from bracket notation', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'TEST', location: 'InvoiceLine[3]' }),
            createError({ code: 'TEST', location: 'InvoiceLine[7]' }),
          ]}
          type="error"
        />
      )

      expect(screen.getByText('Zeile 3')).toBeInTheDocument()
      expect(screen.getByText('Zeile 7')).toBeInTheDocument()
    })
  })

  describe('expansion toggle', () => {
    it('shows expand button for grouped errors', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'TEST', location: 'line 1' }),
            createError({ code: 'TEST', location: 'line 2' }),
          ]}
          type="error"
        />
      )

      expect(screen.getByText(/Alle 2 Vorkommen anzeigen/)).toBeInTheDocument()
    })

    it('toggles expansion on click', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'TEST', location: 'line 1', message_de: 'Detail 1' }),
            createError({ code: 'TEST', location: 'line 2', message_de: 'Detail 2' }),
          ]}
          type="error"
        />
      )

      // Initially expanded content is not visible
      expect(screen.queryByText('Einzelne Vorkommen:')).not.toBeInTheDocument()

      // Click expand button
      fireEvent.click(screen.getByText(/Alle 2 Vorkommen anzeigen/))

      // Now expanded content should be visible
      expect(screen.getByText('Einzelne Vorkommen:')).toBeInTheDocument()
      expect(screen.getByText('Weniger anzeigen')).toBeInTheDocument()

      // Click again to collapse
      fireEvent.click(screen.getByText('Weniger anzeigen'))

      expect(screen.queryByText('Einzelne Vorkommen:')).not.toBeInTheDocument()
    })
  })

  describe('empty errors array', () => {
    it('renders nothing for empty errors array', () => {
      const { container } = render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[]}
          type="error"
        />
      )

      // Should still render the title but with count 0
      expect(screen.getByText('Fehler (0)')).toBeInTheDocument()
      // But no error items
      expect(container.querySelectorAll('.rounded-lg.border')).toHaveLength(0)
    })
  })

  describe('truncation for many locations', () => {
    it('shows "+X weitere" when more than 5 locations', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'TEST', location: 'line 1' }),
            createError({ code: 'TEST', location: 'line 2' }),
            createError({ code: 'TEST', location: 'line 3' }),
            createError({ code: 'TEST', location: 'line 4' }),
            createError({ code: 'TEST', location: 'line 5' }),
            createError({ code: 'TEST', location: 'line 6' }),
            createError({ code: 'TEST', location: 'line 7' }),
            createError({ code: 'TEST', location: 'line 8' }),
          ]}
          type="error"
        />
      )

      // Should show first 5 locations
      expect(screen.getByText('Zeile 1')).toBeInTheDocument()
      expect(screen.getByText('Zeile 5')).toBeInTheDocument()

      // Should show truncation indicator
      expect(screen.getByText('+3 weitere')).toBeInTheDocument()
    })

    it('shows all locations when expanded', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[
            createError({ code: 'TEST', location: 'line 1' }),
            createError({ code: 'TEST', location: 'line 2' }),
            createError({ code: 'TEST', location: 'line 3' }),
            createError({ code: 'TEST', location: 'line 4' }),
            createError({ code: 'TEST', location: 'line 5' }),
            createError({ code: 'TEST', location: 'line 6' }),
          ]}
          type="error"
        />
      )

      // Expand
      fireEvent.click(screen.getByText(/Alle 6 Vorkommen anzeigen/))

      // All locations should now be visible
      expect(screen.getByText('Zeile 6')).toBeInTheDocument()
      expect(screen.queryByText(/weitere/)).not.toBeInTheDocument()
    })
  })

  describe('error code normalization', () => {
    it('removes brackets from error codes in display', () => {
      render(
        <GroupedErrorsSection
          title="Fehler"
          errors={[createError({ code: '[BR-CO-10]' })]}
          type="error"
        />
      )

      // Should show normalized code without brackets
      expect(screen.getByText('BR-CO-10')).toBeInTheDocument()
      expect(screen.queryByText('[BR-CO-10]')).not.toBeInTheDocument()
    })
  })
})
