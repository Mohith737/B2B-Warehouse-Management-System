// client/src/features/backorders/components/BackordersView.tsx
import { Stack, Tag, Tile } from '@carbon/react'

import { FilterBar } from '../../../design-system/ui/molecules'
import { BackorderTable } from '../../../design-system/ui/organisms'
import { BACKORDERS_CONFIG } from '../constants/backordersConfig'
import { BACKORDER_FILTERS } from '../constants/backordersConfig'
import type { BackorderRead } from '../types'
import styles from './BackordersView.module.scss'

type BackordersViewProps = {
  backorders: BackorderRead[]
  isLoading: boolean
  error: string | null
  activeFilter: 'all' | 'overdue'
  onFilterChange: (value: 'all' | 'overdue') => void
  onRetry: () => void
}

export function BackordersView({
  backorders,
  isLoading,
  error,
  activeFilter,
  onFilterChange,
  onRetry,
}: BackordersViewProps): JSX.Element {
  const overdueCount = backorders.filter((entry) => {
    const ageMs = Date.now() - new Date(entry.created_at).getTime()
    const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24))
    return ageDays > BACKORDERS_CONFIG.overdueThresholdDays
  }).length

  return (
    <Stack className={styles.page} gap={6}>
      <Tile className={styles.filterTile}>
        <div className={styles.headerRow}>
          <Tag type="blue">{`${backorders.length} Orders`}</Tag>
          <Tag type={overdueCount > 0 ? 'red' : 'green'}>
            {`${overdueCount} Overdue`}
          </Tag>
        </div>
        <FilterBar
          activeFilter={activeFilter}
          filters={BACKORDER_FILTERS}
          onFilterChange={(value) => onFilterChange(value as 'all' | 'overdue')}
        />
      </Tile>

      <BackorderTable
        backorders={backorders}
        error={error}
        isEmpty={!isLoading && !error && backorders.length === 0}
        isLoading={isLoading}
        onRetry={onRetry}
      />
    </Stack>
  )
}
