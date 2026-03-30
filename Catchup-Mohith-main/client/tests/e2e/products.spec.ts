// client/tests/e2e/products.spec.ts
import { expect, test } from '@playwright/test'

import { AuthPage, ProductsPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'
const MANAGER_EMAIL = process.env.E2E_MANAGER_EMAIL ?? 'manager@stockbridge.com'
const MANAGER_PASSWORD = process.env.E2E_MANAGER_PASSWORD ?? 'ManagerPass123!'

test.describe('Products E2E', () => {
  let authPage: AuthPage
  let productsPage: ProductsPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    productsPage = new ProductsPage(page)
  })

  test('test_products_page_loads_for_staff', async () => {
    await authPage.goto('/login')
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await productsPage.goto()
    await productsPage.assertPageRendered()
  })

  test('test_products_page_loads_for_manager', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await productsPage.goto()
    await productsPage.assertPageRendered()
  })

  test('test_products_search_filters_results', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await productsPage.goto()

    const initialCount = await productsPage.getRowCount()
    const firstCellText = await productsPage.getFirstCellText()

    if (firstCellText.length > 0) {
      await productsPage.search(firstCellText.slice(0, 3))
      await productsPage.assertProductVisible(firstCellText)
      const filteredCount = await productsPage.getRowCount()
      expect(filteredCount).toBeLessThanOrEqual(initialCount)
      return
    }

    await productsPage.search('NONEXISTENT-SKU-SEARCH')
    await productsPage.assertEmptyState()
  })

  test('test_products_pagination_works', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await productsPage.goto()

    const beforeRange = await productsPage.getPaginationRange()
    await productsPage.clickNextPage()
    const afterRange = await productsPage.getPaginationRange()

    expect(afterRange).not.toBe(beforeRange)
  })

  test('test_products_empty_state_shown_when_no_results', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await productsPage.goto()

    await productsPage.search('SKU-DOES-NOT-EXIST-12345')
    await productsPage.assertEmptyState()
  })
})
