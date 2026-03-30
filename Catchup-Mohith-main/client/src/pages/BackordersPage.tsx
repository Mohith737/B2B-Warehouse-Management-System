// client/src/pages/BackordersPage.tsx
import { useNavigate } from 'react-router-dom'

import { BackordersContainer } from '../features/backorders/containers/BackordersContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function BackordersPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="backorders"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Backorders"
      role={role}
    >
      <BackordersContainer />
    </AppShell>
  )
}
