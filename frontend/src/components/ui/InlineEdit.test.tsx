import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/test-utils'
import { InlineEdit, InlineEditSimple } from './InlineEdit'

describe('InlineEdit', () => {
  const defaultProps = {
    value: 'Test value',
    onSave: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders display mode by default', () => {
    render(<InlineEdit {...defaultProps} />)
    expect(screen.getByText('Test value')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('shows empty text when value is empty', () => {
    render(<InlineEdit {...defaultProps} value="" emptyText="No value" />)
    expect(screen.getByText('No value')).toBeInTheDocument()
  })

  it('enters edit mode on click', () => {
    render(<InlineEdit {...defaultProps} />)
    fireEvent.click(screen.getByText('Test value'))
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('does not enter edit mode when disabled', () => {
    render(<InlineEdit {...defaultProps} disabled={true} />)
    fireEvent.click(screen.getByText('Test value'))
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('focuses input when entering edit mode', () => {
    render(<InlineEdit {...defaultProps} />)
    fireEvent.click(screen.getByText('Test value'))
    expect(screen.getByRole('textbox')).toHaveFocus()
  })

  it('saves on blur', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<InlineEdit {...defaultProps} onSave={onSave} />)

    fireEvent.click(screen.getByText('Test value'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New value' } })
    fireEvent.blur(input)

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith('New value')
    })
  })

  it('saves on Enter key for text input', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<InlineEdit {...defaultProps} onSave={onSave} type="text" />)

    fireEvent.click(screen.getByText('Test value'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New value' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith('New value')
    })
  })

  it('cancels on Escape key', () => {
    render(<InlineEdit {...defaultProps} />)

    fireEvent.click(screen.getByText('Test value'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'Changed value' } })
    fireEvent.keyDown(input, { key: 'Escape' })

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByText('Test value')).toBeInTheDocument()
  })

  it('trims value before saving', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<InlineEdit {...defaultProps} onSave={onSave} />)

    fireEvent.click(screen.getByText('Test value'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '  Trimmed  ' } })
    fireEvent.blur(input)

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith('Trimmed')
    })
  })

  it('does not save if value is unchanged', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<InlineEdit {...defaultProps} onSave={onSave} />)

    fireEvent.click(screen.getByText('Test value'))
    const input = screen.getByRole('textbox')
    fireEvent.blur(input)

    // Should exit edit mode without calling save
    await waitFor(() => {
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    })
    expect(onSave).not.toHaveBeenCalled()
  })

  it('shows save and cancel buttons when editing', () => {
    render(<InlineEdit {...defaultProps} />)
    fireEvent.click(screen.getByText('Test value'))

    expect(screen.getByTitle('Speichern (Enter)')).toBeInTheDocument()
    expect(screen.getByTitle('Abbrechen (Esc)')).toBeInTheDocument()
  })

  it('renders as textarea when type is textarea', () => {
    render(<InlineEdit {...defaultProps} type="textarea" />)
    fireEvent.click(screen.getByText('Test value'))
    expect(screen.getByRole('textbox').tagName).toBe('TEXTAREA')
  })

  it('shows helper text for textarea', () => {
    render(<InlineEdit {...defaultProps} type="textarea" />)
    fireEvent.click(screen.getByText('Test value'))
    expect(screen.getByText(/⌘\+Enter zum Speichern/)).toBeInTheDocument()
  })

  it('respects maxLength prop', () => {
    render(<InlineEdit {...defaultProps} maxLength={10} />)
    fireEvent.click(screen.getByText('Test value'))
    expect(screen.getByRole('textbox')).toHaveAttribute('maxLength', '10')
  })

  it('applies custom className', () => {
    const { container } = render(
      <InlineEdit {...defaultProps} className="custom-class" />
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('InlineEditSimple', () => {
  const defaultProps = {
    value: 'Simple value',
    onSave: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders value in display mode', () => {
    render(<InlineEditSimple {...defaultProps} />)
    expect(screen.getByText('Simple value')).toBeInTheDocument()
  })

  it('enters edit mode on click', () => {
    render(<InlineEditSimple {...defaultProps} />)
    fireEvent.click(screen.getByText('Simple value'))
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('selects text when entering edit mode', () => {
    render(<InlineEditSimple {...defaultProps} />)
    fireEvent.click(screen.getByText('Simple value'))
    // Focus should be on input
    expect(screen.getByRole('textbox')).toHaveFocus()
  })

  it('saves on Enter', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<InlineEditSimple {...defaultProps} onSave={onSave} />)

    fireEvent.click(screen.getByText('Simple value'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New value' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith('New value')
    })
  })

  it('cancels on Escape', () => {
    render(<InlineEditSimple {...defaultProps} />)

    fireEvent.click(screen.getByText('Simple value'))
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Escape' })

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('shows placeholder when empty', () => {
    render(<InlineEditSimple {...defaultProps} value="" placeholder="Enter text" />)
    expect(screen.getByText('Enter text')).toBeInTheDocument()
  })
})
