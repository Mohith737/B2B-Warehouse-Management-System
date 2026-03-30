// client/src/features/backorders/containers/BackordersContainer.tsx
import { useState } from 'react'

import { BACKORDERS_CONFIG } from '../constants/backordersConfig'
import { BackordersView } from '../components/BackordersView'
import { useBackordersQuery } from '../hooks/useBackordersQuery'

export function BackordersContainer(): JSX.Element {
  const [activeFilter, setActiveFilter] = useState<'all' | 'overdue'>('all')

  const query = useBackordersQuery({
    page: BACKORDERS_CONFIG.defaultPage,
    pageSize: BACKORDERS_CONFIG.defaultPageSize,
    overdueOnly: activeFilter === 'overdue',
  })

  return (
    <BackordersView
      activeFilter={activeFilter}
      backorders={query.data?.data ?? []}
      error={query.isError ? (query.error as Error).message : null}
      isLoading={query.isLoading}
      onFilterChange={(value) => setActiveFilter(value)}
      onRetry={() => {
        void query.refetch()
      }}
    />
  )
}
