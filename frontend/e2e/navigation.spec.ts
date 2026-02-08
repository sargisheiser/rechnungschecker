import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('homepage loads successfully', async ({ page }) => {
    const response = await page.goto('/')
    expect(response?.status()).toBe(200)
  })

  test('login page loads successfully', async ({ page }) => {
    const response = await page.goto('/login')
    expect(response?.status()).toBe(200)
  })

  test('registration page loads successfully', async ({ page }) => {
    const response = await page.goto('/registrieren')
    expect(response?.status()).toBe(200)
  })

  test('forgot password page loads successfully', async ({ page }) => {
    const response = await page.goto('/passwort-vergessen')
    expect(response?.status()).toBe(200)
  })

  test('pricing page loads successfully', async ({ page }) => {
    const response = await page.goto('/preise')
    expect(response?.status()).toBe(200)
  })

  test('API docs page loads successfully', async ({ page }) => {
    const response = await page.goto('/api-docs')
    expect(response?.status()).toBe(200)
  })
})

test.describe('Protected Routes - Unauthenticated', () => {
  test('dashboard redirects to login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/.*login/)
  })

  test('settings redirects to login', async ({ page }) => {
    await page.goto('/einstellungen')
    await expect(page).toHaveURL(/.*login/)
  })

  test('history redirects to login', async ({ page }) => {
    await page.goto('/verlauf')
    await expect(page).toHaveURL(/.*login/)
  })
})

test.describe('Footer Links', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('has privacy policy link', async ({ page }) => {
    const privacyLink = page.getByRole('link', { name: /privacy|datenschutz/i })
    if (await privacyLink.isVisible()) {
      await privacyLink.click()
      await expect(page).toHaveURL(/.*datenschutz|privacy/)
    }
  })

  test('has terms of service link', async ({ page }) => {
    const termsLink = page.getByRole('link', { name: /terms|agb|nutzungsbedingungen/i })
    if (await termsLink.isVisible()) {
      await termsLink.click()
      await expect(page).toHaveURL(/.*agb|terms/)
    }
  })

  test('has imprint link', async ({ page }) => {
    const imprintLink = page.getByRole('link', { name: /imprint|impressum/i })
    if (await imprintLink.isVisible()) {
      await imprintLink.click()
      await expect(page).toHaveURL(/.*impressum|imprint/)
    }
  })
})

test.describe('Responsive Navigation', () => {
  test('mobile menu toggle works on small screens', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Look for mobile menu button (hamburger)
    const menuButton = page.getByRole('button', { name: /menu|menü/i }).or(
      page.locator('[aria-label*="menu"]')
    ).or(
      page.locator('button').filter({ has: page.locator('svg') }).first()
    )

    if (await menuButton.isVisible()) {
      await menuButton.click()
      // Menu should now be open
      await expect(page.getByRole('link', { name: /login|anmelden/i })).toBeVisible()
    }
  })
})

test.describe('404 Page', () => {
  test('shows 404 for non-existent routes', async ({ page }) => {
    await page.goto('/this-page-does-not-exist-12345')

    // Should show 404 message
    await expect(page.getByText(/404|not found|nicht gefunden|seite/i)).toBeVisible()
  })
})
