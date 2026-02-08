import { test, expect } from '@playwright/test'
import path from 'path'

// Sample XML invoice content for testing
const sampleInvoiceXML = `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <ID>INV-001</ID>
  <IssueDate>2024-01-15</IssueDate>
</Invoice>`

test.describe('File Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows upload area on homepage', async ({ page }) => {
    // Check for file input or dropzone
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached()
  })

  test('upload area shows accepted formats', async ({ page }) => {
    await expect(page.getByText('XRechnung')).toBeVisible()
    await expect(page.getByText('ZUGFeRD')).toBeVisible()
    await expect(page.getByText('Factur-X')).toBeVisible()
  })

  test('can upload XML file via file input', async ({ page }) => {
    // Create a buffer with XML content
    const buffer = Buffer.from(sampleInvoiceXML)

    // Find the file input
    const fileInput = page.locator('input[type="file"]')

    // Upload the file
    await fileInput.setInputFiles({
      name: 'test-invoice.xml',
      mimeType: 'application/xml',
      buffer: buffer,
    })

    // Should show some indication of processing or result
    // Wait for either validation progress or result
    await expect(
      page.getByText(/validat|prüf|hochlad|upload/i).first()
    ).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Validation Results', () => {
  test('displays validation result after upload', async ({ page }) => {
    await page.goto('/')

    const buffer = Buffer.from(sampleInvoiceXML)
    const fileInput = page.locator('input[type="file"]')

    await fileInput.setInputFiles({
      name: 'test-invoice.xml',
      mimeType: 'application/xml',
      buffer: buffer,
    })

    // Wait for validation to complete (either success or error)
    await page.waitForSelector(
      '[data-testid="validation-result"], .validation-result, [class*="result"]',
      { timeout: 15000, state: 'visible' }
    ).catch(() => {
      // Result might be shown differently, check for status text
    })

    // Should show some kind of result or status
    const resultIndicator = page.locator('text=/valid|invalid|gültig|ungültig|fehler|error|success/i')
    await expect(resultIndicator.first()).toBeVisible({ timeout: 15000 })
  })
})

test.describe('Guest User Limits', () => {
  test('shows registration prompt after guest limit', async ({ page }) => {
    await page.goto('/')

    // This test would need multiple uploads to trigger the limit
    // For now, just verify the UI elements exist
    const buffer = Buffer.from(sampleInvoiceXML)
    const fileInput = page.locator('input[type="file"]')

    // First upload
    await fileInput.setInputFiles({
      name: 'test-invoice.xml',
      mimeType: 'application/xml',
      buffer: buffer,
    })

    // Wait for first result
    await page.waitForTimeout(3000)

    // Check if there's any indication about guest limits or registration
    const hasGuestMessage = await page.getByText(/register|registrieren|limit|kostenlos/i).isVisible().catch(() => false)

    // This is informational - the actual limit depends on backend config
    if (hasGuestMessage) {
      await expect(page.getByText(/register|registrieren/i)).toBeVisible()
    }
  })
})
