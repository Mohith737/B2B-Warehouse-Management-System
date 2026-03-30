// client/src/pages/StockLedgerPage.tsx
import { useNavigate } from 'react-router-dom'

import { StockLedgerContainer } from '../features/stock-ledger/containers/StockLedgerContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function StockLedgerPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="stock"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Stock Ledger"
      role={role}
    >
      <StockLedgerContainer />
    </AppShell>
  )
}
