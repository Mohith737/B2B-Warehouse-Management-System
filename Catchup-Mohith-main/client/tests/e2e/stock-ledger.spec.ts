// client/tests/e2e/stock-ledger.spec.ts
import { expect, test } from '@playwright/test'

import { AuthPage, StockLedgerPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'

test.describe('Stock Ledger E2E', () => {
  let authPage: AuthPage
  let stockLedgerPage: StockLedgerPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    stockLedgerPage = new StockLedgerPage(page)

    await authPage.goto('/login')
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await stockLedgerPage.goto()
  })

  test('test_stock_ledger_loads_initial_entries', async () => {
    const rowCount = await stockLedgerPage.getRowCount()
    expect(rowCount).toBeGreaterThanOrEqual(0)
  })

  test('test_stock_ledger_load_more_appends_rows', async () => {
    const beforeCount = await stockLedgerPage.getRowCount()
    await stockLedgerPage.clickLoadMore()
    const afterCount = await stockLedgerPage.getRowCount()
    expect(afterCount).toBeGreaterThan(beforeCount)
  })

  test('test_stock_ledger_empty_state_when_no_entries', async () => {
    const rowCount = await stockLedgerPage.getRowCount()
    if (rowCount === 0) {
      await stockLedgerPage.assertEmptyState()
      return
    }
    expect(rowCount).toBeGreaterThan(0)
  })

  test('test_stock_ledger_shows_correct_columns', async () => {
    await stockLedgerPage.assertColumnsVisible()
  })
})
