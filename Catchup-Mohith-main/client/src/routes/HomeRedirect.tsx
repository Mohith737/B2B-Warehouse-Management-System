// client/src/routes/HomeRedirect.tsx
import { Navigate } from 'react-router-dom'

import { ROLE_HOME } from '../config/navigation'
import { useAuthStore } from '../stores/authStore'

export function HomeRedirect(): JSX.Element {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const role = useAuthStore((state) => state.role)

  if (!isAuthenticated || !role) {
    return <Navigate replace to="/login" />
  }

  return <Navigate replace to={ROLE_HOME[role]} />
}
