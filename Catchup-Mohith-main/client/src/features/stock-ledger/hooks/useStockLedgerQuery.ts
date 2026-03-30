// client/src/features/stock-ledger/hooks/useStockLedgerQuery.ts
import { useInfiniteQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import { STOCK_LEDGER_CONFIG } from '../constants/stockLedgerConfig'
import type { StockLedgerPageResponse } from '../types'

function normalizeStockLedgerPageResponse(
  payload: ApiResponse<StockLedgerPageResponse> | StockLedgerPageResponse,
): StockLedgerPageResponse {
  if (
    typeof payload === 'object' &&
    payload !== null &&
    'meta' in payload &&
    'data' in payload
  ) {
    return payload as StockLedgerPageResponse
  }

  return (payload as ApiResponse<StockLedgerPageResponse>).data
}

async function fetchStockLedgerPage(
  cursor: string | undefined,
): Promise<StockLedgerPageResponse> {
  const response = await apiClient.get<
    ApiResponse<StockLedgerPageResponse> | StockLedgerPageResponse
  >('/stock-ledger', {
    params: {
      limit: STOCK_LEDGER_CONFIG.pageSize,
      cursor,
    },
  })

  return normalizeStockLedgerPageResponse(response.data)
}

export function useStockLedgerQuery() {
  return useInfiniteQuery({
    queryKey: ['stock-ledger'],
    queryFn: ({ pageParam }) => fetchStockLedgerPage(pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => {
      const nextCursor = lastPage?.meta?.next_cursor
      return nextCursor === null || nextCursor === undefined ? undefined : nextCursor
    },
    retry: 1,
    staleTime: 30_000,
  })
}
