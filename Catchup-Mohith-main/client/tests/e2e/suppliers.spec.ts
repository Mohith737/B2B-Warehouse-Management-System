// client/tests/e2e/suppliers.spec.ts
import { expect, test } from '@playwright/test'

import { AuthPage, SuppliersPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'
const MANAGER_EMAIL = process.env.E2E_MANAGER_EMAIL ?? 'manager@stockbridge.com'
const MANAGER_PASSWORD = process.env.E2E_MANAGER_PASSWORD ?? 'ManagerPass123!'

test.describe('Suppliers E2E', () => {
  let authPage: AuthPage
  let suppliersPage: SuppliersPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    suppliersPage = new SuppliersPage(page)
  })

  test('test_suppliers_page_loads_for_manager', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await suppliersPage.goto()
    await suppliersPage.assertPageRendered()
  })

  test('test_suppliers_staff_redirects_to_unauthorized', async () => {
    await authPage.goto('/login')
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await suppliersPage.goto()
    await suppliersPage.assertRedirectedToUnauthorized()
  })

  test('test_suppliers_tier_filter_silver', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await suppliersPage.goto()

    await suppliersPage.filterByTier('Silver')
    await suppliersPage.assertAllRowsMatchTier('Silver')
  })

  test('test_suppliers_tier_filter_gold', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await suppliersPage.goto()

    await suppliersPage.filterByTier('Gold')
    await suppliersPage.assertAllRowsMatchTier('Gold')
  })

  test('test_suppliers_search_filters_results', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await suppliersPage.goto()

    const initialCount = await suppliersPage.getRowCount()
    const firstSupplier = await suppliersPage.getFirstSupplierName()

    if (firstSupplier.length > 0) {
      await suppliersPage.search(firstSupplier.slice(0, 3))
      await suppliersPage.assertSupplierVisible(firstSupplier)
      const filteredCount = await suppliersPage.getRowCount()
      expect(filteredCount).toBeLessThanOrEqual(initialCount)
      return
    }

    await suppliersPage.search('SUPPLIER-DOES-NOT-EXIST-12345')
    await suppliersPage.assertPageRendered()
  })
})
