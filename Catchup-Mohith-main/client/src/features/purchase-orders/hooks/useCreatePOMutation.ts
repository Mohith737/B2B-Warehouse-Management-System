// client/src/features/purchase-orders/hooks/useCreatePOMutation.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { CreatePOInput, CreatePOResponse } from '../types'

async function createPurchaseOrder(payload: CreatePOInput): Promise<CreatePOResponse> {
  const response = await apiClient.post<ApiResponse<CreatePOResponse>>(
    '/purchase-orders',
    payload,
  )
  return response.data.data
}

export function useCreatePOMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createPurchaseOrder,
    retry: 0,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
  })
}
