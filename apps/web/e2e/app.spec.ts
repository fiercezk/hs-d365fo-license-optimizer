import { test, expect } from '@playwright/test'

test.describe('Application Smoke Tests', () => {
  test('should load the application successfully', async ({ page }) => {
    // Navigate to the dashboard page
    await page.goto('/dashboard')

    // Wait for the page to be fully loaded
    await page.waitForLoadState('domcontentloaded')

    // Verify the page title contains "D365 FO License Agent"
    await expect(page).toHaveTitle(/D365 FO License Agent/)

    // Verify the dashboard heading is visible
    const heading = page.getByRole('heading', { name: /Executive Dashboard/i })
    await expect(heading).toBeVisible()

    // Verify the page loaded successfully (not a 404 or error page)
    const body = page.locator('body')
    await expect(body).not.toContainText('404')
    await expect(body).not.toContainText('This page could not be found')
  })

  test('should display dashboard content', async ({ page }) => {
    await page.goto('/dashboard')

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded')

    // Verify dashboard description is present
    await expect(
      page.getByText(/License optimization and security compliance overview/i)
    ).toBeVisible()

    // Verify placeholder message is visible
    await expect(
      page.getByText(/Dashboard implementation in progress/i)
    ).toBeVisible()
  })

  test('should have correct page structure', async ({ page }) => {
    await page.goto('/dashboard')

    // Wait for the page to be fully loaded
    await page.waitForLoadState('domcontentloaded')

    // Verify main content area exists
    const main = page.locator('main')
    await expect(main).toBeVisible()

    // Verify the page has proper heading hierarchy
    const h1 = page.getByRole('heading', { level: 1 })
    await expect(h1).toBeVisible()
  })
})
