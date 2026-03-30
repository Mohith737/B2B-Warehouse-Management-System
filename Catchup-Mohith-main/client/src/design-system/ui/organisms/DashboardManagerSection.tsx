// client/src/design-system/ui/organisms/DashboardManagerSection.tsx
import {
  ActionableNotification,
  DataTable,
  Grid,
  Column,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'

import { EmptyState, LoadingSkeleton } from '../atoms'
import { MetricCard } from '../molecules'

type ActivityRow = {
  product_name: string
  product_sku: string
  quantity_change: number
  change_type: string
  balance_after: number
  created_at: string
}

type DashboardManagerData = {
  total_products: number
  low_stock_count: number
  pending_grns: number
  open_pos: number
  overdue_backorders: number
  total_suppliers: number
  recent_activity: ActivityRow[]
}

type DashboardManagerSectionProps = {
  data: DashboardManagerData | null
  isLoading: boolean
  error: string | null
  onRetry: () => void
}

const headers = [
  { key: 'product', header: 'Product Name' },
  { key: 'sku', header: 'SKU' },
  { key: 'change', header: 'Change' },
  { key: 'type', header: 'Type' },
  { key: 'balance', header: 'Balance After' },
  { key: 'date', header: 'Date' },
]

export function DashboardManagerSection({
  data,
  isLoading,
  error,
  onRetry,
}: DashboardManagerSectionProps): JSX.Element {
  if (isLoading) {
    return <LoadingSkeleton lines={7} state="loading" />
  }

  if (error) {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={onRetry}
        subtitle={error}
        title="Failed to load dashboard"
      />
    )
  }

  if (!data) {
    return (
      <EmptyState
        description="No dashboard data is currently available."
        state="empty"
        title="No metrics"
      />
    )
  }

  const rows = data.recent_activity.map((entry) => ({
    id: `${entry.product_sku}-${entry.created_at}`,
    product: entry.product_name,
    sku: entry.product_sku,
    change: String(entry.quantity_change),
    type: entry.change_type,
    balance: String(entry.balance_after),
    date: new Date(entry.created_at).toLocaleString(),
  }))

  return (
    <Grid condensed>
      <Column lg={4} md={2} sm={4}>
        <MetricCard label="Total Products" value={data.total_products} />
      </Column>
      <Column lg={4} md={2} sm={4}>
        <MetricCard label="Low Stock" linkTo="/products" value={data.low_stock_count} />
      </Column>
      <Column lg={4} md={2} sm={4}>
        <MetricCard label="Pending GRNs" value={data.pending_grns} />
      </Column>
      <Column lg={4} md={2} sm={4}>
        <MetricCard label="Open POs" value={data.open_pos} />
      </Column>
      <Column lg={4} md={2} sm={4}>
        <MetricCard label="Overdue Backorders" value={data.overdue_backorders} />
      </Column>
      <Column lg={4} md={2} sm={4}>
        <MetricCard label="Total Suppliers" value={data.total_suppliers} />
      </Column>
      <Column lg={16} md={8} sm={4}>
        {rows.length === 0 ? (
          <EmptyState
            description="There is no recent manager activity to display."
            state="empty"
            title="No recent activity"
          />
        ) : (
          <DataTable headers={headers} rows={rows}>
            {({
              rows: dataRows,
              headers: dataHeaders,
              getHeaderProps,
              getTableProps,
            }) => (
              <TableContainer title="Recent Activity">
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
        )}
      </Column>
    </Grid>
  )
}
