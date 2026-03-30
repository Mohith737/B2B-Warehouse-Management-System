// client/src/features/grns/hooks/useCompleteGRNMutation.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { CompleteGRNResponse } from '../types'

async function completeGRN(grnId: string): Promise<CompleteGRNResponse> {
  const response = await apiClient.post<ApiResponse<CompleteGRNResponse>>(
    `/grns/${grnId}/complete`,
  )
  return response.data.data
}

export function useCompleteGRNMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: completeGRN,
    retry: 0,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['grns'] })
      await queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
