// client/src/features/admin/hooks/useUsersQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import type { UsersListResponse, UsersQueryParams } from '../types'

async function fetchUsers(params: UsersQueryParams): Promise<UsersListResponse> {
  const response = await apiClient.get<ApiResponse<UsersListResponse> | UsersListResponse>(
    '/users/',
    {
      params: {
        page: params.page,
        page_size: params.pageSize,
      },
    },
  )

  if (
    typeof response.data === 'object' &&
    response.data !== null &&
    'meta' in response.data &&
    'data' in response.data
  ) {
    return response.data as UsersListResponse
  }

  return (response.data as ApiResponse<UsersListResponse>).data
}

export function useUsersQuery(params: UsersQueryParams) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => fetchUsers(params),
    staleTime: 60_000,
    retry: 1,
  })
}
