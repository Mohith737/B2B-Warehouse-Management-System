// client/src/features/purchase-orders/components/PurchaseOrdersView.tsx
import {
  Button,
  Column,
  DataTable,
  Dropdown,
  Grid,
  InlineNotification,
  Row,
  Search,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
  Tag,
  Tile,
} from '@carbon/react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  EmptyState,
  LoadingSkeleton,
  PageTitle,
  StatusBadge,
} from '../../../design-system/ui/atoms'
import { PaginationBar, type FilterOption } from '../../../design-system/ui/molecules'
import { useAuthStore } from '../../../stores/authStore'
import styles from '../../shared/ListPageLayout.module.scss'
import type { PurchaseOrderRead } from '../types'

type PurchaseOrdersViewProps = {
  toolbarTitle: string
  orders: PurchaseOrderRead[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
  searchProps: {
    value: string
    onChange: (value: string) => void
    placeholder: string
  }
  filterProps: {
    filters: FilterOption[]
    activeFilter: string
    onFilterChange: (value: string) => void
  }
  paginationProps: {
    page: number
    pageSize: number
    totalItems: number
    onPageChange: (page: number) => void
    onPageSizeChange: (pageSize: number) => void
  }
}

const headers = [
  { key: 'poNumber', header: 'PO Number' },
  { key: 'supplier', header: 'Supplier' },
  { key: 'status', header: 'Status' },
  { key: 'totalAmount', header: 'Total' },
  { key: 'createdDate', header: 'Created Date' },
  { key: 'createdBy', header: 'Created By' },
]

function formatCurrency(value: number | string): string {
  const numericValue =
    typeof value === 'number' ? value : Number.parseFloat(String(value))
  if (Number.isNaN(numericValue)) {
    return '₹0'
  }

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(numericValue)
}

function formatRelativeDate(value: string): string {
  const createdAt = new Date(value)
  if (Number.isNaN(createdAt.getTime())) {
    return 'N/A'
  }

  const diffMs = Date.now() - createdAt.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 24) {
    return `${Math.max(diffHours, 1)} hours ago`
  }

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) {
    return `${diffDays} days ago`
  }

  return createdAt.toLocaleDateString()
}

