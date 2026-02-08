import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('displays login form', async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/password|passwort/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /login|anmelden/i })).toBeVisible()
  })

  test('shows validation error for empty form submission', async ({ page }) => {
    await page.getByRole('button', { name: /login|anmelden/i }).click()

    // Should show validation errors
    await expect(page.getByText(/required|erforderlich|email/i)).toBeVisible()
  })

  test('shows error for invalid email format', async ({ page }) => {
    await page.getByLabel(/email/i).fill('invalid-email')
    await page.getByLabel(/password|passwort/i).fill('password123')
    await page.getByRole('button', { name: /login|anmelden/i }).click()

    // Should show email validation error
    await expect(page.getByText(/valid|gültig|email/i)).toBeVisible()
  })

  test('has link to registration page', async ({ page }) => {
    const registerLink = page.getByRole('link', { name: /register|registrieren|sign up/i })
    await expect(registerLink).toBeVisible()
  })

  test('has link to forgot password', async ({ page }) => {
    const forgotLink = page.getByRole('link', { name: /forgot|vergessen|reset/i })
    await expect(forgotLink).toBeVisible()
  })

  test('can navigate to forgot password page', async ({ page }) => {
    await page.getByRole('link', { name: /forgot|vergessen|reset/i }).click()
    await expect(page).toHaveURL(/.*passwort-vergessen|forgot/)
  })
})

test.describe('Registration Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/registrieren')
  })

  test('displays registration form', async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/password|passwort/i).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /register|registrieren|sign up/i })).toBeVisible()
  })

  test('shows validation for password requirements', async ({ page }) => {
    await page.getByLabel(/email/i).fill('test@example.com')

    // Fill a weak password
    const passwordField = page.getByLabel(/password|passwort/i).first()
    await passwordField.fill('weak')

    // Trigger validation by clicking elsewhere or submitting
    await page.getByRole('button', { name: /register|registrieren|sign up/i }).click()

    // Should show password requirements
    await expect(page.getByText(/character|zeichen|mindestens/i)).toBeVisible()
  })

  test('has link to login page', async ({ page }) => {
    const loginLink = page.getByRole('link', { name: /login|anmelden|sign in/i })
    await expect(loginLink).toBeVisible()
  })
})

test.describe('Forgot Password Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/passwort-vergessen')
  })

  test('displays forgot password form', async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /reset|zurücksetzen|send/i })).toBeVisible()
  })

  test('has link back to login', async ({ page }) => {
    const loginLink = page.getByRole('link', { name: /login|anmelden|back/i })
    await expect(loginLink).toBeVisible()
  })
})
