// client/src/stores/authStore.ts
import { create } from 'zustand'

export type UserRole = 'warehouse_staff' | 'procurement_manager' | 'admin'

export type LoginPayload = {
  userId: string
  username: string
  email: string
  role: UserRole
  accessToken: string
  refreshToken: string | null
}

type AuthState = {
  userId: string | null
  username: string | null
  email: string | null
  role: UserRole | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (payload: LoginPayload) => void
  logout: () => void
  setToken: (token: string) => void
  setRefreshToken: (token: string | null) => void
}

const initialState = {
  userId: null,
  username: null,
  email: null,
  role: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
}

export const useAuthStore = create<AuthState>((set) => ({
  ...initialState,
  login: (payload) =>
    set({
      userId: payload.userId,
      username: payload.username,
      email: payload.email,
      role: payload.role,
      accessToken: payload.accessToken,
      refreshToken: payload.refreshToken,
      isAuthenticated: true,
    }),
  logout: () =>
    set({
      ...initialState,
    }),
  setToken: (token) =>
    set((state) => ({
      accessToken: token,
      isAuthenticated: Boolean(token && state.userId),
    })),
  setRefreshToken: (token) =>
    set({
      refreshToken: token,
    }),
}))
