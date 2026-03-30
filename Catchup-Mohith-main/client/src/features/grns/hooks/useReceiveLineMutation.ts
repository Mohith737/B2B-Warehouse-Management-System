// client/src/features/grns/hooks/useReceiveLineMutation.ts
import { useMutation } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { ReceiveLineInput, ReceiveLineResponse } from '../types'

async function receiveGRNLine(payload: ReceiveLineInput): Promise<ReceiveLineResponse> {
  const response = await apiClient.post<ApiResponse<ReceiveLineResponse>>(
    `/grns/${payload.grnId}/lines`,
    {
      product_id: payload.product_id,
      quantity_received: payload.quantity_received,
      unit_cost: payload.unit_cost,
      barcode_scanned: payload.barcode,
    },
  )
  return response.data.data
}

export function useReceiveLineMutation() {
  return useMutation({
    mutationFn: receiveGRNLine,
    retry: 0,
  })
}
