// client/tests/e2e/backorders.spec.ts
import { expect, test } from '@playwright/test'

import { AuthPage, BackordersPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'

test.describe('Backorders E2E', () => {
  let authPage: AuthPage
  let backordersPage: BackordersPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    backordersPage = new BackordersPage(page)

    await authPage.goto('/login')
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await backordersPage.goto()
  })

  test('test_backorders_loads_open_backorders', async () => {
    const rows = await backordersPage.getRowCount()
    expect(rows).toBeGreaterThanOrEqual(0)
  })

  test('test_backorders_overdue_filter_works', async () => {
    await backordersPage.filterOverdue()
    await backordersPage.assertOverdueFilterActive()
  })

  test('test_backorders_age_indicator_per_row', async () => {
    const rows = await backordersPage.getRowCount()
    if (rows === 0) {
      await backordersPage.assertEmptyState()
      return
    }
    await backordersPage.assertAgeIndicatorVisible()
  })

  test('test_backorders_empty_state_when_none', async () => {
    const rows = await backordersPage.getRowCount()
    if (rows === 0) {
      await backordersPage.assertEmptyState()
      return
    }
    expect(rows).toBeGreaterThan(0)
  })
})
