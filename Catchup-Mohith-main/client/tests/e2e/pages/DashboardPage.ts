// client/tests/e2e/pages/DashboardPage.ts
import { expect, type Locator, type Page } from '@playwright/test'

import { BasePage } from './BasePage'

export class DashboardPage extends BasePage {
  // Locators
  private readonly pageTitle: Locator
  private readonly systemHealthTitle: Locator

  constructor(page: Page) {
    super(page)
    this.pageTitle = this.page.getByText('Dashboard', { exact: true })
    this.systemHealthTitle = this.page.getByText('System Health', { exact: true })
  }

  // Actions
  async goto(): Promise<void> {
    await super.goto('/dashboard')
  }

  async clickMetricCard(label: string): Promise<void> {
    await this.page
      .getByRole('heading', { name: label, exact: true })
      .locator('..')
      .getByRole('button', { name: 'View' })
      .click()
  }

  // Assertions
  async assertMetricCardVisible(label: string): Promise<void> {
    await expect(
      this.page.getByRole('heading', { name: label, exact: true }),
    ).toBeVisible()
  }

  async assertSystemHealthVisible(): Promise<void> {
    await expect(this.systemHealthTitle).toBeVisible()
    await expect(this.page.getByText('Database', { exact: true })).toBeVisible()
    await expect(this.page.getByText('Redis', { exact: true })).toBeVisible()
    await expect(this.page.getByText('Temporal', { exact: true })).toBeVisible()
  }

  async assertStaffView(): Promise<void> {
    await expect(this.pageTitle).toBeVisible()
    await this.assertMetricCardVisible('Total Products')
    await this.assertMetricCardVisible('Low Stock')
    await this.assertMetricCardVisible('Pending GRNs')
    await expect(
      this.page.getByRole('heading', { name: 'Open POs', exact: true }),
    ).not.toBeVisible()
  }

  async assertManagerView(): Promise<void> {
    await expect(this.pageTitle).toBeVisible()
    await this.assertMetricCardVisible('Total Products')
    await this.assertMetricCardVisible('Open POs')
    await this.assertMetricCardVisible('Overdue Backorders')
    await this.assertMetricCardVisible('Total Suppliers')
  }

  async assertAdminView(): Promise<void> {
    await this.assertManagerView()
    await this.assertMetricCardVisible('Total Users')
    await this.assertMetricCardVisible('Email Failures')
    await this.assertSystemHealthVisible()
  }

  async assertLoadingSkeletonHidden(): Promise<void> {
    await expect(this.page.locator('.cds--skeleton__text').first()).not.toBeVisible()
  }
}
