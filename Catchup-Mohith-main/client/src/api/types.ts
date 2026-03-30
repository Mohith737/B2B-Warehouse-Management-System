// client/src/api/types.ts
export type ApiError = {
  code: string
  message: string
  details: Record<string, unknown>
}

export type ApiResponse<T> = {
  data: T
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}
