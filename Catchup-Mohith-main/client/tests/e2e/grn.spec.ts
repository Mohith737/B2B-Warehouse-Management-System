// client/tests/e2e/grn.spec.ts
import { test } from '@playwright/test'

import { AuthPage, GRNPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'
const PO_NUMBER = process.env.E2E_GRN_PO_NUMBER ?? ''
const BARCODE = process.env.E2E_GRN_BARCODE ?? '1234567890123'

test.describe('GRN E2E', () => {
  let authPage: AuthPage
  let grnPage: GRNPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    grnPage = new GRNPage(page)

    await authPage.goto('/login')
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await grnPage.goto()
  })

  test('test_grn_page_shows_acknowledged_pos', async () => {
    await grnPage.assertOpenPOsVisible()
  })

  test('test_grn_select_po_shows_line_scanner', async () => {
    await grnPage.selectPO(PO_NUMBER)
    await grnPage.assertLineScannerVisible()
  })

  test('test_grn_barcode_enter_key_triggers_scan', async () => {
    await grnPage.selectPO(PO_NUMBER)
    await grnPage.scanBarcodeWithEnter(BARCODE)
    await grnPage.assertSummaryVisible()
  })

  test('test_grn_over_receipt_shows_warning', async () => {
    await grnPage.selectPO(PO_NUMBER)
    await grnPage.scanBarcode(0, BARCODE)
    await grnPage.scanBarcode(0, BARCODE)
    await grnPage.assertOverReceiptWarning()
  })

  test('test_grn_summary_panel_shown_before_confirm', async () => {
    await grnPage.selectPO(PO_NUMBER)
    await grnPage.assertSummaryVisible()
  })

  test('test_grn_confirmation_banner_on_resume', async () => {
    await grnPage.selectPO(PO_NUMBER)
    await grnPage.refreshPage()
    await grnPage.assertConfirmationBannerVisible()
  })

  test('test_grn_completion_clears_session', async () => {
    await grnPage.selectPO(PO_NUMBER)
    await grnPage.clickConfirm()
    await grnPage.assertSessionCleared()
  })
})
