// client/src/features/dashboard/types/index.ts
import type { ComponentType } from 'react'

import type { UserRole } from '../../../stores/authStore'

export type DashboardStockMovement = {
  product_name: string
  product_sku: string
  quantity_change: number | string
  change_type: string
  balance_after: number | string
  created_at: string
}

export type DashboardApiRead = {
  total_products: number
  low_stock_count: number
  pending_grns: number
  total_stock_units?: number
  out_of_stock_count?: number
  open_pos?: number
  total_suppliers?: number
  overdue_backorders?: number
  stock_movement_7days?: Array<{
    day: string
    stock_in: number | string
    stock_out: number | string
  }>
  low_stock_products?: DashboardLowStockProduct[]
  recent_grns?: Array<{
    id: string
    grn_no?: string
    grnNo?: string
    supplier?: string
    supplier_name?: string
    date?: string
    created_at?: string
    status: string
  }>
  top_suppliers?: Array<{
    rank?: number
    supplier_name?: string
    supplierName?: string
    delivery_count?: number
    deliveryCount?: number
  }>
  recent_stock_movements?: DashboardStockMovement[]
  recent_activity?: DashboardStockMovement[]
}

export type DashboardMetricData = {
  totalStockUnits: number
  lowStockItems: number
  outOfStockItems: number
  openPOs: number
  openBackorders: number
  activeSuppliers: number
  stockMovement7Days: Array<{
    day: string
    stockIn: number
    stockOut: number
  }>
}

export type DashboardLowStockProduct = {
  id: string
  name: string
  sku: string
  current_stock: number | string
  reorder_point: number | string
}

export type DashboardRecentGRN = {
  id: string
  grnNo: string
  supplier: string
  date: string
  status: string
}

export type DashboardTopSupplier = {
  rank: number
  supplierName: string
  deliveryCount: number
}

export type DashboardViewProps = {
  role: UserRole
}

export type DashboardRead = DashboardApiRead

export type DashboardSectionProps = {
  data: DashboardRead | null
  isLoading: boolean
  error: string | null
  onRetry: () => void
}

export type DashboardSectionComponent = ComponentType<DashboardSectionProps>

export type DashboardSectionMap = Record<UserRole, DashboardSectionComponent>
