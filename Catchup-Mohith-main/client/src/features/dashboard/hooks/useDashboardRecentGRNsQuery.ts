// client/src/features/dashboard/hooks/useDashboardRecentGRNsQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { DashboardRecentGRN } from '../types'

type GRNRead = {
  id: string
  po_id: string
  status: string
  created_at: string
}

type GRNListResponse = {
  data: GRNRead[]
  meta: {
    total: number
  }
}

type PORead = {
  id: string
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

async function fetchDashboardRecentGRNs(): Promise<DashboardRecentGRN[]> {
  const [grnsResponse, posResponse] = await Promise.all([
    apiClient.get<ApiResponse<GRNListResponse> | GRNListResponse>('/grns', {
      params: {
        page: 1,
        page_size: 5,
      },
    }),
    apiClient.get<ApiResponse<POListResponse> | POListResponse>('/purchase-orders', {
      params: {
        page: 1,
        page_size: 50,
      },
    }),
  ])

  const grns = normalizeEnvelope<GRNListResponse>(grnsResponse.data).data ?? []
  const purchaseOrders = normalizeEnvelope<POListResponse>(posResponse.data).data ?? []
  const supplierByPOId = new Map(
    purchaseOrders.map((purchaseOrder) => [
      purchaseOrder.id,
      purchaseOrder.supplier_name,
    ]),
  )

  return grns.slice(0, 5).map((grn) => ({
    id: grn.id,
    grnNo: `GRN-${grn.id.slice(0, 8).toUpperCase()}`,
    supplier: supplierByPOId.get(grn.po_id) ?? 'Unknown Supplier',
    date: grn.created_at,
    status: grn.status,
  }))
}

export function useDashboardRecentGRNsQuery() {
  return useQuery({
    queryKey: ['dashboard-recent-grns'],
    queryFn: fetchDashboardRecentGRNs,
    placeholderData: [],
    refetchInterval: 30_000,
    retry: 1,
  })
}
