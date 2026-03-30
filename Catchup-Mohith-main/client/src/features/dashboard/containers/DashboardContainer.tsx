// client/src/features/dashboard/containers/DashboardContainer.tsx

import { useAuthStore } from '../../../stores/authStore'
import { DashboardView } from '../components/DashboardView'
import { useDashboardLowStockQuery } from '../hooks/useDashboardLowStockQuery'
import { useDashboardMetricsQuery } from '../hooks/useDashboardMetricsQuery'
import { useDashboardRecentGRNsQuery } from '../hooks/useDashboardRecentGRNsQuery'
import { useDashboardTopSuppliersQuery } from '../hooks/useDashboardTopSuppliersQuery'

export function DashboardContainer(): JSX.Element {
  const role = useAuthStore((state) => state.role ?? 'warehouse_staff')
  const metricsQuery = useDashboardMetricsQuery()
  const lowStockQuery = useDashboardLowStockQuery()
  const recentGRNsQuery = useDashboardRecentGRNsQuery()
  const topSuppliersQuery = useDashboardTopSuppliersQuery()

  return (
    <DashboardView
      lowStockQuery={lowStockQuery}
      metricsQuery={metricsQuery}
      recentGRNsQuery={recentGRNsQuery}
      role={role}
      topSuppliersQuery={topSuppliersQuery}
    />
  )
}
