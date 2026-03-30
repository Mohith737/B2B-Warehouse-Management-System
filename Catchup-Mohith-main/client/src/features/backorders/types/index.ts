// client/src/features/backorders/types/index.ts
export type BackorderRead = {
  id: string
  po_number: string
  supplier_name: string
  status: string
  total_amount: number
  ordered_quantity: number
  received_quantity: number
  backorder_quantity: number
  created_at: string
}

export type BackordersQueryParams = {
  page: number
  pageSize: number
  overdueOnly: boolean
}

export type BackordersMeta = {
  page: number
  page_size: number
  total: number
}

export type BackordersListResponse = {
  data: BackorderRead[]
  meta: BackordersMeta
}
