// client/src/features/backorders/constants/backordersConfig.ts
import type { FilterOption } from '../../../design-system/ui/molecules'

export const BACKORDERS_CONFIG = {
  pageTitle: 'Backorders',
  toolbarTitle: 'Backorders',
  defaultPage: 1,
  defaultPageSize: 20,
  overdueThresholdDays: 7,
} as const

export const BACKORDER_FILTERS: FilterOption[] = [
  { value: 'all', label: 'All' },
  { value: 'overdue', label: 'Overdue' },
]
