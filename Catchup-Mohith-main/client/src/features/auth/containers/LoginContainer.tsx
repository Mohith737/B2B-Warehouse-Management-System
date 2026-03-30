// client/src/features/auth/containers/LoginContainer.tsx
// client/src/features/auth/containers/LoginContainer.tsx
import { Tile } from '@carbon/react'
import { useLocation, useNavigate } from 'react-router-dom'

import { ROLE_HOME } from '../../../config/navigation'
import styles from '../../../pages/LoginPage.module.scss'
import { useAuthStore } from '../../../stores/authStore'
import { AUTH_ERROR_MESSAGES } from '../constants/authConfig'
import { useAuth } from '../hooks/useAuth'
import { LoginForm } from '../components/LoginForm'
import type { LoginRequest } from '../types'

type LocationState = {
  from?: {
    pathname?: string
  }
}

export function LoginContainer(): JSX.Element {
  const navigate = useNavigate()
  const location = useLocation()
  const role = useAuthStore((state) => state.role)
  const { login, isLoading, error } = useAuth()

  const handleSubmit = async (payload: LoginRequest) => {
    try {
      await login(payload)
      const fromPath = (location.state as LocationState | null)?.from?.pathname
      if (fromPath) {
        navigate(fromPath, { replace: true })
        return
      }

      const latestRole = useAuthStore.getState().role ?? role
      if (latestRole) {
        navigate(ROLE_HOME[latestRole], { replace: true })
      }
    } catch {
      return
    }
  }

  const errorMessage =
    error instanceof Error ? error.message : error ? AUTH_ERROR_MESSAGES.generic : null

  return (
    <Tile className={styles.formCard}>
      <h2 className={styles.cardTitle}>Welcome back</h2>
      <p className={styles.cardSubtitle}>Sign in to your StockBridge account</p>
      <LoginForm error={errorMessage} isLoading={isLoading} onSubmit={handleSubmit} />
      <p className={styles.footerText}>Use your StockBridge credentials</p>
    </Tile>
  )
}
