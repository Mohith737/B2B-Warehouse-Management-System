// client/tests/e2e/auth.spec.ts
import { test } from '@playwright/test'

import { AuthPage } from './pages'

const STAFF_EMAIL = process.env.E2E_STAFF_EMAIL ?? 'staff@stockbridge.com'
const STAFF_PASSWORD = process.env.E2E_STAFF_PASSWORD ?? 'StaffPass123!'
const MANAGER_EMAIL = process.env.E2E_MANAGER_EMAIL ?? 'manager@stockbridge.com'
const MANAGER_PASSWORD = process.env.E2E_MANAGER_PASSWORD ?? 'ManagerPass123!'
const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@stockbridge.com'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'AdminPass123!'

test.describe('Auth E2E', () => {
  let authPage: AuthPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    await authPage.goto()
  })

  test('test_login_staff_redirects_to_grns', async () => {
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await authPage.shouldBeOnPage('/grns')
  })

  test('test_login_manager_redirects_to_pos', async () => {
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await authPage.shouldBeOnPage('/purchase-orders')
  })

  test('test_login_admin_redirects_to_dashboard', async () => {
    await authPage.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    await authPage.shouldBeOnPage('/dashboard')
  })

  test('test_login_invalid_credentials_shows_error', async () => {
    await authPage.login('invalid@stockbridge.com', 'wrong-password')
    await authPage.shouldShowError()
  })

  test('test_protected_route_without_auth_redirects_to_login', async () => {
    await authPage.goto('/dashboard')
    await authPage.shouldBeOnPage('/login')
  })

  test('test_post_login_redirect_returns_to_original_route', async () => {
    await authPage.goto('/reports')
    await authPage.shouldBeOnPage('/login')
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await authPage.shouldBeOnPage('/reports')
  })

  test('test_logout_redirects_to_login', async () => {
    await authPage.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    await authPage.logout()
    await authPage.shouldBeOnPage('/login')
  })

  test('test_sidebar_staff_shows_3_items', async () => {
    await authPage.login(STAFF_EMAIL, STAFF_PASSWORD)
    await authPage.shouldHaveSidebarCount(3)
  })

  test('test_sidebar_manager_shows_7_items', async () => {
    await authPage.login(MANAGER_EMAIL, MANAGER_PASSWORD)
    await authPage.shouldHaveSidebarCount(7)
  })

  test('test_sidebar_admin_shows_9_items', async () => {
    await authPage.login(ADMIN_EMAIL, ADMIN_PASSWORD)
    await authPage.shouldHaveSidebarCount(9)
  })
})
