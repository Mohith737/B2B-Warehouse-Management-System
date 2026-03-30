// client/tests/e2e/pages/POWizardPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class POWizardPage extends BasePage {
  // Locators
  private readonly supplierSelect: Locator
  private readonly nextButton: Locator
  private readonly previousButton: Locator
  private readonly submitButton: Locator
  private readonly continueButton: Locator
  private readonly startFreshButton: Locator
  private readonly addLineButton: Locator
  private readonly reviewTotalText: Locator
  private readonly poCreatedTitle: Locator

  constructor(page: Page) {
    super(page)
    this.supplierSelect = this.page.getByRole('combobox', { name: 'Supplier' })
    this.nextButton = this.page.getByRole('button', { name: 'Next' })
    this.previousButton = this.page.getByRole('button', { name: 'Previous' })
    this.submitButton = this.page.getByRole('button', { name: 'Submit PO' })
    this.continueButton = this.page.getByRole('button', { name: 'Continue' })
    this.startFreshButton = this.page.getByRole('button', { name: 'Start Fresh' })
    this.addLineButton = this.page.getByRole('button', { name: 'Add Line' })
    this.reviewTotalText = this.page.getByText(/Estimated Total:/)
    this.poCreatedTitle = this.page.getByText('Purchase order created', { exact: true })
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/purchase-orders/new')
  }

  async selectSupplier(name: string): Promise<void> {
    await this.supplierSelect.selectOption({ label: name })
  }

  async clickNext(): Promise<void> {
    await this.nextButton.click()
  }

  async clickBack(): Promise<void> {
    await this.previousButton.click()
  }

  async clickContinue(): Promise<void> {
    await this.continueButton.click()
  }

  async clickStartFresh(): Promise<void> {
    await this.startFreshButton.click()
  }

  async addLine(): Promise<void> {
    await this.addLineButton.click()
  }

  async clickSubmit(): Promise<void> {
    await this.submitButton.click()
  }

  async refreshPage(): Promise<void> {
    await this.page.reload()
  }

  // Assertions
  async assertStep(step: number): Promise<void> {
    if (step === 1) {
      await expect(
        this.page.getByText('Select supplier', { exact: true }),
      ).toBeVisible()
      return
    }

    if (step === 2) {
      await expect(
        this.page
          .getByText('PO Lines', { exact: true })
          .or(this.page.getByText('No lines', { exact: true }))
          .first(),
      ).toBeVisible()
      return
    }

    if (step === 3) {
      await expect(this.reviewTotalText).toBeVisible()
      return
    }

    await expect(this.poCreatedTitle).toBeVisible()
  }

  async assertNextDisabled(): Promise<void> {
    await expect(this.nextButton).toBeDisabled()
  }

  async assertNextEnabled(): Promise<void> {
    await expect(this.nextButton).toBeEnabled()
  }

  async assertConfirmationBannerVisible(): Promise<void> {
    await expect(
      this.page.getByText('Saved progress found', { exact: true }),
    ).toBeVisible()
  }

  async assertConfirmationBannerHidden(): Promise<void> {
    await expect(
      this.page.getByText('Saved progress found', { exact: true }),
    ).not.toBeVisible()
  }

  async assertEstimatedTotalUpdated(): Promise<void> {
    await expect(this.page.getByText(/Estimated Total: (?!0\.00)\d+/)).toBeVisible()
  }

  async assertReviewLineCount(count: number): Promise<void> {
    await expect(this.page.getByText(`Lines: ${count}`, { exact: true })).toBeVisible()
  }

  async assertCreditWarningVisible(): Promise<void> {
    await expect(this.page.getByText(/credit|limit/i)).toBeVisible()
  }

  async assertPONumberVisible(): Promise<void> {
    await expect(this.page.getByText(/PO .* was submitted\./)).toBeVisible()
  }
}
