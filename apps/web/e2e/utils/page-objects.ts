import { Page, Locator } from '@playwright/test'

/**
 * Page Object for the main application layout.
 *
 * Usage:
 *   const layout = new LayoutPage(page)
 *   await layout.clickSidebarLink('Dashboard')
 */
export class LayoutPage {
  readonly page: Page
  readonly sidebar: Locator
  readonly header: Locator
  readonly searchInput: Locator
  readonly notificationButton: Locator
  readonly userMenu: Locator

  constructor(page: Page) {
    this.page = page
    this.sidebar = page.locator('[role="navigation"]').first()
    this.header = page.locator('header').first()
    this.searchInput = page.locator('input[type="search"]')
    this.notificationButton = page.locator('button[aria-label*="notification"]')
    this.userMenu = page.locator('button[aria-label*="user"]')
  }

  async clickSidebarLink(linkText: string) {
    await this.sidebar.getByText(linkText).click()
  }

  async search(query: string) {
    await this.searchInput.fill(query)
    await this.searchInput.press('Enter')
  }

  async openNotifications() {
    await this.notificationButton.click()
  }

  async openUserMenu() {
    await this.userMenu.click()
  }
}

/**
 * Page Object for the Dashboard page.
 */
export class DashboardPage {
  readonly page: Page
  readonly metricCards: Locator
  readonly costTrendChart: Locator

  constructor(page: Page) {
    this.page = page
    this.metricCards = page.locator('[data-testid="metric-card"]')
    this.costTrendChart = page.locator('[data-testid="cost-trend-chart"]')
  }

  async goto() {
    await this.page.goto('/dashboard')
  }

  async getMetricValue(title: string): Promise<string> {
    const card = this.page.locator(`[data-testid="metric-card"]:has-text("${title}")`)
    return await card.locator('[data-testid="metric-value"]').textContent() || ''
  }

  async clickMetricCard(title: string) {
    const card = this.page.locator(`[data-testid="metric-card"]:has-text("${title}")`)
    await card.click()
  }
}
