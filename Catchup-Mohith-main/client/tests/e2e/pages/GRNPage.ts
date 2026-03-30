// client/tests/e2e/pages/GRNPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class GRNPage extends BasePage {
  // Locators
  private readonly openPOSelect: Locator
  private readonly startGRNButton: Locator
  private readonly barcodeInput: Locator
  private readonly receiveLineButton: Locator
  private readonly completeGRNButton: Locator

  constructor(page: Page) {
    super(page)
    this.openPOSelect = this.page.getByRole('combobox', {
      name: 'Open purchase orders',
    })
    this.startGRNButton = this.page.getByRole('button', { name: 'Start GRN' })
    this.barcodeInput = this.page.getByRole('textbox', { name: 'Scan barcode' })
    this.receiveLineButton = this.page.getByRole('button', { name: 'Receive Line' })
    this.completeGRNButton = this.page.getByRole('button', { name: 'Complete GRN' })
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/grns')
  }

  async selectPO(poNumber: string): Promise<void> {
    const options = this.page.getByRole('option')
    const optionCount = await options.count()

    let matchedOptionValue: string | null = null
    for (let index = 0; index < optionCount; index += 1) {
      const option = options.nth(index)
      const optionText = (await option.textContent())?.trim() ?? ''
      if (optionText.includes(poNumber) || (poNumber.length === 0 && index > 0)) {
        matchedOptionValue = await option.getAttribute('value')
        break
      }
    }

    if (matchedOptionValue) {
      await this.openPOSelect.selectOption(matchedOptionValue)
    } else {
      await this.openPOSelect.selectOption({ index: 1 })
    }

    await this.startGRNButton.click()
  }

  async scanBarcode(lineIndex: number, barcode: string): Promise<void> {
    void lineIndex
    await this.barcodeInput.fill(barcode)
    await this.receiveLineButton.click()
  }

  async scanBarcodeWithEnter(barcode: string): Promise<void> {
    await this.barcodeInput.fill(barcode)
    await this.barcodeInput.press('Enter')
  }

  async clickConfirm(): Promise<void> {
    await this.completeGRNButton.click()
  }

  async refreshPage(): Promise<void> {
    await this.page.reload()
  }

  // Assertions
  async assertOpenPOsVisible(): Promise<void> {
    await expect(this.openPOSelect).toBeVisible()
  }

  async assertLineScannerVisible(): Promise<void> {
    await expect(this.page.getByText('GRN Line Scanner', { exact: true })).toBeVisible()
  }

  async assertSummaryVisible(): Promise<void> {
    await expect(
      this.page.getByText('Completion impact', { exact: true }),
    ).toBeVisible()
    await expect(this.completeGRNButton).toBeVisible()
  }

  async assertOverReceiptWarning(): Promise<void> {
    await expect(this.page.getByText(/over|exceed|warning/i).first()).toBeVisible()
  }

  async assertConfirmationBannerVisible(): Promise<void> {
    await expect(
      this.page.getByText('Saved progress found', { exact: true }),
    ).toBeVisible()
  }

  async assertSessionCleared(): Promise<void> {
    await expect(this.openPOSelect).toBeVisible()
    await expect(
      this.page.getByText('Saved progress found', { exact: true }),
    ).not.toBeVisible()
  }
}
