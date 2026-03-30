// client/src/features/auth/constants/authConfig.ts
export const AUTH_VALIDATION_RULES = {
  email: {
    required: 'Email is required.',
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    invalid: 'Enter a valid email address.',
  },
  password: {
    required: 'Password is required.',
    minLength: 8,
    minLengthMessage: 'Password must be at least 8 characters.',
  },
} as const

export const AUTH_ERROR_MESSAGES = {
  generic: 'Unable to sign in. Please try again.',
  invalidCredentials: 'Invalid email or password.',
  network: 'Network error. Check your connection and retry.',
} as const
