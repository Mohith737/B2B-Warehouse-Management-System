// client/src/pages/DashboardPage.tsx
import { useNavigate } from 'react-router-dom'

import { DashboardContainer } from '../features/dashboard/containers/DashboardContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function DashboardPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="dashboard"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Dashboard"
      role={role}
    >
      <DashboardContainer />
    </AppShell>
  )
}
