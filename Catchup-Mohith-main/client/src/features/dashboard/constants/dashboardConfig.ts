// client/src/features/dashboard/constants/dashboardConfig.ts
import {
  DashboardAdminSection,
  DashboardManagerSection,
  DashboardStaffSection,
} from '../../../design-system/ui/organisms'
import type { DashboardSectionComponent, DashboardSectionMap } from '../types'

export const DASHBOARD_QUERY_CONFIG = {
  staleTimeMs: 30_000,
  refetchIntervalMs: 30_000,
} as const

export const METRIC_DEFINITIONS = [
  {
    key: 'totalStockUnits',
    title: 'Total Stock',
    unit: 'units',
    trend: 'neutral' as const,
  },
  {
    key: 'lowStockItems',
    title: 'Low Stock Items',
    unit: 'products',
    trend: 'down' as const,
  },
  {
    key: 'outOfStockItems',
    title: 'Out of Stock',
    unit: 'products',
    trend: 'down' as const,
  },
  { key: 'openPOs', title: 'Open POs', unit: 'orders', trend: 'neutral' as const },
  {
    key: 'openBackorders',
    title: 'Open Backorders',
    unit: 'items',
    trend: 'neutral' as const,
  },
  {
    key: 'activeSuppliers',
    title: 'Active Suppliers',
    unit: 'suppliers',
    trend: 'neutral' as const,
  },
] as const

export const DASHBOARD_SECTION: DashboardSectionMap = {
  warehouse_staff: DashboardStaffSection as DashboardSectionComponent,
  procurement_manager: DashboardManagerSection as DashboardSectionComponent,
  admin: DashboardAdminSection as DashboardSectionComponent,
}
