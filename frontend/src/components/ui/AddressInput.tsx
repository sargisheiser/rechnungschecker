import { useState, useEffect, useCallback, useRef } from 'react'
import { MapPin, Loader2, Search, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { lookupCityByPLZ, searchAddresses, type AddressSuggestion } from '@/lib/addressLookup'

interface AddressFields {
  street?: string
  postalCode?: string
  city?: string
  countryCode?: string
}

interface AddressInputProps {
  /** Current address values */
  values: AddressFields
  /** Called when any address field changes */
  onChange: (fields: AddressFields) => void
  /** Whether the fields are disabled */
  disabled?: boolean
  /** Show address search input */
  showSearch?: boolean
  /** Custom class name */
  className?: string
}

export function AddressInput({
  values,
  onChange,
  disabled = false,
  showSearch = true,
  className,
}: AddressInputProps) {
  const [isLookingUp, setIsLookingUp] = useState(false)
  const [lookupSuccess, setLookupSuccess] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const lookupTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  // Refs to hold latest values/onChange to avoid stale closures in useEffect
  const valuesRef = useRef(values)
  const onChangeRef = useRef(onChange)

  // Keep refs updated
  useEffect(() => {
    valuesRef.current = values
    onChangeRef.current = onChange
  }, [values, onChange])

  // PLZ auto-lookup for city
  useEffect(() => {
    const plz = values.postalCode?.trim()

    // Only lookup if PLZ is exactly 5 digits and city is empty
    if (!plz || !/^\d{5}$/.test(plz)) {
      return
    }

    // Clear any pending lookup
    if (lookupTimeoutRef.current) {
      clearTimeout(lookupTimeoutRef.current)
    }

    // Debounce the lookup
    lookupTimeoutRef.current = setTimeout(async () => {
      setIsLookingUp(true)
      setLookupSuccess(false)

      const city = await lookupCityByPLZ(plz)

      if (city) {
        // Use refs to get latest values and onChange
        onChangeRef.current({ ...valuesRef.current, city })
        setLookupSuccess(true)
        // Reset success indicator after 2 seconds
        setTimeout(() => setLookupSuccess(false), 2000)
      }

      setIsLookingUp(false)
    }, 500)

    return () => {
      if (lookupTimeoutRef.current) {
        clearTimeout(lookupTimeoutRef.current)
      }
    }
  }, [values.postalCode])

  // Address search
  const handleSearch = useCallback(async (query: string) => {
    if (query.length < 3) {
      setSuggestions([])
      return
    }

    setIsSearching(true)
    const results = await searchAddresses(query)
    setSuggestions(results)
    setShowSuggestions(results.length > 0)
    setIsSearching(false)
  }, [])

  // Debounced search
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (searchQuery.length >= 3) {
      searchTimeoutRef.current = setTimeout(() => {
        handleSearch(searchQuery)
      }, 500)
    } else {
      setSuggestions([])
      setShowSuggestions(false)
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchQuery, handleSearch])

  const handleSelectSuggestion = (suggestion: AddressSuggestion) => {
    onChange({
      street: suggestion.street
        ? suggestion.houseNumber
          ? `${suggestion.street} ${suggestion.houseNumber}`
          : suggestion.street
        : values.street,
      postalCode: suggestion.postalCode || values.postalCode,
      city: suggestion.city || values.city,
      countryCode: suggestion.countryCode || values.countryCode,
    })
    setSearchQuery('')
    setSuggestions([])
    setShowSuggestions(false)
  }

  const handleFieldChange = (field: keyof AddressFields, value: string) => {
    onChange({ ...values, [field]: value })
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Address Search */}
      {showSearch && (
        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Adresse suchen
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              placeholder="Straße, PLZ oder Stadt eingeben..."
              disabled={disabled}
              className="input pl-10 pr-10"
            />
            {isSearching && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
            )}
          </div>

          {/* Suggestions dropdown */}
          {showSuggestions && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowSuggestions(false)}
              />
              <div className="absolute z-20 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 max-h-60 overflow-y-auto">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleSelectSuggestion(suggestion)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start gap-3 border-b border-gray-100 last:border-0"
                  >
                    <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {suggestion.street}
                        {suggestion.houseNumber && ` ${suggestion.houseNumber}`}
                        {suggestion.postalCode && `, ${suggestion.postalCode}`}
                        {suggestion.city && ` ${suggestion.city}`}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {suggestion.displayName}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Street */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Straße
        </label>
        <input
          type="text"
          value={values.street || ''}
          onChange={(e) => handleFieldChange('street', e.target.value)}
          disabled={disabled}
          className="input"
          maxLength={200}
          placeholder="Musterstraße 123"
        />
      </div>

      {/* PLZ and City row */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            PLZ
          </label>
          <div className="relative">
            <input
              type="text"
              value={values.postalCode || ''}
              onChange={(e) => handleFieldChange('postalCode', e.target.value)}
              disabled={disabled}
              className="input pr-8"
              maxLength={5}
              placeholder="12345"
            />
            {isLookingUp && (
              <Loader2 className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-primary-500" />
            )}
            {lookupSuccess && (
              <Check className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-success-500" />
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Stadt wird automatisch ergänzt
          </p>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stadt
          </label>
          <input
            type="text"
            value={values.city || ''}
            onChange={(e) => handleFieldChange('city', e.target.value)}
            disabled={disabled}
            className="input"
            maxLength={100}
            placeholder="Berlin"
          />
        </div>
      </div>
    </div>
  )
}
