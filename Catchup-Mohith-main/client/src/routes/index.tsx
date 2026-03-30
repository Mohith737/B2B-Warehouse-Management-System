// client/src/routes/index.tsx
import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'

import { LoadingSkeleton } from '../design-system'
import { HomeRedirect } from './HomeRedirect'
import { ProtectedRoute } from './ProtectedRoute'

const LoginPage = lazy(() => import('../pages/LoginPage'))
const UnauthorizedPage = lazy(() => import('../pages/UnauthorizedPage'))
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'))
const ProductsPage = lazy(() => import('../pages/ProductsPage'))
const SuppliersPage = lazy(() => import('../pages/SuppliersPage'))
const PurchaseOrdersPage = lazy(() => import('../pages/PurchaseOrdersPage'))
const CreatePOPage = lazy(() => import('../pages/CreatePOPage'))
const GRNPage = lazy(() => import('../pages/GRNPage'))
const DashboardPage = lazy(() => import('../pages/DashboardPage'))
const StockLedgerPage = lazy(() => import('../pages/StockLedgerPage'))
const BackordersPage = lazy(() => import('../pages/BackordersPage'))
const AdminUsersPage = lazy(() => import('../pages/AdminUsersPage'))
const ReportsPage = lazy(() => import('../pages/ReportsPage'))

const withSuspense = (element: JSX.Element) => (
  <Suspense fallback={<LoadingSkeleton />}>{element}</Suspense>
)

export const appRouter = createBrowserRouter([
  { path: '/', element: withSuspense(<HomeRedirect />) },
  { path: '/login', element: withSuspense(<LoginPage />) },
  { path: '/unauthorized', element: withSuspense(<UnauthorizedPage />) },
  {
    path: '/products',
    element: withSuspense(
      <ProtectedRoute>
        <ProductsPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/suppliers',
    element: withSuspense(
      <ProtectedRoute>
        <SuppliersPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/purchase-orders',
    element: withSuspense(
      <ProtectedRoute>
        <PurchaseOrdersPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/purchase-orders/new',
    element: withSuspense(
      <ProtectedRoute>
        <CreatePOPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/grns',
    element: withSuspense(
      <ProtectedRoute>
        <GRNPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/dashboard',
    element: withSuspense(
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/stock-ledger',
    element: withSuspense(
      <ProtectedRoute>
        <StockLedgerPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/backorders',
    element: withSuspense(
      <ProtectedRoute>
        <BackordersPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/admin/users',
    element: withSuspense(
      <ProtectedRoute>
        <AdminUsersPage />
      </ProtectedRoute>,
    ),
  },
  {
    path: '/reports',
    element: withSuspense(
      <ProtectedRoute>
        <ReportsPage />
      </ProtectedRoute>,
    ),
  },
  { path: '*', element: withSuspense(<NotFoundPage />) },
])
