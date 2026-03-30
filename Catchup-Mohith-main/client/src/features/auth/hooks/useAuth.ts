// client/src/features/auth/hooks/useAuth.ts
import { useMutation } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import { useAuthStore, type UserRole } from '../../../stores/authStore'
import type { LoginRequest, LoginResponse } from '../types'

type TokenPayload = {
  user_id?: string
  sub?: string
  email?: string
  username?: string
  role?: UserRole
  type?: string
}

function decodeTokenPayload(token: string): TokenPayload {
  const parts = token.split('.')
  if (parts.length < 2) {
    return {}
  }

  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')
    const payload = atob(padded)
    return JSON.parse(payload) as TokenPayload
  } catch {
    return {}
  }
}

export function useAuth() {
  const loginToStore = useAuthStore((state) => state.login)
  const logoutFromStore = useAuthStore((state) => state.logout)

  const mutation = useMutation({
    mutationFn: async (payload: LoginRequest) => {
      const response = await apiClient.post<ApiResponse<LoginResponse>>(
        '/auth/login',
        payload,
      )
      return response.data.data
    },
    onSuccess: (data) => {
      const decoded = decodeTokenPayload(data.access_token)
      const role =
        data.user?.role ??
        decoded.role ??
        useAuthStore.getState().role ??
        'warehouse_staff'

      loginToStore({
        userId: data.user?.userId ?? decoded.user_id ?? decoded.sub ?? '',
        username: data.user?.username ?? decoded.username ?? 'StockBridge User',
        email: data.user?.email ?? decoded.email ?? '',
        role,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      })
    },
  })

  return {
    login: mutation.mutateAsync,
    logout: logoutFromStore,
    isLoading: mutation.isPending,
    error: mutation.error,
  }
}
