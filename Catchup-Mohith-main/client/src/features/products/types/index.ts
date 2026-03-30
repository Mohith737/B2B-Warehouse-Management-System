// client/src/features/products/types/index.ts
export type ProductRead = {
  id: string
  sku: string
  name: string
  category?: string | null
  current_stock: number
  reorder_point: number
  unit_price?: number | null
}

export type ProductsQueryParams = {
  page: number
  pageSize: number
  search: string
}

export type ProductsMeta = {
  page: number
  page_size: number
  total: number
}

export type ProductsListResponse = {
  data: ProductRead[]
  meta: ProductsMeta
}

export type ProductRow = {
  id: string
  sku: string
  name: string
  category?: string | null
  currentStock: number
  reorderPoint: number
  unitPrice?: number | null
}
