// client/src/features/admin/hooks/useUpdateUserMutation.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { AdminUserRead, UpdateUserInput } from '../types'

async function updateUser(payload: UpdateUserInput): Promise<AdminUserRead> {
  const response = await apiClient.patch<ApiResponse<AdminUserRead>>(
    `/users/${payload.id}`,
    {
      role: payload.role,
      is_active: payload.is_active,
    },
  )

  return response.data.data
}

export function useUpdateUserMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateUser,
    retry: 0,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
