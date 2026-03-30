// client/src/features/admin/types/index.ts
import type { UserRole } from '../../../stores/authStore'

export type AdminUserRead = {
  id: string
  full_name: string
  email: string
  role: UserRole
  is_active: boolean
}

export type UsersQueryParams = {
  page: number
  pageSize: number
}

export type UsersListResponse = {
  data: AdminUserRead[]
  meta: {
    page: number
    page_size: number
    total: number
  }
}

export type CreateUserInput = {
  full_name: string
  email: string
  password: string
  role: UserRole
  is_active: boolean
}

export type UpdateUserInput = {
  id: string
  role?: UserRole
  is_active?: boolean
}
