// client/src/pages/AdminUsersPage.tsx
import { useNavigate } from 'react-router-dom'

import { AdminUsersContainer } from '../features/admin/containers/AdminUsersContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function AdminUsersPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="users"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Users"
      role={role}
    >
      <AdminUsersContainer />
    </AppShell>
  )
}
