// client/src/api/client.ts
import axios from 'axios'

import type { ApiError, ApiResponse, TokenResponse } from './types'
import { useAuthStore } from '../stores/authStore'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type RetryableRequestConfig = {
  _retry?: boolean
  headers?: Record<string, string>
  url?: string
}

export const apiClient = axios.create({
  baseURL,
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status
    const originalRequest = (error?.config ?? {}) as RetryableRequestConfig
    const requestUrl = String(originalRequest.url ?? '')
    const isAuthRequest =
      requestUrl.includes('/auth/login') || requestUrl.includes('/auth/refresh')

    if (!error?.response) {
      const parsedNetworkError: ApiError = {
        code: 'NETWORK_ERROR',
        message: 'Unable to reach the server. Check your connection and try again.',
        details: {},
      }
      return Promise.reject(parsedNetworkError)
    }

    if (status === 403) {
      window.location.href = '/unauthorized'
      return Promise.reject(error)
    }

    if (status === 401 && !originalRequest._retry && !isAuthRequest) {
      originalRequest._retry = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        if (!refreshToken) {
          throw new Error('Missing refresh token')
        }

        const refreshClient = axios.create({ baseURL })
        const refreshResponse = await refreshClient.post<ApiResponse<TokenResponse>>(
          '/auth/refresh',
          {
            refresh_token: refreshToken,
          },
        )

        const nextAccessToken = refreshResponse.data.data.access_token
        const nextRefreshToken = refreshResponse.data.data.refresh_token

        useAuthStore.getState().setToken(nextAccessToken)
        useAuthStore.getState().setRefreshToken(nextRefreshToken)

        originalRequest.headers = originalRequest.headers ?? {}
        originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`

        return apiClient.request(originalRequest)
      } catch (refreshError) {
        useAuthStore.getState().logout()
        window.location.assign('/login')
        return Promise.reject(refreshError)
      }
    }

    const parsedError: ApiError = {
      code: error?.response?.data?.error?.code ?? 'UNKNOWN_ERROR',
      message: error?.response?.data?.error?.message ?? 'Unexpected error occurred',
      details: error?.response?.data?.error?.details ?? {},
    }

    return Promise.reject(parsedError)
  },
)
