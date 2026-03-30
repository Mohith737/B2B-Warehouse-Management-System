// client/tests/e2e/pages/ProductsPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class ProductsPage extends BasePage {
  // Locators
  private readonly searchInput: Locator
  private readonly productsTableTitle: Locator
  private readonly noProductsTitle: Locator
  private readonly loadingText: Locator
  private readonly nextPageButton: Locator
  private readonly paginationRangeText: Locator
  private readonly tableRows: Locator
  private readonly tableCells: Locator

  constructor(page: Page) {
    super(page)
    this.searchInput = this.page.getByRole('searchbox', { name: /products search/i })
    this.productsTableTitle = this.page.getByText('Products', { exact: true })
    this.noProductsTitle = this.page.getByText('No products', { exact: true })
    this.loadingText = this.page.getByText('Loading')
    this.nextPageButton = this.page.getByRole('button', { name: 'Next page' })
    this.paginationRangeText = this.page.getByText(/\d+-\d+ of \d+/)
    this.tableRows = this.page.getByRole('row')
    this.tableCells = this.page.getByRole('cell')
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/products')
  }

  async search(term: string): Promise<void> {
    await this.searchInput.fill(term)
    await this.page.waitForTimeout(350)
  }

  async clickNextPage(): Promise<void> {
    await this.nextPageButton.click()
  }

  async getPaginationRange(): Promise<string> {
    return (await this.paginationRangeText.first().textContent())?.trim() ?? ''
  }

  async getFirstCellText(): Promise<string> {
    const count = await this.tableCells.count()
    if (count === 0) {
      return ''
    }
    return (await this.tableCells.first().textContent())?.trim() ?? ''
  }

  async getRowCount(): Promise<number> {
    const totalRows = await this.tableRows.count()
    return Math.max(0, totalRows - 1)
  }

  // Assertions
  async assertPageRendered(): Promise<void> {
    await expect(this.productsTableTitle.or(this.noProductsTitle).first()).toBeVisible()
  }

  async assertProductVisible(sku: string): Promise<void> {
    await expect(this.page.getByRole('cell', { name: sku, exact: true })).toBeVisible()
  }

  async assertEmptyState(): Promise<void> {
    await expect(this.noProductsTitle).toBeVisible()
  }

  async assertLoadingVisible(): Promise<void> {
    await expect(this.loadingText).toBeVisible()
  }
}
