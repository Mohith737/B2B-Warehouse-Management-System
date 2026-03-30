// client/src/features/grns/types/index.ts
export type OpenPORead = {
  id: string
  po_number: string
  supplier_id: string
  total_amount: number
}

export type PurchaseOrderLineRead = {
  id: string
  product_id: string
  quantity_ordered: number
}

export type PurchaseOrderDetailRead = {
  id: string
  lines: PurchaseOrderLineRead[]
}

export type OpenPOsResponse = {
  data: OpenPORead[]
  meta: {
    total: number
    page: number
    page_size: number
    total_pages: number
  }
}

export type CreateGRNInput = {
  po_id: string
}

export type CreateGRNResponse = {
  id: string
  grn_number: string
  status: 'open' | 'completed'
}

export type ReceiveLineInput = {
  grnId: string
  product_id: string
  barcode: string
  quantity_received: number
  unit_cost: number
}

export type GRNLineRead = {
  id: string
  grn_id: string
  product_id: string
  quantity_received: number
  unit_cost: number
  barcode_scanned: string | null
}

export type ReceiveLineResponse = {
  id: string
  po_id: string
  status: 'open' | 'completed'
  lines: GRNLineRead[]
}

export type CompleteGRNResponse = {
  id: string
  po_id: string
  status: 'open' | 'completed'
  lines: GRNLineRead[]
}

export type GRNScanRow = {
  id: string
  barcode: string
  productName: string
  expectedQty: number
  receivedQty: number
}
