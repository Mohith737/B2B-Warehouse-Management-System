// client/src/features/dashboard/hooks/useDashboardTopSuppliersQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { DashboardTopSupplier } from '../types'

type PORead = {
  supplier_name: string
}

type POListResponse = {
  data: PORead[]
  meta: {
    total: number
  }
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

async function fetchDashboardTopSuppliers(): Promise<DashboardTopSupplier[]> {
  const response = await apiClient.get<ApiResponse<POListResponse> | POListResponse>(
    '/purchase-orders',
    {
      params: {
        page: 1,
        page_size: 50,
        status: 'closed',
      },
    },
  )

  const purchaseOrders = normalizeEnvelope<POListResponse>(response.data).data ?? []

  const counts = purchaseOrders.reduce<Record<string, number>>((accumulator, po) => {
    const supplierName = po.supplier_name || 'Unknown Supplier'
    return {
      ...accumulator,
      [supplierName]: (accumulator[supplierName] ?? 0) + 1,
    }
  }, {})

  return Object.entries(counts)
    .map(([supplierName, deliveryCount]) => ({
      supplierName,
      deliveryCount,
    }))
    .sort((a, b) => b.deliveryCount - a.deliveryCount)
    .slice(0, 5)
    .map((entry, index) => ({
      rank: index + 1,
      supplierName: entry.supplierName,
      deliveryCount: entry.deliveryCount,
    }))
}

export function useDashboardTopSuppliersQuery() {
  return useQuery({
    queryKey: ['dashboard-top-suppliers'],
    queryFn: fetchDashboardTopSuppliers,
    placeholderData: [],
    refetchInterval: 60_000,
    retry: 1,
  })
}
