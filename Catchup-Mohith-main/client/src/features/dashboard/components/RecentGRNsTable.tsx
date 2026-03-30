// client/src/features/dashboard/components/RecentGRNsTable.tsx
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
import type { DashboardRecentGRN } from '../types'

type RecentGRNsTableProps = {
  data: DashboardRecentGRN[]
}

const headers = [
  { key: 'grnNo', header: 'GRN No' },
  { key: 'supplier', header: 'Supplier' },
  { key: 'date', header: 'Date' },
  { key: 'status', header: 'Status' },
]

export function RecentGRNsTable({ data }: RecentGRNsTableProps): JSX.Element {
  const rows = data.map((row) => ({
    id: row.id,
    grnNo: row.grnNo,
    supplier: row.supplier,
    date: new Date(row.date).toLocaleDateString(),
    status: row.status,
  }))

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

                    if (cell.info.header === 'grnNo') {
                      return (
                        <TableCell className={styles.monospace} key={cell.id}>
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
