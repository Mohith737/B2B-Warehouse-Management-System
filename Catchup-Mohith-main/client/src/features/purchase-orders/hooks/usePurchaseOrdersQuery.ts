// client/src/features/purchase-orders/hooks/usePurchaseOrdersQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { PurchaseOrdersListResponse, PurchaseOrdersQueryParams } from '../types'

async function fetchPurchaseOrders(
  params: PurchaseOrdersQueryParams,
): Promise<PurchaseOrdersListResponse> {
  const normalizedStatus = params.status === 'received' ? 'closed' : params.status

  const response = await apiClient.get<
    ApiResponse<PurchaseOrdersListResponse> | PurchaseOrdersListResponse
  >('/purchase-orders', {
    params: {
      page: params.page,
      page_size: params.pageSize,
      search: params.search || undefined,
      status: normalizedStatus === 'all' ? undefined : normalizedStatus,
    },
  })

  if (
    typeof response.data === 'object' &&
    response.data !== null &&
    'meta' in response.data &&
    'data' in response.data
  ) {
    return response.data as PurchaseOrdersListResponse
  }

  return (response.data as ApiResponse<PurchaseOrdersListResponse>).data
}

export function usePurchaseOrdersQuery(params: PurchaseOrdersQueryParams) {
  return useQuery({
    queryKey: ['purchase-orders', params],
    queryFn: () => fetchPurchaseOrders(params),
    staleTime: 30_000,
    retry: 1,
  })
}
