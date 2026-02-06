/**
 * Address lookup service using OpenStreetMap Nominatim API
 * Free to use with attribution, rate-limited to 1 request/second
 */

const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org'

interface NominatimResult {
  place_id: number
  display_name: string
  address: {
    road?: string
    house_number?: string
    postcode?: string
    city?: string
    town?: string
    village?: string
    municipality?: string
    state?: string
    country?: string
    country_code?: string
  }
  lat: string
  lon: string
}

export interface AddressSuggestion {
  displayName: string
  street?: string
  houseNumber?: string
  postalCode?: string
  city?: string
  state?: string
  country?: string
  countryCode?: string
}

/**
 * Lookup city by German postal code (PLZ)
 */
export async function lookupCityByPLZ(plz: string): Promise<string | null> {
  // Validate PLZ format (5 digits for Germany)
  if (!/^\d{5}$/.test(plz)) {
    return null
  }

  try {
    const params = new URLSearchParams({
      postalcode: plz,
      country: 'de',
      format: 'json',
      addressdetails: '1',
      limit: '1',
    })

    const response = await fetch(`${NOMINATIM_BASE_URL}/search?${params}`, {
      headers: {
        'Accept-Language': 'de',
        'User-Agent': 'RechnungsChecker/1.0',
      },
    })

    if (!response.ok) {
      return null
    }

    const results: NominatimResult[] = await response.json()

    if (results.length === 0) {
      return null
    }

    const address = results[0].address
    // German addresses can have city, town, village, or municipality
    return address.city || address.town || address.village || address.municipality || null
  } catch (error) {
    console.error('PLZ lookup failed:', error)
    return null
  }
}

/**
 * Search for addresses by query string
 */
export async function searchAddresses(query: string, limit = 5): Promise<AddressSuggestion[]> {
  if (!query || query.length < 3) {
    return []
  }

  try {
    const params = new URLSearchParams({
      q: query,
      country: 'de',
      format: 'json',
      addressdetails: '1',
      limit: limit.toString(),
    })

    const response = await fetch(`${NOMINATIM_BASE_URL}/search?${params}`, {
      headers: {
        'Accept-Language': 'de',
        'User-Agent': 'RechnungsChecker/1.0',
      },
    })

    if (!response.ok) {
      return []
    }

    const results: NominatimResult[] = await response.json()

    return results.map((result) => ({
      displayName: result.display_name,
      street: result.address.road,
      houseNumber: result.address.house_number,
      postalCode: result.address.postcode,
      city:
        result.address.city ||
        result.address.town ||
        result.address.village ||
        result.address.municipality,
      state: result.address.state,
      country: result.address.country,
      countryCode: result.address.country_code?.toUpperCase(),
    }))
  } catch (error) {
    console.error('Address search failed:', error)
    return []
  }
}

/**
 * Debounce helper for rate limiting
 */
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}
