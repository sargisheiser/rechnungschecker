import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@/test/test-utils'
import { AddressInput } from './AddressInput'

// Mock the address lookup functions
vi.mock('@/lib/addressLookup', () => ({
  lookupCityByPLZ: vi.fn(),
  searchAddresses: vi.fn(),
}))

import { lookupCityByPLZ, searchAddresses } from '@/lib/addressLookup'

describe('AddressInput', () => {
  const defaultValues = {
    street: '',
    postalCode: '',
    city: '',
    countryCode: 'DE',
  }

  const mockOnChange = vi.fn()

  beforeEach(() => {
    vi.useFakeTimers()
    vi.mocked(lookupCityByPLZ).mockResolvedValue(null)
    vi.mocked(searchAddresses).mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('basic rendering', () => {
    it('renders all address fields', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} />)

      expect(screen.getByPlaceholderText('Musterstraße 123')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('12345')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Berlin')).toBeInTheDocument()
    })

    it('renders search input when showSearch is true', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} showSearch />)

      expect(screen.getByPlaceholderText('Straße, PLZ oder Stadt eingeben...')).toBeInTheDocument()
    })

    it('hides search input when showSearch is false', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} showSearch={false} />)

      expect(screen.queryByPlaceholderText('Straße, PLZ oder Stadt eingeben...')).not.toBeInTheDocument()
    })

    it('displays provided values', () => {
      const values = {
        street: 'Teststraße 1',
        postalCode: '10115',
        city: 'Berlin',
        countryCode: 'DE',
      }

      render(<AddressInput values={values} onChange={mockOnChange} />)

      expect(screen.getByDisplayValue('Teststraße 1')).toBeInTheDocument()
      expect(screen.getByDisplayValue('10115')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Berlin')).toBeInTheDocument()
    })
  })

  describe('field changes', () => {
    it('calls onChange when street changes', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} />)

      const streetInput = screen.getByPlaceholderText('Musterstraße 123')
      fireEvent.change(streetInput, { target: { value: 'Neue Straße 5' } })

      expect(mockOnChange).toHaveBeenCalledWith({
        ...defaultValues,
        street: 'Neue Straße 5',
      })
    })

    it('calls onChange when postal code changes', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} />)

      const plzInput = screen.getByPlaceholderText('12345')
      fireEvent.change(plzInput, { target: { value: '10115' } })

      expect(mockOnChange).toHaveBeenCalledWith({
        ...defaultValues,
        postalCode: '10115',
      })
    })

    it('calls onChange when city changes', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} />)

      const cityInput = screen.getByPlaceholderText('Berlin')
      fireEvent.change(cityInput, { target: { value: 'München' } })

      expect(mockOnChange).toHaveBeenCalledWith({
        ...defaultValues,
        city: 'München',
      })
    })
  })

  describe('PLZ auto-lookup', () => {
    it('does not lookup for incomplete PLZ', async () => {
      const values = { ...defaultValues, postalCode: '101' }
      render(<AddressInput values={values} onChange={mockOnChange} />)

      await act(async () => {
        vi.advanceTimersByTime(600)
      })

      expect(lookupCityByPLZ).not.toHaveBeenCalled()
    })

    it('does not lookup for non-numeric PLZ', async () => {
      const values = { ...defaultValues, postalCode: 'abcde' }
      render(<AddressInput values={values} onChange={mockOnChange} />)

      await act(async () => {
        vi.advanceTimersByTime(600)
      })

      expect(lookupCityByPLZ).not.toHaveBeenCalled()
    })

    it('shows auto-complete hint text', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} />)

      expect(screen.getByText('Stadt wird automatisch ergänzt')).toBeInTheDocument()
    })

    it('calls lookupCityByPLZ for valid 5-digit PLZ', async () => {
      vi.mocked(lookupCityByPLZ).mockResolvedValue('Berlin')

      const values = { ...defaultValues, postalCode: '10115' }
      render(<AddressInput values={values} onChange={mockOnChange} />)

      // Advance past debounce
      await act(async () => {
        vi.advanceTimersByTime(600)
      })

      // Flush promises
      await act(async () => {
        await vi.runAllTimersAsync()
      })

      expect(lookupCityByPLZ).toHaveBeenCalledWith('10115')
    })
  })

  describe('address search', () => {
    it('does not search for queries less than 3 characters', async () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} showSearch />)

      const searchInput = screen.getByPlaceholderText('Straße, PLZ oder Stadt eingeben...')
      fireEvent.change(searchInput, { target: { value: 'Te' } })

      await act(async () => {
        vi.advanceTimersByTime(600)
      })

      expect(searchAddresses).not.toHaveBeenCalled()
    })

    it('searches when query is at least 3 characters', async () => {
      vi.mocked(searchAddresses).mockResolvedValue([])

      render(<AddressInput values={defaultValues} onChange={mockOnChange} showSearch />)

      const searchInput = screen.getByPlaceholderText('Straße, PLZ oder Stadt eingeben...')
      fireEvent.change(searchInput, { target: { value: 'Test' } })

      await act(async () => {
        vi.advanceTimersByTime(600)
      })

      await act(async () => {
        await vi.runAllTimersAsync()
      })

      expect(searchAddresses).toHaveBeenCalledWith('Test')
    })
  })

  describe('disabled state', () => {
    it('disables all inputs when disabled prop is true', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} disabled showSearch />)

      expect(screen.getByPlaceholderText('Musterstraße 123')).toBeDisabled()
      expect(screen.getByPlaceholderText('12345')).toBeDisabled()
      expect(screen.getByPlaceholderText('Berlin')).toBeDisabled()
      expect(screen.getByPlaceholderText('Straße, PLZ oder Stadt eingeben...')).toBeDisabled()
    })
  })

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <AddressInput values={defaultValues} onChange={mockOnChange} className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('labels', () => {
    it('displays field labels', () => {
      render(<AddressInput values={defaultValues} onChange={mockOnChange} showSearch />)

      expect(screen.getByText('Adresse suchen')).toBeInTheDocument()
      expect(screen.getByText('Straße')).toBeInTheDocument()
      expect(screen.getByText('PLZ')).toBeInTheDocument()
      expect(screen.getByText('Stadt')).toBeInTheDocument()
    })
  })

})
