// client/src/features/dashboard/hooks/useDashboardMetricsQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { DashboardApiRead, DashboardMetricData } from '../types'

type ProductsListResponse = {
  data: Array<{
    current_stock: number | string
  }>
  meta: {
    total: number
  }
}

function toNumber(value: number | string | null | undefined): number {
  if (typeof value === 'number') {
    return value
  }
  const parsed = Number.parseFloat(String(value ?? 0))
  return Number.isNaN(parsed) ? 0 : parsed
}

function normalizeEnvelope<T>(payload: ApiResponse<T> | T): T {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'data' in payload &&
    Object.keys(payload as object).length === 1
  ) {
    return (payload as ApiResponse<T>).data
  }

  return payload as T
}

function last7DayBuckets(): Array<{
  dateKey: string
  day: string
  stockIn: number
  stockOut: number
}> {
  const format = new Intl.DateTimeFormat('en-US', { weekday: 'short' })
  return Array.from({ length: 7 }).map((_, index) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - index))
    const dateKey = date.toISOString().slice(0, 10)
    return {
      dateKey,
      day: format.format(date),
      stockIn: 0,
      stockOut: 0,
    }
  })
}

async function fetchDashboardMetrics(): Promise<DashboardMetricData> {
  const [dashboardResponse, productsResponse] = await Promise.all([
    apiClient.get<ApiResponse<DashboardApiRead> | DashboardApiRead>('/dashboard'),
    apiClient.get<ApiResponse<ProductsListResponse> | ProductsListResponse>(
      '/products',
      {
        params: {
          page: 1,
          page_size: 100,
        },
      },
    ),
  ])

  const dashboard = normalizeEnvelope<DashboardApiRead>(dashboardResponse.data)
  const productsList = normalizeEnvelope<ProductsListResponse>(productsResponse.data)

  const movements = dashboard.recent_activity ?? dashboard.recent_stock_movements ?? []
  const movementByDate = new Map(
    last7DayBuckets().map((entry) => [entry.dateKey, entry]),
  )

  for (const movement of movements) {
    const dateKey = String(movement.created_at).slice(0, 10)
    const bucket = movementByDate.get(dateKey)
    if (!bucket) {
      continue
    }
    const qty = toNumber(movement.quantity_change)
    if (qty >= 0) {
      bucket.stockIn += qty
    } else {
      bucket.stockOut += Math.abs(qty)
    }
  }

  const products = productsList.data ?? []
  const totalStockUnits = products.reduce(
    (total, product) => total + toNumber(product.current_stock),
    0,
  )

  const outOfStockItems = products.filter(
    (product) => toNumber(product.current_stock) <= 0,
  ).length

  return {
    totalStockUnits,
    lowStockItems: dashboard.low_stock_count ?? 0,
    outOfStockItems,
    openPOs: dashboard.open_pos ?? 0,
    openBackorders: dashboard.overdue_backorders ?? 0,
    activeSuppliers: dashboard.total_suppliers ?? 0,
    stockMovement7Days: Array.from(movementByDate.values()).map((entry) => ({
      day: entry.day,
      stockIn: entry.stockIn,
      stockOut: entry.stockOut,
    })),
  }
}

export function useDashboardMetricsQuery() {
  return useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
    placeholderData: {
      totalStockUnits: 0,
      lowStockItems: 0,
      outOfStockItems: 0,
      openPOs: 0,
      openBackorders: 0,
      activeSuppliers: 0,
      stockMovement7Days: [],
    },
    refetchInterval: 30_000,
    retry: 1,
  })
}
