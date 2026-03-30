// client/src/design-system/ui/organisms/SupplierTable.tsx
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

type SupplierRow = {
  id: string
  name: string
  tier: 'Silver' | 'Gold' | 'Diamond'
  creditLimit: number | string
  contactEmail: string
  status: 'active' | 'inactive'
}

type SupplierTableProps = {
  suppliers: SupplierRow[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
}

const headers = [
  { key: 'name', header: 'Name' },
  { key: 'tier', header: 'Tier' },
  { key: 'creditLimit', header: 'Credit Limit' },
  { key: 'contactEmail', header: 'Contact' },
  { key: 'status', header: 'Status' },
]

export function SupplierTable({
  suppliers,
  isLoading,
  isEmpty,
  error,
  onRetry,
}: SupplierTableProps): JSX.Element {
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
        title="Failed to load suppliers"
      />
    )
  }

  if (isEmpty) {
    return (
      <EmptyState
        description="No suppliers found for the selected filters."
        state="empty"
        title="No suppliers"
      />
    )
  }

  const rows = suppliers.map((supplier) => ({
    id: supplier.id,
    name: supplier.name,
    tier: supplier.tier,
    creditLimit: formatCurrency(supplier.creditLimit),
    contactEmail: supplier.contactEmail,
    status: supplier.status,
  }))

  return (
    <DataTable headers={headers} rows={rows}>
      {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
        <TableContainer title="Suppliers">
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
                      {cell.info.header === 'tier' ? (
                        <StatusBadge domain="tier" status={String(cell.value)} />
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
