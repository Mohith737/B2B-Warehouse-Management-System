// client/src/features/purchase-orders/types/index.ts
import type { WizardLine } from '../../../stores/wizardStore'

export type PurchaseOrderStatus =
  | 'draft'
  | 'submitted'
  | 'acknowledged'
  | 'shipped'
  | 'received'
  | 'closed'
  | 'cancelled'

export type PurchaseOrderRead = {
  id: string
  po_number: string
  supplier_name: string
  status: PurchaseOrderStatus
  total_amount: number
  created_at: string
  created_by?: string | null
  created_by_name?: string | null
}

export type PurchaseOrdersMeta = {
  page: number
  page_size: number
  total: number
}

export type PurchaseOrdersListResponse = {
  data: PurchaseOrderRead[]
  meta: PurchaseOrdersMeta
}

export type PurchaseOrdersQueryParams = {
  page: number
  pageSize: number
  search: string
  status: 'all' | PurchaseOrderStatus
}

export type CreatePOInput = {
  supplier_id: string
  notes: string
  lines: Array<{
    product_id: string
    quantity_ordered: number
    unit_price: number
  }>
}

export type CreatePOResponse = {
  id: string
  po_number: string
  status: PurchaseOrderStatus
}

export type WizardProductOption = {
  id: string
  name: string
  defaultUnitPrice?: number
}

export type WizardSupplierOption = {
  id: string
  name: string
  creditLimit: number
}

export type WizardSnapshot = {
  currentStep: 1 | 2 | 3 | 4
  supplierId: string | null
  supplierName: string | null
  notes: string
  lines: WizardLine[]
}
