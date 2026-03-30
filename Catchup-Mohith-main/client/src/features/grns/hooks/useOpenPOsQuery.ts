// client/src/features/grns/hooks/useOpenPOsQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { OpenPORead, OpenPOsResponse } from '../types'

function normalizeOpenPOsPayload(
  payload: ApiResponse<OpenPOsResponse> | OpenPOsResponse,
): OpenPOsResponse {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'meta' in payload &&
    'data' in payload
  ) {
    return payload as OpenPOsResponse
  }

  return (payload as ApiResponse<OpenPOsResponse>).data
}

async function fetchOpenPOs(): Promise<OpenPORead[]> {
  const response = await apiClient.get<ApiResponse<OpenPOsResponse> | OpenPOsResponse>(
    '/purchase-orders/',
    {
      params: {
        status: 'shipped',
        page_size: 50,
        page: 1,
      },
    },
  )

  const payload = normalizeOpenPOsPayload(response.data)
  return payload.data ?? []
}

export function useOpenPOsQuery() {
  return useQuery({
    queryKey: ['open-pos-grn'],
    queryFn: fetchOpenPOs,
    staleTime: 30_000,
    retry: 1,
  })
}
