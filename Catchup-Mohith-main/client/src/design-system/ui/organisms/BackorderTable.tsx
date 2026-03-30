// client/src/design-system/ui/organisms/BackorderTable.tsx
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

import { EmptyState, LoadingSkeleton, StatusBadge } from '../atoms'
import { BackorderAgeIndicator } from '../molecules'

type BackorderRow = {
  id: string
  po_number: string
  supplier_name: string
  status: string
  total_amount: number | string
  ordered_quantity: number
  received_quantity: number
  backorder_quantity: number
  created_at: string
}

type BackorderTableProps = {
  backorders: BackorderRow[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
}

const headers = [
  { key: 'poNumber', header: 'PO Number' },
  { key: 'supplier', header: 'Supplier' },
  { key: 'status', header: 'Status' },
  { key: 'total', header: 'Total' },
  { key: 'ordered', header: 'Ordered Qty' },
  { key: 'received', header: 'Received Qty' },
  { key: 'backorder', header: 'Backorder Qty' },
  { key: 'age', header: 'Age (days)' },
]

export function BackorderTable({
  backorders,
  isLoading,
  isEmpty,
  error,
  onRetry,
}: BackorderTableProps): JSX.Element {
  const formatCurrency = (value: number | string): string => {
    const numericValue =
      typeof value === 'number' ? value : Number.parseFloat(String(value))
    if (Number.isNaN(numericValue)) {
      return '0.00'
    }
    return numericValue.toFixed(2)
  }

  if (isLoading) {
    return <LoadingSkeleton lines={5} state="loading" />
  }

  if (error) {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={onRetry}
        subtitle={error}
        title="Unable to load backorders"
      />
    )
  }

  if (isEmpty) {
    return (
      <EmptyState
        description="No backorders match your current filters."
        state="empty"
        title="No backorders"
      />
    )
  }

  const rows = backorders.map((entry) => {
    const ageMs = Date.now() - new Date(entry.created_at).getTime()
    const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24))

    return {
      id: entry.id,
      poNumber: entry.po_number,
      supplier: entry.supplier_name,
      status: entry.status,
      total: formatCurrency(entry.total_amount),
      ordered: String(entry.ordered_quantity),
      received: String(entry.received_quantity),
      backorder: String(entry.backorder_quantity),
      age: String(ageDays),
    }
  })
  const createdAtById = new Map(
    backorders.map((entry) => [entry.id, entry.created_at] as const),
  )

  return (
    <DataTable headers={headers} rows={rows}>
      {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
        <TableContainer title="Backorders">
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
                    <TableCell key={cell.id}>
                      {cell.info.header === 'status' ? (
                        <StatusBadge domain="backorder" status={String(cell.value)} />
                      ) : cell.info.header === 'age' ? (
                        <BackorderAgeIndicator
                          createdAt={
                            createdAtById.get(row.id) ?? new Date().toISOString()
                          }
                        />
                      ) : (
                        cell.value
                      )}
                    </TableCell>
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
