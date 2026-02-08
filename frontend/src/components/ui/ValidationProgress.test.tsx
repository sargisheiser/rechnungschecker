import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, waitFor } from '@/test/test-utils'
import { ValidationProgress } from './ValidationProgress'

describe('ValidationProgress', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('initial state', () => {
    it('renders all step labels', () => {
      render(<ValidationProgress isValidating={false} />)

      expect(screen.getByText('Hochladen')).toBeInTheDocument()
      expect(screen.getByText('Analysieren')).toBeInTheDocument()
      expect(screen.getByText('Validieren')).toBeInTheDocument()
      expect(screen.getByText('Fertig')).toBeInTheDocument()
    })

    it('shows upload message when not validating', () => {
      render(<ValidationProgress isValidating={false} />)

      expect(screen.getByText('Datei wird hochgeladen...')).toBeInTheDocument()
    })
  })

  describe('validating state', () => {
    it('starts at uploading step when validation begins', () => {
      render(<ValidationProgress isValidating={true} />)

      expect(screen.getByText('Datei wird hochgeladen...')).toBeInTheDocument()
    })

    it('advances to parsing step after delay', async () => {
      render(<ValidationProgress isValidating={true} />)

      // Initial state
      expect(screen.getByText('Datei wird hochgeladen...')).toBeInTheDocument()

      // Advance past uploading duration (800ms)
      await act(async () => {
        vi.advanceTimersByTime(850)
      })

      expect(screen.getByText('Datei wird analysiert...')).toBeInTheDocument()
    })

    it('advances through all steps with enough time', async () => {
      render(<ValidationProgress isValidating={true} />)

      // Advance past uploading (800ms)
      await act(async () => {
        vi.advanceTimersByTime(850)
      })
      expect(screen.getByText('Datei wird analysiert...')).toBeInTheDocument()

      // Advance past parsing (1200ms more)
      await act(async () => {
        vi.advanceTimersByTime(1300)
      })
      expect(screen.getByText('Validierungsregeln werden geprüft...')).toBeInTheDocument()
    })
  })

  describe('completion', () => {
    it('shows completion message when validation stops after starting', async () => {
      const { rerender } = render(<ValidationProgress isValidating={true} />)

      // Advance to parsing step first
      await act(async () => {
        vi.advanceTimersByTime(850)
      })

      expect(screen.getByText('Datei wird analysiert...')).toBeInTheDocument()

      // Stop validating
      rerender(<ValidationProgress isValidating={false} />)

      // Wait for state update
      await act(async () => {
        vi.advanceTimersByTime(50)
      })

      expect(screen.getByText('Validierung abgeschlossen!')).toBeInTheDocument()
    })

    it('calls onComplete callback when validation finishes', async () => {
      const onComplete = vi.fn()
      const { rerender } = render(
        <ValidationProgress isValidating={true} onComplete={onComplete} />
      )

      // Advance to parsing step
      await act(async () => {
        vi.advanceTimersByTime(850)
      })

      // Stop validating
      rerender(<ValidationProgress isValidating={false} onComplete={onComplete} />)

      await act(async () => {
        vi.advanceTimersByTime(50)
      })

      expect(onComplete).toHaveBeenCalled()
    })
  })

  describe('progress bar', () => {
    it('renders progress bar element', () => {
      const { container } = render(<ValidationProgress isValidating={true} />)

      // Progress bar container
      const progressBar = container.querySelector('.bg-gray-200.rounded-full')
      expect(progressBar).toBeInTheDocument()
    })
  })

  describe('step indicators', () => {
    it('shows loader icon for active step', () => {
      const { container } = render(<ValidationProgress isValidating={true} />)

      // Should have spinning loader
      const loader = container.querySelector('.animate-spin')
      expect(loader).toBeInTheDocument()
    })

    it('shows pulse animation for active step', () => {
      const { container } = render(<ValidationProgress isValidating={true} />)

      // Should have ping animation
      const pulse = container.querySelector('.animate-ping')
      expect(pulse).toBeInTheDocument()
    })
  })

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <ValidationProgress isValidating={false} className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })
})
