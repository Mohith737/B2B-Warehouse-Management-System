// client/src/features/products/hooks/useProductsQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { ProductsListResponse, ProductsQueryParams } from '../types'

function normalizeProductsListResponse(
  payload: ApiResponse<ProductsListResponse> | ProductsListResponse,
): ProductsListResponse {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'meta' in payload &&
    'data' in payload
  ) {
    return payload as ProductsListResponse
  }

  return (payload as ApiResponse<ProductsListResponse>).data
}

async function fetchProducts(
  params: ProductsQueryParams,
): Promise<ProductsListResponse> {
  const response = await apiClient.get<
    ApiResponse<ProductsListResponse> | ProductsListResponse
  >('/products', {
    params: {
      page: params.page,
      page_size: params.pageSize,
      search: params.search || undefined,
    },
  })

  return normalizeProductsListResponse(response.data)
}

export function useProductsQuery(params: ProductsQueryParams) {
  return useQuery({
    queryKey: ['products', params],
    queryFn: () => fetchProducts(params),
    staleTime: 30_000,
    retry: 1,
  })
}
