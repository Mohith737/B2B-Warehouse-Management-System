// client/src/features/purchase-orders/constants/poConfig.ts
import type { FilterOption } from '../../../design-system/ui/molecules/FilterBar'

export const PO_CONFIG = {
  pageTitle: 'Purchase Orders',
  wizardTitle: 'Create Purchase Order',
  toolbarTitle: 'Purchase Orders',
  searchPlaceholder: 'Search by PO number or supplier',
  defaultPage: 1,
  defaultPageSize: 10,
  wizardSteps: ['Supplier', 'Lines', 'Review', 'Complete'],
} as const

export const PO_STATUS_FILTERS: FilterOption[] = [
  { value: 'all', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'shipped', label: 'Shipped' },
  { value: 'closed', label: 'Closed' },
  { value: 'cancelled', label: 'Cancelled' },
]
