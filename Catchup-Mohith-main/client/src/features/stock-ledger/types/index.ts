// client/src/features/stock-ledger/types/index.ts
export type StockLedgerChangeType =
  | 'grn_receipt'
  | 'po_reservation'
  | 'manual_adjustment'
  | 'reorder_auto'
  | 'backorder_fulfillment'

export type StockLedgerEntry = {
  id: string
  product_id: string
  product_name?: string
  product_sku?: string
  quantity_change: number
  change_type: StockLedgerChangeType
  reference_id: string | null
  reference_type?: string | null
  notes: string | null
  balance_after: number
  created_at: string
}

export type StockLedgerCursorMeta = {
  limit: number
  next_cursor: string | null
}

export type StockLedgerPageResponse = {
  data: StockLedgerEntry[]
  meta: StockLedgerCursorMeta
}
