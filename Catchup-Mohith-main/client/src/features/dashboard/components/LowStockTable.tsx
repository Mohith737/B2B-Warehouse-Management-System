// client/src/features/dashboard/components/LowStockTable.tsx
import {
  DataTable,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'

import { StatusBadge } from '../../../design-system/ui/atoms'
import styles from '../dashboard.module.scss'
import type { DashboardLowStockProduct } from '../types'

type LowStockTableProps = {
  data: DashboardLowStockProduct[]
}

const headers = [
  { key: 'name', header: 'Product Name' },
  { key: 'sku', header: 'SKU' },
  { key: 'stock', header: 'Stock' },
  { key: 'status', header: 'Status' },
]

function toNumber(value: number | string | null | undefined): number {
  if (typeof value === 'number') {
    return value
  }
  const parsed = Number.parseFloat(String(value ?? 0))
  return Number.isNaN(parsed) ? 0 : parsed
}

export function LowStockTable({ data }: LowStockTableProps): JSX.Element {
  const rows = data.map((row) => {
    const stock = toNumber(row.current_stock)
    const reorder = toNumber(row.reorder_point)
    const stockStatus =
      stock <= 0 ? 'critical' : stock <= reorder ? 'warning' : 'normal'

    return {
      id: row.id,
      name: row.name,
      sku: row.sku,
      stock: String(stock),
      status: stockStatus,
    }
  })

  return (
    <DataTable headers={headers} rows={rows}>
      {({ rows: tableRows, headers: tableHeaders, getHeaderProps, getTableProps }) => (
        <TableContainer>
          <Table {...getTableProps()} size="sm">
            <TableHead>
              <TableRow>
                {tableHeaders.map((header) => {
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
              {tableRows.map((row) => (
                <TableRow key={row.id}>
                  {row.cells.map((cell) => {
                    if (cell.info.header === 'status') {
                      return (
                        <TableCell key={cell.id}>
                          <StatusBadge status={String(cell.value)} />
                        </TableCell>
                      )
                    }

                    if (cell.info.header === 'stock') {
                      return (
                        <TableCell
                          className={`${styles.rightAligned} ${
                            cell.value === '0'
                              ? styles.stockCritical
                              : row.cells.find(
                                    (candidate) => candidate.info.header === 'status',
                                  )?.value === 'warning'
                                ? styles.stockWarning
                                : ''
                          }`}
                          key={cell.id}
                        >
                          {cell.value}
                        </TableCell>
                      )
                    }

                    return <TableCell key={cell.id}>{cell.value}</TableCell>
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </DataTable>
  )
}
