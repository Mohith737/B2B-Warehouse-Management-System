// client/src/pages/PurchaseOrdersPage.tsx
import { useNavigate } from 'react-router-dom'

import { PurchaseOrdersContainer } from '../features/purchase-orders/containers/PurchaseOrdersContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function PurchaseOrdersPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="pos"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Purchase Orders"
      role={role}
    >
      <PurchaseOrdersContainer />
    </AppShell>
  )
}
