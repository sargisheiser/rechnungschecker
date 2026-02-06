import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
})

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: MockResizeObserver,
})

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: vi.fn(),
})

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
    get length() { return Object.keys(store).length },
    key: (i: number) => Object.keys(store)[i] || null,
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// MSW Server Handlers
export const handlers = [
  // Auth endpoints
  http.get('/api/auth/me', () => {
    return HttpResponse.json({
      id: 'test-user-id',
      email: 'test@example.com',
      full_name: 'Test User',
      company_name: 'Test Company',
      plan: 'pro',
      created_at: new Date().toISOString(),
    })
  }),

  // Usage endpoint
  http.get('/api/billing/usage', () => {
    return HttpResponse.json({
      validations_used: 5,
      validations_limit: 100,
      conversions_used: 2,
      conversions_limit: 50,
    })
  }),

  // Validation history
  http.get('/api/validations', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'val-1',
          file_name: 'test-invoice.xml',
          file_type: 'xrechnung',
          is_valid: true,
          error_count: 0,
          warning_count: 1,
          validated_at: new Date().toISOString(),
        },
        {
          id: 'val-2',
          file_name: 'test-invoice-2.pdf',
          file_type: 'zugferd',
          is_valid: false,
          error_count: 2,
          warning_count: 0,
          validated_at: new Date().toISOString(),
        },
      ],
      total: 2,
      page: 1,
      size: 10,
    })
  }),

  // Templates
  http.get('/api/templates', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'tmpl-1',
          name: 'My Company',
          template_type: 'sender',
          company_name: 'My Company GmbH',
          city: 'Berlin',
          is_default: true,
        },
      ],
      total: 1,
    })
  }),

  // Clients
  http.get('/api/clients', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'client-1',
          name: 'Test Client',
          client_number: 'C001',
          is_active: true,
        },
      ],
      total: 1,
    })
  }),
]

export const server = setupServer(...handlers)

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }))

// Reset handlers after each test
afterEach(() => server.resetHandlers())

// Clean up after all tests
afterAll(() => server.close())
