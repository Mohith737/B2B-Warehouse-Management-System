// client/tests/e2e/pages/SuppliersPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class SuppliersPage extends BasePage {
  // Locators
  private readonly searchInput: Locator
  private readonly suppliersTableTitle: Locator
  private readonly noSuppliersTitle: Locator
  private readonly unauthorizedTitle: Locator

  constructor(page: Page) {
    super(page)
    this.searchInput = this.page.getByRole('searchbox', { name: /suppliers search/i })
    this.suppliersTableTitle = this.page.getByText('Suppliers', { exact: true })
    this.noSuppliersTitle = this.page.getByText('No suppliers', { exact: true })
    this.unauthorizedTitle = this.page.getByText('Unauthorized', { exact: true })
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/suppliers')
  }

  async filterByTier(tier: 'Silver' | 'Gold' | 'Diamond'): Promise<void> {
    await this.page.getByRole('button', { name: tier, exact: true }).click()
    await this.page.waitForTimeout(350)
  }

  async search(term: string): Promise<void> {
    await this.searchInput.fill(term)
    await this.page.waitForTimeout(350)
  }

  async getRowCount(): Promise<number> {
    const rows = this.page.getByRole('row')
    const totalRows = await rows.count()
    return Math.max(0, totalRows - 1)
  }

  async getFirstSupplierName(): Promise<string> {
    const firstCell = this.page.getByRole('cell').first()
    if ((await firstCell.count()) === 0) {
      return ''
    }
    return (await firstCell.textContent())?.trim() ?? ''
  }

  // Assertions
  async assertPageRendered(): Promise<void> {
    await expect(
      this.suppliersTableTitle.or(this.noSuppliersTitle).first(),
    ).toBeVisible()
  }

  async assertSupplierVisible(name: string): Promise<void> {
    await expect(this.page.getByRole('cell', { name, exact: true })).toBeVisible()
  }

  async assertAllRowsMatchTier(tier: 'Silver' | 'Gold' | 'Diamond'): Promise<void> {
    const dataRows = this.page
      .getByRole('row')
      .filter({ has: this.page.getByRole('cell') })
    const rowCount = await dataRows.count()
    for (let index = 0; index < rowCount; index += 1) {
      await expect(dataRows.nth(index).getByText(tier, { exact: true })).toBeVisible()
    }
  }

  async assertRedirectedToUnauthorized(): Promise<void> {
    await expect(this.page).toHaveURL(/\/unauthorized$/)
    await expect(this.unauthorizedTitle).toBeVisible()
  }
}
