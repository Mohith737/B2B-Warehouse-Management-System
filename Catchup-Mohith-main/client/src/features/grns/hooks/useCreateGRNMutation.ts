// client/src/features/grns/hooks/useCreateGRNMutation.ts
import { useMutation } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { CreateGRNInput, CreateGRNResponse } from '../types'

async function createGRN(payload: CreateGRNInput): Promise<CreateGRNResponse> {
  const response = await apiClient.post<ApiResponse<CreateGRNResponse>>(
    '/grns/',
    payload,
  )
  return response.data.data
}

export function useCreateGRNMutation() {
  return useMutation({
    mutationFn: createGRN,
    retry: 0,
  })
}
