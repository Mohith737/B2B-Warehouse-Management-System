// client/src/features/backorders/hooks/useBackordersQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { BackordersListResponse, BackordersQueryParams } from '../types'

type PurchaseOrderListLike = {
  data: Array<{
    id: string
    po_number: string
    supplier_name?: string
    status?: string
    total_amount?: number | string
    lines?: Array<{
      quantity_ordered?: number
      quantity_received?: number
    }>
    created_at: string
  }>
  meta: {
    page: number
    page_size: number
    total: number
  }
}

function normalizePurchaseOrderListPayload(
  payload: ApiResponse<PurchaseOrderListLike> | PurchaseOrderListLike,
): PurchaseOrderListLike {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'meta' in payload &&
    'data' in payload
  ) {
    return payload as PurchaseOrderListLike
  }

  return (payload as ApiResponse<PurchaseOrderListLike>).data
}

async function fetchBackorders(
  params: BackordersQueryParams,
): Promise<BackordersListResponse> {
  const response = await apiClient.get<
    ApiResponse<PurchaseOrderListLike> | PurchaseOrderListLike
  >('/purchase-orders', {
    params: {
      status: 'acknowledged',
      page: params.page,
      page_size: 50,
    },
  })

  const payload = normalizePurchaseOrderListPayload(response.data)

  const mappedRows = (payload.data ?? []).map((item) => ({
    id: item.id,
    po_number: item.po_number,
    supplier_name: item.supplier_name ?? '',
    status: item.status ?? 'acknowledged',
    total_amount:
      typeof item.total_amount === 'number'
        ? item.total_amount
        : Number.parseFloat(String(item.total_amount ?? 0)) || 0,
    ordered_quantity: (item.lines ?? []).reduce(
      (sum, line) => sum + (line.quantity_ordered ?? 0),
      0,
    ),
    received_quantity: (item.lines ?? []).reduce(
      (sum, line) => sum + (line.quantity_received ?? 0),
      0,
    ),
    backorder_quantity: (item.lines ?? []).reduce(
      (sum, line) =>
        sum + Math.max(0, (line.quantity_ordered ?? 0) - (line.quantity_received ?? 0)),
      0,
    ),
    created_at: item.created_at,
  }))

  return {
    data: params.overdueOnly
      ? mappedRows.filter((row) => {
          const ageMs = Date.now() - new Date(row.created_at).getTime()
          const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24))
          return ageDays > 7
        })
      : mappedRows,
    meta: payload.meta,
  }
}

export function useBackordersQuery(params: BackordersQueryParams) {
  return useQuery({
    queryKey: ['backorders', params],
    queryFn: () => fetchBackorders(params),
    staleTime: 30_000,
    retry: 1,
  })
}
