// client/src/pages/CreatePOPage.tsx
import { useNavigate } from 'react-router-dom'

import { POWizardContainer } from '../features/purchase-orders/containers/POWizardContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function CreatePOPage(): JSX.Element {
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
      pageTitle="Create Purchase Order"
      role={role}
    >
      <POWizardContainer />
    </AppShell>
  )
}
