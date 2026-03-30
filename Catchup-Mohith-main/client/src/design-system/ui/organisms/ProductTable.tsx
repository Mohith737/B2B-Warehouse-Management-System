// client/src/design-system/ui/organisms/ProductTable.tsx
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

type ProductRow = {
  id: string
  sku: string
  name: string
  currentStock: number
  reorderPoint: number
}

type ProductTableProps = {
  products: ProductRow[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
}

const headers = [
  { key: 'sku', header: 'SKU' },
  { key: 'name', header: 'Name' },
  { key: 'currentStock', header: 'Stock' },
  { key: 'reorderPoint', header: 'Reorder Point' },
  { key: 'status', header: 'Status' },
]

export function ProductTable({
  products,
  isLoading,
  isEmpty,
  error,
  onRetry,
}: ProductTableProps): JSX.Element {
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
        title="Failed to load products"
      />
    )
  }

  if (isEmpty) {
    return (
      <EmptyState
        description="No products found for the current filters."
        state="empty"
        title="No products"
      />
    )
  }

  const rows = products.map((product) => ({
    id: product.id,
    sku: product.sku,
    name: product.name,
    currentStock: String(product.currentStock),
    reorderPoint: String(product.reorderPoint),
    status: product.currentStock <= product.reorderPoint ? 'low_stock' : 'in_stock',
  }))

  return (
    <DataTable headers={headers} rows={rows}>
      {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
        <TableContainer title="Products">
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
                        <StatusBadge domain="po" status={String(cell.value)} />
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
