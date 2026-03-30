// client/src/features/dashboard/hooks/useDashboardLowStockQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { DashboardLowStockProduct } from '../types'

type LowStockListResponse = {
  data: DashboardLowStockProduct[]
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

async function fetchDashboardLowStock(): Promise<DashboardLowStockProduct[]> {
  const response = await apiClient.get<
    ApiResponse<LowStockListResponse> | LowStockListResponse
  >('/dashboard/low-stock', {
    params: {
      page: 1,
      page_size: 5,
    },
  })

  const payload = normalizeEnvelope<LowStockListResponse>(response.data)
  return payload.data ?? []
}

export function useDashboardLowStockQuery() {
  return useQuery({
    queryKey: ['dashboard-low-stock'],
    queryFn: fetchDashboardLowStock,
    placeholderData: [],
    refetchInterval: 30_000,
    retry: 1,
  })
}