export function PurchaseOrdersView({
  toolbarTitle,
  orders,
  isLoading,
  isEmpty,
  error,
  onRetry,
  searchProps,
  filterProps,
  paginationProps,
}: PurchaseOrdersViewProps): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const canCreate = role === 'procurement_manager'

  const activeStatus = useMemo(
    () =>
      filterProps.filters.find((filter) => filter.value === filterProps.activeFilter) ??
      filterProps.filters[0],
    [filterProps.activeFilter, filterProps.filters],
  )

  const totalValue = useMemo(
    () =>
      orders.reduce((sum, order) => {
        const numeric = Number(order.total_amount)
        return sum + (Number.isNaN(numeric) ? 0 : numeric)
      }, 0),
    [orders],
  )

  const rows = orders.map((order) => ({
    id: order.id,
    poNumber: order.po_number,
    supplier: order.supplier_name,
    status: order.status,
    totalAmount: formatCurrency(order.total_amount),
    createdDate: formatRelativeDate(order.created_at),
    createdBy: order.created_by_name ?? order.created_by ?? 'System',
  }))
  const dueSoonCount = useMemo(
    () =>
      orders.filter((order) => {
        const diffHours =
          (Date.now() - new Date(order.created_at).getTime()) / (1000 * 60 * 60)
        return diffHours <= 24
      }).length,
    [orders],
  )

  return (
    <div className={styles.pageShell}>
      <Grid className={styles.grid} fullWidth>
        <Row className={styles.headerRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.headerContent}>
              <PageTitle
                subtitle={`${paginationProps.totalItems} orders · ${formatCurrency(totalValue)} total`}
                title={toolbarTitle}
              />
              {canCreate ? (
                <Button kind="primary" onClick={() => navigate('/purchase-orders/new')}>
                  Create PO
                </Button>
              ) : null}
            </div>
          </Column>
        </Row>

        <Row className={styles.summaryRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Total Orders</p>
                <p className={styles.summaryValue}>{paginationProps.totalItems}</p>
              </div>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Total Value</p>
                <p className={styles.summaryValue}>{formatCurrency(totalValue)}</p>
              </div>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Created Today</p>
                <p className={styles.summaryValue}>{dueSoonCount}</p>
              </div>
            </div>
          </Column>
        </Row>

        <Row className={styles.filtersRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.filtersContent}>
              <div className={styles.filterControls}>
                <div className={styles.searchControl}>
                  <Search
                    id="po-list-search"
                    labelText="Search purchase orders"
                    onChange={(event) => {
                      searchProps.onChange(event.currentTarget.value)
                    }}
                    placeholder={searchProps.placeholder}
                    size="lg"
                    value={searchProps.value}
                  />
                </div>
                <div className={styles.dropdownControl}>
                  <Dropdown
                    id="po-status-filter"
                    itemToString={(item) => item?.label ?? ''}
                    items={filterProps.filters}
                    label="PO status"
                    onChange={({ selectedItem }) => {
                      if (selectedItem) {
                        filterProps.onFilterChange(selectedItem.value)
                      }
                    }}
                    selectedItem={activeStatus}
                    titleText="Status"
                  />
                </div>
              </div>
              <div className={styles.activeFilters}>
                {searchProps.value.trim() ? (
                  <Tag
                    filter
                    onClose={() => {
                      searchProps.onChange('')
                    }}
                    type="blue"
                  >
                    Search: {searchProps.value.trim()}
                  </Tag>
                ) : null}
                {filterProps.activeFilter !== 'all' ? (
                  <Tag
                    filter
                    onClose={() => {
                      filterProps.onFilterChange('all')
                    }}
                    type="teal"
                  >
                    Status: {activeStatus?.label ?? 'All'}
                  </Tag>
                ) : null}
              </div>
            </div>
          </Column>
        </Row>

        <Row className={styles.tableRow}>
          <Column lg={16} md={8} sm={4}>
            <Tile className={styles.tableCard}>
              {isLoading ? (
                <LoadingSkeleton lines={8} state="loading" />
              ) : error ? (
                <>
                  <InlineNotification
                    hideCloseButton
                    kind="error"
                    subtitle={error}
                    title="Failed to load purchase orders"
                  />
                  <Button kind="ghost" onClick={onRetry} size="sm">
                    Retry
                  </Button>
                </>
              ) : isEmpty || rows.length === 0 ? (
                <EmptyState
                  action={
                    canCreate
                      ? {
                          label: 'Create First PO',
                          onClick: () => navigate('/purchase-orders/new'),
                        }
                      : undefined
                  }
                  description="No purchase orders match the selected filters for your role."
                  state="empty"
                  title="No purchase orders"
                />
              ) : (
                <DataTable headers={headers} rows={rows}>
                  {({
                    rows: tableRows,
                    headers: tableHeaders,
                    getHeaderProps,
                    getTableProps,
                  }) => (
                    <TableContainer>
                      <Table {...getTableProps()} className={styles.dataTable}>
                        <TableHead>
                          <TableRow>
                            {tableHeaders.map((header) => (
                              <TableHeader
                                {...getHeaderProps({ header })}
                                key={header.key}
                              >
                                {header.header}
                              </TableHeader>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {tableRows.map((row) => (
                            <TableRow
                              className={styles.rowClickable}
                              key={row.id}
                              onClick={() => navigate(`/purchase-orders/${row.id}`)}
                            >
                              {row.cells.map((cell) => {
                                if (cell.info.header === 'poNumber') {
                                  return (
                                    <TableCell
                                      className={styles.monospace}
                                      key={cell.id}
                                    >
                                      {cell.value}
                                    </TableCell>
                                  )
                                }

                                if (cell.info.header === 'status') {
                                  return (
                                    <TableCell key={cell.id}>
                                      <StatusBadge status={String(cell.value)} />
                                    </TableCell>
                                  )
                                }

                                if (cell.info.header === 'totalAmount') {
                                  return (
                                    <TableCell
                                      className={styles.rightAlign}
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
              )}
            </Tile>
          </Column>
        </Row>

        <Row className={styles.paginationRow}>
          <Column className={styles.paginationFlush} lg={16} md={8} sm={4}>
            <PaginationBar
              onPageChange={paginationProps.onPageChange}
              onPageSizeChange={paginationProps.onPageSizeChange}
              page={paginationProps.page}
              pageSize={paginationProps.pageSize}
              totalItems={paginationProps.totalItems}
            />
          </Column>
        </Row>
      </Grid>
    </div>
  )
}
