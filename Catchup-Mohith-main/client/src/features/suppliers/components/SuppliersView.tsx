// client/src/features/suppliers/components/SuppliersView.tsx
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
import type { SupplierRow } from '../types'

type SuppliersViewProps = {
  toolbarTitle: string
  suppliers: SupplierRow[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
  searchProps: {
    value: string
    onChange: (value: string) => void
    placeholder: string
  }
  paginationProps: {
    page: number
    pageSize: number
    totalItems: number
    onPageChange: (page: number) => void
    onPageSizeChange: (pageSize: number) => void
  }
  filterProps: {
    filters: FilterOption[]
    activeFilter: string
    onFilterChange: (value: string) => void
  }
}

const headers = [
  { key: 'name', header: 'Supplier Name' },
  { key: 'tier', header: 'Current Tier' },
  { key: 'creditLimit', header: 'Credit Limit' },
  { key: 'leadTime', header: 'Lead Time' },
  { key: 'paymentTerms', header: 'Payment Terms' },
  { key: 'status', header: 'Status' },
]

function formatCurrency(value: number | string): string {
  const numericValue =
    typeof value === 'number' ? value : Number.parseFloat(String(value))
  if (Number.isNaN(numericValue)) {
    return 'N/A'
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(numericValue)
}

export function SuppliersView({
  toolbarTitle,
  suppliers,
  isLoading,
  isEmpty,
  error,
  onRetry,
  searchProps,
  paginationProps,
  filterProps,
}: SuppliersViewProps): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const canCreate = role === 'procurement_manager' || role === 'admin'

  const activeTier = useMemo(
    () =>
      filterProps.filters.find((filter) => filter.value === filterProps.activeFilter) ??
      filterProps.filters[0],
    [filterProps.activeFilter, filterProps.filters],
  )
  const activeSuppliers = useMemo(
    () => suppliers.filter((supplier) => supplier.status === 'active').length,
    [suppliers],
  )
  const diamondSuppliers = useMemo(
    () => suppliers.filter((supplier) => supplier.tier === 'Diamond').length,
    [suppliers],
  )

  const rows = suppliers.map((supplier) => ({
    id: supplier.id,
    name: supplier.name,
    tier: supplier.tier,
    creditLimit: formatCurrency(supplier.creditLimit),
    leadTime: supplier.leadTimeDays ? `${supplier.leadTimeDays} days` : 'N/A',
    paymentTerms: supplier.paymentTerms ?? 'N/A',
    status: supplier.status,
  }))

  return (
    <div className={styles.pageShell}>
      <Grid className={styles.grid} fullWidth>
        <Row className={styles.headerRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.headerContent}>
              <PageTitle
                subtitle={`${paginationProps.totalItems} suppliers`}
                title={toolbarTitle}
              />
              {canCreate ? (
                <Button kind="primary" onClick={() => navigate('/suppliers/new')}>
                  Add Supplier
                </Button>
              ) : null}
            </div>
          </Column>
        </Row>

        <Row className={styles.summaryRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Total Suppliers</p>
                <p className={styles.summaryValue}>{paginationProps.totalItems}</p>
              </div>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Active Suppliers</p>
                <p className={styles.summaryValue}>{activeSuppliers}</p>
              </div>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Diamond Tier</p>
                <p className={styles.summaryValue}>{diamondSuppliers}</p>
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
                    id="suppliers-list-search"
                    labelText="Search suppliers"
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
                    id="suppliers-tier-filter"
                    itemToString={(item) => item?.label ?? ''}
                    items={filterProps.filters}
                    label="Supplier tier"
                    onChange={({ selectedItem }) => {
                      if (selectedItem) {
                        filterProps.onFilterChange(selectedItem.value)
                      }
                    }}
                    selectedItem={activeTier}
                    titleText="Tier"
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
                    Tier: {activeTier?.label ?? 'All'}
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
                    title="Failed to load suppliers"
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
                          label: 'Add First Supplier',
                          onClick: () => navigate('/suppliers/new'),
                        }
                      : undefined
                  }
                  description="No suppliers match the selected filters for your role."
                  state="empty"
                  title="No suppliers"
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
                              onClick={() => navigate(`/suppliers/${row.id}`)}
                            >
                              {row.cells.map((cell) => {
                                if (cell.info.header === 'tier') {
                                  return (
                                    <TableCell key={cell.id}>
                                      <StatusBadge status={String(cell.value)} />
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

                                if (cell.info.header === 'creditLimit') {
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
