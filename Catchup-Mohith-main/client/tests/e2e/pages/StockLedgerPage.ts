// client/tests/e2e/pages/StockLedgerPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class StockLedgerPage extends BasePage {
  // Locators
  private readonly loadMoreButton: Locator
  private readonly noEntriesTitle: Locator
  private readonly stockLedgerTitle: Locator
  private readonly tableRows: Locator

  constructor(page: Page) {
    super(page)
    this.loadMoreButton = this.page.getByRole('button', { name: 'Load More' })
    this.noEntriesTitle = this.page.getByText('No ledger entries', { exact: true })
    this.stockLedgerTitle = this.page.getByText('Stock Ledger', { exact: true })
    this.tableRows = this.page.getByRole('row')
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/stock-ledger')
  }

  async clickLoadMore(): Promise<void> {
    if (await this.loadMoreButton.isVisible().catch(() => false)) {
      await this.loadMoreButton.click()
    }
  }

  // Assertions
  async getRowCount(): Promise<number> {
    const rows = await this.tableRows.count()
    return Math.max(0, rows - 1)
  }

  async assertEmptyState(): Promise<void> {
    await expect(this.noEntriesTitle).toBeVisible()
  }

  async assertColumnsVisible(): Promise<void> {
    await expect(this.stockLedgerTitle).toBeVisible()
    await expect(this.page.getByRole('columnheader', { name: 'Date' })).toBeVisible()
    await expect(this.page.getByRole('columnheader', { name: 'Product' })).toBeVisible()
    await expect(this.page.getByRole('columnheader', { name: 'SKU' })).toBeVisible()
    await expect(this.page.getByRole('columnheader', { name: 'Change' })).toBeVisible()
    await expect(this.page.getByRole('columnheader', { name: 'Type' })).toBeVisible()
  }
}
