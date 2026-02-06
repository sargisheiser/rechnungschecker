import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/setup'
import { lookupCityByPLZ, searchAddresses, debounce } from './addressLookup'

describe('lookupCityByPLZ', () => {
  it('returns null for invalid PLZ format', async () => {
    expect(await lookupCityByPLZ('123')).toBe(null)
    expect(await lookupCityByPLZ('123456')).toBe(null)
    expect(await lookupCityByPLZ('abcde')).toBe(null)
    expect(await lookupCityByPLZ('')).toBe(null)
  })

  it('returns city name for valid PLZ', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.json([
          {
            place_id: 123,
            display_name: 'Berlin, Germany',
            address: {
              city: 'Berlin',
              postcode: '10115',
              country: 'Germany',
            },
          },
        ])
      })
    )

    const result = await lookupCityByPLZ('10115')
    expect(result).toBe('Berlin')
  })

  it('returns town if city is not available', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.json([
          {
            place_id: 123,
            display_name: 'Kleinstadt, Germany',
            address: {
              town: 'Kleinstadt',
              postcode: '12345',
            },
          },
        ])
      })
    )

    const result = await lookupCityByPLZ('12345')
    expect(result).toBe('Kleinstadt')
  })

  it('returns village if city and town not available', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.json([
          {
            place_id: 123,
            display_name: 'Dorf, Germany',
            address: {
              village: 'Dorf',
              postcode: '54321',
            },
          },
        ])
      })
    )

    const result = await lookupCityByPLZ('54321')
    expect(result).toBe('Dorf')
  })

  it('returns null for empty results', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.json([])
      })
    )

    const result = await lookupCityByPLZ('99999')
    expect(result).toBe(null)
  })

  it('returns null on fetch error', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.error()
      })
    )

    const result = await lookupCityByPLZ('10115')
    expect(result).toBe(null)
  })

  it('returns null on non-ok response', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    const result = await lookupCityByPLZ('10115')
    expect(result).toBe(null)
  })
})

describe('searchAddresses', () => {
  it('returns empty array for short queries', async () => {
    expect(await searchAddresses('')).toEqual([])
    expect(await searchAddresses('ab')).toEqual([])
  })

  it('returns formatted address suggestions', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.json([
          {
            place_id: 1,
            display_name: 'Musterstraße 1, 10115 Berlin, Germany',
            address: {
              road: 'Musterstraße',
              house_number: '1',
              postcode: '10115',
              city: 'Berlin',
              state: 'Berlin',
              country: 'Germany',
              country_code: 'de',
            },
            lat: '52.5',
            lon: '13.4',
          },
        ])
      })
    )

    const results = await searchAddresses('Musterstraße Berlin')
    expect(results).toHaveLength(1)
    expect(results[0]).toEqual({
      displayName: 'Musterstraße 1, 10115 Berlin, Germany',
      street: 'Musterstraße',
      houseNumber: '1',
      postalCode: '10115',
      city: 'Berlin',
      state: 'Berlin',
      country: 'Germany',
      countryCode: 'DE',
    })
  })

  it('handles missing address fields', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.json([
          {
            place_id: 1,
            display_name: 'Berlin, Germany',
            address: {
              city: 'Berlin',
              country: 'Germany',
            },
            lat: '52.5',
            lon: '13.4',
          },
        ])
      })
    )

    const results = await searchAddresses('Berlin')
    expect(results).toHaveLength(1)
    expect(results[0].street).toBeUndefined()
    expect(results[0].houseNumber).toBeUndefined()
    expect(results[0].postalCode).toBeUndefined()
    expect(results[0].city).toBe('Berlin')
  })

  it('returns empty array on error', async () => {
    server.use(
      http.get('https://nominatim.openstreetmap.org/search', () => {
        return HttpResponse.error()
      })
    )

    const results = await searchAddresses('Berlin')
    expect(results).toEqual([])
  })
})

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('delays function execution', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn()
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(50)
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(50)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('only executes once for multiple calls within delay', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn()
    debouncedFn()
    debouncedFn()

    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('passes arguments to debounced function', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn('arg1', 'arg2')

    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledWith('arg1', 'arg2')
  })

  it('uses latest arguments when called multiple times', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn('first')
    debouncedFn('second')
    debouncedFn('third')

    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledWith('third')
  })
})
