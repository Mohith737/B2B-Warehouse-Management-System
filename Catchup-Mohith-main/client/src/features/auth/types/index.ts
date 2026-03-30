// client/src/features/auth/types/index.ts
import type { UserRole } from '../../../stores/authStore'

export type LoginRequest = {
  email: string
  password: string
}

export type AuthUser = {
  userId: string
  username: string
  email: string
  role: UserRole
}

export type LoginResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  user?: AuthUser
}
