import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nextProvider } from 'react-i18next'
import i18n from '@/lib/i18n'

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface WrapperProps {
  children: React.ReactNode
}

function AllTheProviders({ children }: WrapperProps) {
  const queryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        <BrowserRouter>{children}</BrowserRouter>
      </I18nextProvider>
    </QueryClientProvider>
  )
}

// Custom render that includes providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything from testing-library
export * from '@testing-library/react'
export { userEvent } from '@testing-library/user-event'

// Override render with custom render
export { customRender as render }

// Utility to create a mock file
export function createMockFile(
  name: string,
  type: string,
  content = 'mock content'
): File {
  const file = new File([content], name, { type })
  return file
}

// Utility to create a mock XML invoice file
export function createMockInvoiceXML(): File {
  const xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:cen.eu:en16931:2017#compliant#urn:xoev-de:kosit:standard:xrechnung_2.0</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>`
  return new File([xmlContent], 'invoice.xml', { type: 'application/xml' })
}

// Utility to wait for async operations
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0))
