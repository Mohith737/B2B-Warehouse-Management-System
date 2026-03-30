// client/src/pages/SuppliersPage.tsx
import { useNavigate } from 'react-router-dom'

import { SuppliersContainer } from '../features/suppliers/containers/SuppliersContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function SuppliersPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="suppliers"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Suppliers"
      role={role}
    >
      <SuppliersContainer />
    </AppShell>
  )
}
