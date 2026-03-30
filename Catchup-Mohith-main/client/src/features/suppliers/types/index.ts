// client/src/features/suppliers/types/index.ts
export type SupplierTier = 'Silver' | 'Gold' | 'Diamond'

export type SupplierRead = {
  id: string
  name: string
  current_tier: SupplierTier
  credit_limit: number
  contact_email: string
  lead_time_days?: number | null
  payment_terms?: string | null
  is_active: boolean
}

export type SuppliersQueryParams = {
  page: number
  pageSize: number
  search: string
  tier: 'all' | 'Silver' | 'Gold' | 'Diamond'
}

export type SuppliersMeta = {
  page: number
  page_size: number
  total: number
}

export type SuppliersListResponse = {
  data: SupplierRead[]
  meta: SuppliersMeta
}

export type SupplierRow = {
  id: string
  name: string
  tier: SupplierTier
  creditLimit: number
  leadTimeDays?: number | null
  paymentTerms?: string | null
  contactEmail: string
  status: 'active' | 'inactive'
}
