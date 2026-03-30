// client/src/features/products/containers/ProductsContainer.tsx
import { useEffect, useMemo, useState } from 'react'

import { PRODUCTS_CONFIG } from '../constants/productsConfig'
import { ProductsView } from '../components/ProductsView'
import { useProductsQuery } from '../hooks/useProductsQuery'
import type { ProductRow } from '../types'

export function ProductsContainer(): JSX.Element {
  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState<number>(PRODUCTS_CONFIG.defaultPage)
  const [pageSize, setPageSize] = useState<number>(PRODUCTS_CONFIG.defaultPageSize)

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      setDebouncedSearch(searchInput.trim())
      setPage(PRODUCTS_CONFIG.defaultPage)
    }, 300)

    return () => {
      window.clearTimeout(timerId)
    }
  }, [searchInput])

  const query = useProductsQuery({ page, pageSize, search: debouncedSearch })

  const products: ProductRow[] = useMemo(
    () =>
      (query.data?.data ?? []).map((product) => ({
        id: product.id,
        sku: product.sku,
        name: product.name,
        category: product.category,
        currentStock: product.current_stock,
        reorderPoint: product.reorder_point,
        unitPrice: product.unit_price,
      })),
    [query.data],
  )

  const totalItems = query.data?.meta.total ?? 0

  return (
    <ProductsView
      error={query.isError ? (query.error as Error).message : null}
      isEmpty={!query.isLoading && !query.isError && products.length === 0}
      isLoading={query.isLoading}
      onRetry={() => {
        void query.refetch()
      }}
      paginationProps={{
        page,
        pageSize,
        totalItems,
        onPageChange: setPage,
        onPageSizeChange: (nextPageSize) => {
          setPageSize(nextPageSize)
          setPage(PRODUCTS_CONFIG.defaultPage)
        },
      }}
      products={products}
      searchProps={{
        value: searchInput,
        onChange: setSearchInput,
        placeholder: PRODUCTS_CONFIG.searchPlaceholder,
      }}
      toolbarTitle={PRODUCTS_CONFIG.toolbarTitle}
    />
  )
}
