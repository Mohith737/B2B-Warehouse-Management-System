// client/src/features/admin/hooks/useCreateUserMutation.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { AdminUserRead, CreateUserInput } from '../types'

async function createUser(payload: CreateUserInput): Promise<AdminUserRead> {
  const response = await apiClient.post<ApiResponse<AdminUserRead>>('/users/', payload)
  return response.data.data
}

export function useCreateUserMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createUser,
    retry: 0,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
