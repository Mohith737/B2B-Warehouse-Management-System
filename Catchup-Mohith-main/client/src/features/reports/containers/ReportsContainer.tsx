// client/src/features/reports/containers/ReportsContainer.tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuthStore } from '../../../stores/authStore'
import { useUIStore } from '../../../stores/uiStore'
import { REPORTS_CONFIG } from '../constants/reportsConfig'
import { ReportsView } from '../components/ReportsView'
import { useDownloadReportMutation } from '../hooks/useDownloadReportMutation'
import { useSuppliersQuery } from '../../suppliers/hooks/useSuppliersQuery'

export function ReportsContainer(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const addToast = useUIStore((state) => state.addToast)

  useEffect(() => {
    if (role === 'warehouse_staff') {
      navigate('/unauthorized')
    }
  }, [navigate, role])

  const suppliersQuery = useSuppliersQuery({
    page: 1,
    pageSize: 50,
    search: '',
    tier: 'all',
  })
  const downloadMutation = useDownloadReportMutation()

  const [supplierId, setSupplierId] = useState('')
  const [months, setMonths] = useState<number>(REPORTS_CONFIG.defaultMonths)
  const [month, setMonth] = useState(REPORTS_CONFIG.defaultMonth)

  return (
    <ReportsView
      isDownloading={downloadMutation.isPending}
      isLoadingSuppliers={suppliersQuery.isLoading}
      month={month}
      months={months}
      onDownloadMonthlyTierSummary={() => {
        downloadMutation.mutate(
          {
            type: 'monthly-tier-summary',
            payload: { month },
          },
          {
            onError: (error) => {
              const message =
                typeof error === 'object' &&
                error !== null &&
                'message' in error &&
                typeof error.message === 'string'
                  ? error.message
                  : 'Failed to download monthly tier summary report.'

              addToast({
                kind: 'error',
                message,
              })
            },
          },
        )
      }}
      onDownloadSupplierReport={() => {
        if (!supplierId) {
          return
        }
        downloadMutation.mutate(
          {
            type: 'supplier',
            payload: { supplierId, months },
          },
          {
            onError: (error) => {
              const message =
                typeof error === 'object' &&
                error !== null &&
                'message' in error &&
                typeof error.message === 'string'
                  ? error.message
                  : 'Failed to download supplier report.'

              addToast({
                kind: 'error',
                message,
              })
            },
          },
        )
      }}
      onMonthChange={setMonth}
      onMonthsChange={setMonths}
      onSupplierIdChange={setSupplierId}
      supplierId={supplierId}
      suppliers={suppliersQuery.data?.data ?? []}
    />
  )
}
