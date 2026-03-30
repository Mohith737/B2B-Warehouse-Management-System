// client/src/features/suppliers/constants/suppliersConfig.ts
import type { FilterOption } from '../../../design-system/ui/molecules/FilterBar'

export const SUPPLIERS_CONFIG = {
  pageTitle: 'Suppliers',
  toolbarTitle: 'Suppliers',
  searchPlaceholder: 'Search suppliers by name or contact',
  defaultPage: 1,
  defaultPageSize: 10,
} as const

export const SUPPLIER_TIER_FILTERS: FilterOption[] = [
  { value: 'all', label: 'All tiers' },
  { value: 'Silver', label: 'Silver' },
  { value: 'Gold', label: 'Gold' },
  { value: 'Diamond', label: 'Diamond' },
]
