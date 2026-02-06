import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { ConfirmDialog, confirmDialogPresets } from './ConfirmDialog'

describe('ConfirmDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    title: 'Test Title',
    message: 'Test message',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Reset body overflow
    document.body.style.overflow = ''
  })

  it('renders nothing when not open', () => {
    render(<ConfirmDialog {...defaultProps} isOpen={false} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders dialog when open', () => {
    render(<ConfirmDialog {...defaultProps} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('has correct aria attributes', () => {
    render(<ConfirmDialog {...defaultProps} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-labelledby', 'confirm-dialog-title')
  })

  it('calls onClose when cancel button is clicked', () => {
    render(<ConfirmDialog {...defaultProps} />)
    fireEvent.click(screen.getByText('Abbrechen'))
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onConfirm when confirm button is clicked', () => {
    render(<ConfirmDialog {...defaultProps} />)
    fireEvent.click(screen.getByText('Bestätigen'))
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', () => {
    render(<ConfirmDialog {...defaultProps} />)
    const backdrop = document.querySelector('[aria-hidden="true"]')
    fireEvent.click(backdrop!)
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when Escape key is pressed', () => {
    render(<ConfirmDialog {...defaultProps} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('uses custom button labels', () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        confirmLabel="Delete"
        cancelLabel="Keep"
      />
    )
    expect(screen.getByText('Delete')).toBeInTheDocument()
    expect(screen.getByText('Keep')).toBeInTheDocument()
  })

  describe('loading state', () => {
    it('shows loading state when isLoading is true', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />)
      expect(screen.getByText('Wird ausgeführt...')).toBeInTheDocument()
    })

    it('disables buttons when loading', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />)
      const buttons = screen.getAllByRole('button')
      buttons.forEach((button) => {
        expect(button).toBeDisabled()
      })
    })

    it('does not close on backdrop click when loading', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />)
      const backdrop = document.querySelector('[aria-hidden="true"]')
      fireEvent.click(backdrop!)
      expect(defaultProps.onClose).not.toHaveBeenCalled()
    })

    it('does not close on Escape when loading', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />)
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(defaultProps.onClose).not.toHaveBeenCalled()
    })
  })

  describe('variants', () => {
    it('renders danger variant correctly', () => {
      render(<ConfirmDialog {...defaultProps} variant="danger" />)
      const confirmBtn = screen.getByText('Bestätigen')
      expect(confirmBtn).toHaveClass('bg-error-600')
    })

    it('renders warning variant correctly', () => {
      render(<ConfirmDialog {...defaultProps} variant="warning" />)
      const confirmBtn = screen.getByText('Bestätigen')
      expect(confirmBtn).toHaveClass('bg-warning-600')
    })

    it('renders info variant correctly', () => {
      render(<ConfirmDialog {...defaultProps} variant="info" />)
      const confirmBtn = screen.getByText('Bestätigen')
      expect(confirmBtn).toHaveClass('bg-primary-600')
    })
  })

  it('renders ReactNode message', () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        message={<strong>Bold message</strong>}
      />
    )
    expect(screen.getByText('Bold message')).toBeInTheDocument()
  })

  it('prevents body scroll when open', () => {
    render(<ConfirmDialog {...defaultProps} />)
    expect(document.body.style.overflow).toBe('hidden')
  })

  it('restores body scroll on unmount', () => {
    const { unmount } = render(<ConfirmDialog {...defaultProps} />)
    unmount()
    expect(document.body.style.overflow).toBe('')
  })
})

describe('confirmDialogPresets', () => {
  it('has delete preset', () => {
    expect(confirmDialogPresets.delete).toEqual({
      title: 'Löschen bestätigen',
      confirmLabel: 'Löschen',
      cancelLabel: 'Abbrechen',
      variant: 'danger',
      icon: 'trash',
    })
  })

  it('has logout preset', () => {
    expect(confirmDialogPresets.logout.title).toBe('Abmelden')
    expect(confirmDialogPresets.logout.variant).toBe('warning')
    expect(confirmDialogPresets.logout.icon).toBe('logout')
  })

  it('has cancel preset', () => {
    expect(confirmDialogPresets.cancel.title).toBe('Abbrechen bestätigen')
    expect(confirmDialogPresets.cancel.variant).toBe('warning')
  })

  it('has deactivate preset', () => {
    expect(confirmDialogPresets.deactivate.title).toBe('Deaktivieren')
    expect(confirmDialogPresets.deactivate.variant).toBe('warning')
  })
})
