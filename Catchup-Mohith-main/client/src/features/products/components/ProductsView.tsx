// client/src/features/products/components/ProductsView.tsx
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
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  EmptyState,
  LoadingSkeleton,
  PageTitle,
  StatusBadge,
} from '../../../design-system/ui/atoms'
import { PaginationBar } from '../../../design-system/ui/molecules'
import { useAuthStore } from '../../../stores/authStore'
import styles from '../../shared/ListPageLayout.module.scss'
import type { ProductRow } from '../types'

type ProductsViewProps = {
  toolbarTitle: string
  products: ProductRow[]
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
}

type StockFilterOption = {
  value: 'all' | 'low_stock' | 'out_of_stock' | 'normal'
  label: string
}

const stockFilterOptions: StockFilterOption[] = [
  { value: 'all', label: 'All' },
  { value: 'low_stock', label: 'Low Stock' },
  { value: 'out_of_stock', label: 'Out of Stock' },
  { value: 'normal', label: 'Normal' },
]

const headers = [
  { key: 'sku', header: 'SKU' },
  { key: 'name', header: 'Product Name' },
  { key: 'category', header: 'Category' },
  { key: 'currentStock', header: 'Current Stock' },
  { key: 'status', header: 'Status' },
  { key: 'reorderPoint', header: 'Reorder Point' },
  { key: 'unitPrice', header: 'Unit Price' },
]

function getStockStatus(product: ProductRow): 'critical' | 'warning' | 'normal' {
  if (product.currentStock <= 0) {
    return 'critical'
  }
  if (product.currentStock <= product.reorderPoint) {
    return 'warning'
  }
  return 'normal'
}

function formatCurrency(value?: number | null): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'N/A'
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

export function ProductsView({
  toolbarTitle,
  products,
  isLoading,
  isEmpty,
  error,
  onRetry,
  searchProps,
  paginationProps,
}: ProductsViewProps): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const [stockFilter, setStockFilter] = useState<StockFilterOption>(
    stockFilterOptions[0],
  )
  const canCreate = role !== 'warehouse_staff'

  const lowStockCount = useMemo(
    () =>
      products.filter(
        (product) =>
          product.currentStock > 0 && product.currentStock <= product.reorderPoint,
      ).length,
    [products],
  )

  const filteredProducts = useMemo(() => {
    if (stockFilter.value === 'all') {
      return products
    }

    return products.filter((product) => {
      const status = getStockStatus(product)
      if (stockFilter.value === 'out_of_stock') {
        return status === 'critical'
      }
      if (stockFilter.value === 'low_stock') {
        return status === 'warning'
      }
      return status === 'normal'
    })
  }, [products, stockFilter.value])
  const outOfStockCount = useMemo(
    () => products.filter((product) => product.currentStock <= 0).length,
    [products],
  )

  const rows = filteredProducts.map((product) => {
    const stockStatus = getStockStatus(product)
    return {
      id: product.id,
      sku: product.sku,
      name: product.name,
      category: product.category ?? 'Uncategorized',
      currentStock: String(product.currentStock),
      status: stockStatus,
      reorderPoint: String(product.reorderPoint),
      unitPrice: formatCurrency(product.unitPrice),
    }
  })

  return (
    <div className={styles.pageShell}>
      <Grid className={styles.grid} fullWidth>
        <Row className={styles.headerRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.headerContent}>
              <PageTitle
                subtitle={`${paginationProps.totalItems} products · ${lowStockCount} low stock`}
                title={toolbarTitle}
              />
              {canCreate ? (
                <Button kind="primary" onClick={() => navigate('/products/new')}>
                  Add Product
                </Button>
              ) : null}
            </div>
          </Column>
        </Row>

        <Row className={styles.summaryRow}>
          <Column lg={16} md={8} sm={4}>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Total Products</p>
                <p className={styles.summaryValue}>{paginationProps.totalItems}</p>
              </div>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Low Stock</p>
                <p className={styles.summaryValue}>{lowStockCount}</p>
              </div>
              <div className={styles.summaryCard}>
                <p className={styles.summaryLabel}>Out of Stock</p>
                <p className={styles.summaryValue}>{outOfStockCount}</p>
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
                    id="products-list-search"
                    labelText="Search products"
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
                    id="products-stock-filter"
                    itemToString={(item) => item?.label ?? ''}
                    items={stockFilterOptions}
                    label="Stock status"
                    onChange={({ selectedItem }) => {
                      if (selectedItem) {
                        setStockFilter(selectedItem)
                      }
                    }}
                    selectedItem={stockFilter}
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
                {stockFilter.value !== 'all' ? (
                  <Tag
                    filter
                    onClose={() => {
                      setStockFilter(stockFilterOptions[0])
                    }}
                    type="teal"
                  >
                    {stockFilter.label}
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
                    title="Failed to load products"
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
                          label: 'Add First Product',
                          onClick: () => navigate('/products/new'),
                        }
                      : undefined
                  }
                  description="No products match the selected filters for your role."
                  state="empty"
                  title="No products"
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
                              onClick={() => navigate(`/products/${row.id}`)}
                            >
                              {row.cells.map((cell) => {
                                if (cell.info.header === 'currentStock') {
                                  const status = row.cells.find(
                                    (candidate) => candidate.info.header === 'status',
                                  )?.value
                                  const tagType =
                                    status === 'critical'
                                      ? 'red'
                                      : status === 'warning'
                                        ? 'magenta'
                                        : 'green'
                                  return (
                                    <TableCell key={cell.id}>
                                      <Tag type={tagType as never}>{cell.value}</Tag>
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

                                if (cell.info.header === 'unitPrice') {
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
