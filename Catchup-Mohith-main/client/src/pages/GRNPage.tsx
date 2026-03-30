// client/src/pages/GRNPage.tsx
import { useNavigate } from 'react-router-dom'

import { GRNContainer } from '../features/grns/containers/GRNContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function GRNPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="grns"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Receive Goods"
      role={role}
    >
      <GRNContainer />
    </AppShell>
  )
}
