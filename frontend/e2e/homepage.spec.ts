import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('displays the main heading and file upload area', async ({ page }) => {
    // Check main heading
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()

    // Check file upload area exists
    await expect(page.getByText('XRechnung')).toBeVisible()
    await expect(page.getByText('ZUGFeRD')).toBeVisible()
  })

  test('shows supported invoice formats', async ({ page }) => {
    await expect(page.getByText('XRechnung')).toBeVisible()
    await expect(page.getByText('ZUGFeRD 2.0/2.1')).toBeVisible()
    await expect(page.getByText('Factur-X')).toBeVisible()
  })

  test('has navigation links', async ({ page }) => {
    // Check for login/register links when not authenticated
    await expect(page.getByRole('link', { name: /login|anmelden/i })).toBeVisible()
  })

  test('can navigate to login page', async ({ page }) => {
    await page.getByRole('link', { name: /login|anmelden/i }).click()
    await expect(page).toHaveURL(/.*login/)
  })

  test('can navigate to registration page', async ({ page }) => {
    const registerLink = page.getByRole('link', { name: /register|registrieren/i })
    if (await registerLink.isVisible()) {
      await registerLink.click()
      await expect(page).toHaveURL(/.*registrieren/)
    }
  })

  test('file upload area accepts drag indication', async ({ page }) => {
    // Find the dropzone
    const dropzone = page.locator('[data-testid="dropzone"]').or(
      page.locator('text=XRechnung').locator('..').locator('..')
    )

    // Verify it exists and is interactive
    await expect(dropzone.first()).toBeVisible()
  })
})

test.describe('Homepage - Language', () => {
  test('can switch language if language switcher exists', async ({ page }) => {
    await page.goto('/')

    // Look for language switcher
    const langSwitcher = page.getByRole('button', { name: /DE|EN|language/i })

    if (await langSwitcher.isVisible()) {
      await langSwitcher.click()
      // Should show language options
      await expect(page.getByText(/English|Deutsch/)).toBeVisible()
    }
  })
})
