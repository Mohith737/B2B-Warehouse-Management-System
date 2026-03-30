// client/tests/e2e/po-wizard.spec.ts
import { test } from '@playwright/test'

import { AuthPage, POWizardPage } from './pages'

const MANAGER_EMAIL = process.env.E2E_MANAGER_EMAIL ?? 'manager@stockbridge.com'
const MANAGER_PASSWORD = process.env.E2E_MANAGER_PASSWORD ?? 'ManagerPass123!'
const SUPPLIER_NAME = process.env.E2E_PO_SUPPLIER_NAME ?? 'Northwind Traders'

test.describe('PO Wizard E2E', () => {
  let authPage: AuthPage
  let poWizardPage: POWizardPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    poWizardPage = new POWizardPage(page)

    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await poWizardPage.goto()
  })

  test('test_po_wizard_renders_step_1_on_load', async () => {
    await poWizardPage.assertStep(1)
  })

  test('test_po_wizard_next_disabled_without_supplier', async () => {
    await poWizardPage.assertNextDisabled()
  })

  test('test_po_wizard_select_supplier_enables_next', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.assertNextEnabled()
  })

  test('test_po_wizard_step_2_add_line_updates_total', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.clickNext()
    await poWizardPage.assertStep(2)
    await poWizardPage.addLine()
    await poWizardPage.clickNext()
    await poWizardPage.assertEstimatedTotalUpdated()
  })

  test('test_po_wizard_step_3_review_shows_all_lines', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.clickNext()
    await poWizardPage.addLine()
    await poWizardPage.clickNext()
    await poWizardPage.assertStep(3)
    await poWizardPage.assertReviewLineCount(1)
  })

  test('test_po_wizard_credit_warning_shown_near_limit', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.clickNext()
    await poWizardPage.addLine()
    await poWizardPage.clickNext()
    await poWizardPage.assertCreditWarningVisible()
  })

  test('test_po_wizard_submit_creates_po_shows_confirm', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.clickNext()
    await poWizardPage.addLine()
    await poWizardPage.clickNext()
    await poWizardPage.clickSubmit()
    await poWizardPage.assertStep(4)
    await poWizardPage.assertPONumberVisible()
  })

  test('test_po_wizard_sessionstorage_persists_on_refresh', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.refreshPage()
    await poWizardPage.assertConfirmationBannerVisible()
  })

  test('test_po_wizard_confirmation_banner_on_resume', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.refreshPage()
    await poWizardPage.assertConfirmationBannerVisible()
    await poWizardPage.clickContinue()
    await poWizardPage.assertStep(1)
  })

  test('test_po_wizard_start_fresh_clears_session', async () => {
    await poWizardPage.selectSupplier(SUPPLIER_NAME)
    await poWizardPage.refreshPage()
    await poWizardPage.assertConfirmationBannerVisible()
    await poWizardPage.clickStartFresh()
    await poWizardPage.assertStep(1)
    await poWizardPage.assertNextDisabled()
  })
})
