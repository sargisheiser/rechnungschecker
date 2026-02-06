import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { Alert } from './Alert'

describe('Alert', () => {
  it('renders children content', () => {
    render(<Alert variant="info">Test message</Alert>)
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('renders with title when provided', () => {
    render(
      <Alert variant="info" title="Alert Title">
        Test message
      </Alert>
    )
    expect(screen.getByText('Alert Title')).toBeInTheDocument()
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('has correct role for accessibility', () => {
    render(<Alert variant="info">Test message</Alert>)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  describe('variants', () => {
    it('renders success variant', () => {
      render(<Alert variant="success">Success message</Alert>)
      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass('bg-success-50')
    })

    it('renders warning variant', () => {
      render(<Alert variant="warning">Warning message</Alert>)
      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass('bg-warning-50')
    })

    it('renders error variant', () => {
      render(<Alert variant="error">Error message</Alert>)
      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass('bg-error-50')
    })

    it('renders info variant', () => {
      render(<Alert variant="info">Info message</Alert>)
      const alert = screen.getByRole('alert')
      expect(alert).toHaveClass('bg-primary-50')
    })
  })

  describe('dismiss button', () => {
    it('does not show dismiss button when onDismiss is not provided', () => {
      render(<Alert variant="info">Test message</Alert>)
      expect(screen.queryByLabelText('Schliessen')).not.toBeInTheDocument()
    })

    it('shows dismiss button when onDismiss is provided', () => {
      const onDismiss = vi.fn()
      render(
        <Alert variant="info" onDismiss={onDismiss}>
          Test message
        </Alert>
      )
      expect(screen.getByLabelText('Schliessen')).toBeInTheDocument()
    })

    it('calls onDismiss when dismiss button is clicked', async () => {
      const onDismiss = vi.fn()
      render(
        <Alert variant="info" onDismiss={onDismiss}>
          Test message
        </Alert>
      )

      const dismissButton = screen.getByLabelText('Schliessen')
      dismissButton.click()

      expect(onDismiss).toHaveBeenCalledTimes(1)
    })
  })

  it('applies custom className', () => {
    render(
      <Alert variant="info" className="custom-class">
        Test message
      </Alert>
    )
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('custom-class')
  })
})
