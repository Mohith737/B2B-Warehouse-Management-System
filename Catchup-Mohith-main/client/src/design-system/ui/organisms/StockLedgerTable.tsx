// client/src/design-system/ui/organisms/StockLedgerTable.tsx
import {
  ActionableNotification,
  DataTable,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'

import { EmptyState, LoadingSkeleton } from '../atoms'

type StockLedgerEntry = {
  id: string
  product_name: string
  product_sku: string
  quantity_change: number
  change_type: string
  balance_after: number
  reference_id: string | null
  reference_type: string | null
  created_at: string
}

type StockLedgerTableProps = {
  entries: StockLedgerEntry[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
}

const headers = [
  { key: 'date', header: 'Date' },
  { key: 'product', header: 'Product' },
  { key: 'sku', header: 'SKU' },
  { key: 'change', header: 'Change' },
  { key: 'type', header: 'Type' },
  { key: 'balance', header: 'Balance After' },
  { key: 'reference', header: 'Reference' },
]

export function StockLedgerTable({
  entries,
  isLoading,
  isEmpty,
  error,
  onRetry,
}: StockLedgerTableProps): JSX.Element {
  const formatQuantity = (value: number): string =>
    new Intl.NumberFormat(undefined, {
      maximumFractionDigits: 2,
      minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
    }).format(value)

  if (isLoading) {
    return <LoadingSkeleton lines={6} state="loading" />
  }

  if (error) {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={onRetry}
        subtitle={error}
        title="Failed to load stock ledger"
      />
    )
  }

  if (isEmpty) {
    return (
      <EmptyState
        description="No stock ledger entries were found for the selected filters."
        state="empty"
        title="No ledger entries"
      />
    )
  }

  const rows = entries.map((entry) => ({
    id: entry.id,
    date: new Date(entry.created_at).toLocaleString(),
    product: entry.product_name,
    sku: entry.product_sku,
    change: formatQuantity(entry.quantity_change),
    type: entry.change_type,
    balance: formatQuantity(entry.balance_after),
    reference:
      entry.reference_id && entry.reference_type
        ? `${entry.reference_type}:${entry.reference_id}`
        : '-',
  }))

  return (
    <DataTable headers={headers} rows={rows}>
      {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
        <TableContainer title="Stock Ledger">
          <Table {...getTableProps()}>
            <TableHead>
              <TableRow>
                {dataHeaders.map((header) => {
                  const { key, ...headerProps } = getHeaderProps({ header })
                  return (
                    <TableHeader key={key} {...headerProps}>
                      {header.header}
                    </TableHeader>
                  )
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {dataRows.map((row) => (
                <TableRow key={row.id}>
                  {row.cells.map((cell) => (
                    <TableCell key={cell.id}>{cell.value}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </DataTable>
  )
}
