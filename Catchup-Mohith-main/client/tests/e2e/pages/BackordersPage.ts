// client/tests/e2e/pages/BackordersPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class BackordersPage extends BasePage {
  // Locators
  private readonly overdueFilterButton: Locator
  private readonly noBackordersTitle: Locator

  constructor(page: Page) {
    super(page)
    this.overdueFilterButton = this.page.getByRole('button', {
      name: 'Overdue',
      exact: true,
    })
    this.noBackordersTitle = this.page.getByText('No backorders', { exact: true })
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/backorders')
  }

  async filterOverdue(): Promise<void> {
    await this.overdueFilterButton.click()
  }

  // Assertions
  async assertAgeIndicatorVisible(): Promise<void> {
    const overdue = this.page.getByText('Overdue', { exact: true })
    const days = this.page.getByText(/\d+ days/)
    const hasOverdue = await overdue.isVisible().catch(() => false)
    if (hasOverdue) {
      await expect(overdue).toBeVisible()
      return
    }
    await expect(days.first()).toBeVisible()
  }

  async assertEmptyState(): Promise<void> {
    await expect(this.noBackordersTitle).toBeVisible()
  }

  async assertOverdueFilterActive(): Promise<void> {
    const ariaSelected = await this.overdueFilterButton.getAttribute('aria-selected')
    const ariaPressed = await this.overdueFilterButton.getAttribute('aria-pressed')
    const className = (await this.overdueFilterButton.getAttribute('class')) ?? ''
    const isActive =
      ariaSelected === 'true' ||
      ariaPressed === 'true' ||
      className.includes('selected')
    expect(isActive).toBe(true)
  }

  async getRowCount(): Promise<number> {
    const rows = await this.page.getByRole('row').count()
    return Math.max(0, rows - 1)
  }
}
