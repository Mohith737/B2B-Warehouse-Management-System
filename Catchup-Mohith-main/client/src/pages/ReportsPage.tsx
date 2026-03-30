// client/src/pages/ReportsPage.tsx
import { useNavigate } from 'react-router-dom'

import { ReportsContainer } from '../features/reports/containers/ReportsContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function ReportsPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="reports"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Reports"
      role={role}
    >
      <ReportsContainer />
    </AppShell>
  )
}
