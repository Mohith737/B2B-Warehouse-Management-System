// client/src/pages/ProductsPage.tsx
import { useNavigate } from 'react-router-dom'

import { ProductsContainer } from '../features/products/containers/ProductsContainer'
import { AppShell } from '../layouts/AppShell'
import { useAuthStore } from '../stores/authStore'

export default function ProductsPage(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const logout = useAuthStore((state) => state.logout)

  return (
    <AppShell
      activeView="products"
      onLogout={() => {
        logout()
        navigate('/login')
      }}
      pageTitle="Products"
      role={role}
    >
      <ProductsContainer />
    </AppShell>
  )
}
