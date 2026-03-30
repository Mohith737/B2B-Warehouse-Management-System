// client/tests/e2e/dashboard.spec.ts
import { expect, test } from '@playwright/test'

import { AuthPage, DashboardPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'
const MANAGER_EMAIL = process.env.E2E_MANAGER_EMAIL ?? 'manager@stockbridge.com'
const MANAGER_PASSWORD = process.env.E2E_MANAGER_PASSWORD ?? 'ManagerPass123!'
const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@stockbridge.com'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'AdminPass123!'

test.describe('Dashboard E2E', () => {
  let authPage: AuthPage
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    dashboardPage = new DashboardPage(page)
  })

  test('test_dashboard_staff_shows_limited_metrics', async () => {
    await authPage.goto('/login')
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await dashboardPage.goto()
    await dashboardPage.assertStaffView()
  })

  test('test_dashboard_manager_shows_extended_metrics', async () => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await dashboardPage.goto()
    await dashboardPage.assertManagerView()
  })

  test('test_dashboard_admin_shows_system_health', async () => {
    await authPage.goto('/login')
    await authPage.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    await dashboardPage.goto()
    await dashboardPage.assertAdminView()
  })

  test('test_dashboard_low_stock_card_navigates_to_products', async ({ page }) => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await dashboardPage.goto()
    await dashboardPage.clickMetricCard('Low Stock')
    await expect(page).toHaveURL(/\/products$/)
  })

  test('test_dashboard_background_refetch_no_skeleton_flash', async ({ page }) => {
    await authPage.goto('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await dashboardPage.goto()
    await dashboardPage.assertManagerView()
    await page.waitForTimeout(500)
    await dashboardPage.assertLoadingSkeletonHidden()
  })
})
