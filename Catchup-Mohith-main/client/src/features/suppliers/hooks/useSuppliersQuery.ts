// client/src/features/suppliers/hooks/useSuppliersQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { SuppliersListResponse, SuppliersQueryParams } from '../types'

function normalizeSuppliersListResponse(
  payload: ApiResponse<SuppliersListResponse> | SuppliersListResponse,
): SuppliersListResponse {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'meta' in payload &&
    'data' in payload
  ) {
    return payload as SuppliersListResponse
  }

  return (payload as ApiResponse<SuppliersListResponse>).data
}

async function fetchSuppliers(
  params: SuppliersQueryParams,
): Promise<SuppliersListResponse> {
  const response = await apiClient.get<
    ApiResponse<SuppliersListResponse> | SuppliersListResponse
  >('/suppliers', {
    params: {
      page: params.page,
      page_size: params.pageSize,
      search: params.search || undefined,
      tier: params.tier === 'all' ? undefined : params.tier,
    },
  })

  return normalizeSuppliersListResponse(response.data)
}

export function useSuppliersQuery(params: SuppliersQueryParams) {
  return useQuery({
    queryKey: ['suppliers', params],
    queryFn: () => fetchSuppliers(params),
    staleTime: 30_000,
    retry: 1,
  })
}
