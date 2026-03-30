// client/tests/e2e/pages/AuthPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class AuthPage extends BasePage {
  // Locators
  private readonly emailInput: Locator
  private readonly passwordInput: Locator
  private readonly signInButton: Locator
  private readonly loginFailedText: Locator
  private readonly receiveGoodsNavItem: Locator
  private readonly purchaseOrdersNavItem: Locator
  private readonly dashboardNavItem: Locator
  private readonly suppliersNavItem: Locator
  private readonly productsNavItem: Locator
  private readonly backordersNavItem: Locator
  private readonly stockLedgerNavItem: Locator
  private readonly usersNavItem: Locator
  private readonly reportsNavItem: Locator

  constructor(page: Page) {
    super(page)
    this.emailInput = this.page.getByRole('textbox', { name: 'Email' })
    this.passwordInput = this.page.getByRole('textbox', { name: 'Password' })
    this.signInButton = this.page.getByRole('button', { name: /sign in/i })
    this.loginFailedText = this.page.getByText(/login failed|invalid/i)

    this.receiveGoodsNavItem = this.page.getByRole('link', {
      name: 'Receive Goods',
    })
    this.purchaseOrdersNavItem = this.page.getByRole('link', {
      name: 'Purchase Orders',
    })
    this.dashboardNavItem = this.page.getByRole('link', { name: 'Dashboard' })
    this.suppliersNavItem = this.page.getByRole('link', { name: 'Suppliers' })
    this.productsNavItem = this.page.getByRole('link', { name: 'Products' })
    this.backordersNavItem = this.page.getByRole('link', { name: 'Backorders' })
    this.stockLedgerNavItem = this.page.getByRole('link', { name: 'Stock Ledger' })
    this.usersNavItem = this.page.getByRole('link', { name: 'Users' })
    this.reportsNavItem = this.page.getByRole('link', { name: 'Reports' })
  }

  // Actions
  async goto(path: string = '/login'): Promise<void> {
    await super.goto(path)
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email)
  }

  async fillPassword(password: string): Promise<void> {
    await this.passwordInput.fill(password)
  }

  async submitForm(): Promise<void> {
    await this.signInButton.click()
  }

  async login(email: string, password: string): Promise<void> {
    await this.fillEmail(email)
    await this.fillPassword(password)
    await this.submitForm()
  }

  async logout(): Promise<void> {
    await this.page
      .getByRole('button', { name: /stockbridge|admin|manager|staff/i })
      .click()
  }

  // Assertions
  async shouldShowError(): Promise<void> {
    await expect(this.loginFailedText).toBeVisible()
  }

  async shouldBeOnPage(path: string): Promise<void> {
    await expect(this.page).toHaveURL(new RegExp(`${path}$`))
  }

  async shouldHaveSidebarCount(expectedCount: number): Promise<void> {
    const navItems = [
      this.dashboardNavItem,
      this.purchaseOrdersNavItem,
      this.suppliersNavItem,
      this.productsNavItem,
      this.receiveGoodsNavItem,
      this.backordersNavItem,
      this.stockLedgerNavItem,
      this.usersNavItem,
      this.reportsNavItem,
    ]

    let visibleCount = 0
    for (const navItem of navItems) {
      if (await navItem.isVisible().catch(() => false)) {
        visibleCount += 1
      }
    }

    expect(visibleCount).toBe(expectedCount)
  }
}
