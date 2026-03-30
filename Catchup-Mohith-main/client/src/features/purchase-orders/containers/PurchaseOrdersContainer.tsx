// client/src/features/purchase-orders/containers/PurchaseOrdersContainer.tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuthStore } from '../../../stores/authStore'
import { PO_CONFIG, PO_STATUS_FILTERS } from '../constants/poConfig'
import { PurchaseOrdersView } from '../components/PurchaseOrdersView'
import { usePurchaseOrdersQuery } from '../hooks/usePurchaseOrdersQuery'
import type { PurchaseOrderStatus } from '../types'

export function PurchaseOrdersContainer(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)

  useEffect(() => {
    if (role === 'warehouse_staff') {
      navigate('/unauthorized')
    }
  }, [navigate, role])

  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState<number>(PO_CONFIG.defaultPage)
  const [pageSize, setPageSize] = useState<number>(PO_CONFIG.defaultPageSize)
  const [status, setStatus] = useState<'all' | PurchaseOrderStatus>('all')

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      setDebouncedSearch(searchInput.trim())
      setPage(PO_CONFIG.defaultPage)
    }, 300)

    return () => {
      window.clearTimeout(timerId)
    }
  }, [searchInput])

  const query = usePurchaseOrdersQuery({
    page,
    pageSize,
    search: debouncedSearch,
    status,
  })

  return (
    <PurchaseOrdersView
      error={query.isError ? (query.error as Error).message : null}
      filterProps={{
        filters: PO_STATUS_FILTERS,
        activeFilter: status,
        onFilterChange: (value) => {
          setStatus(value as 'all' | PurchaseOrderStatus)
          setPage(PO_CONFIG.defaultPage)
        },
      }}
      isEmpty={
        !query.isLoading && !query.isError && (query.data?.data?.length ?? 0) === 0
      }
      isLoading={query.isLoading}
      onRetry={() => {
        void query.refetch()
      }}
      orders={query.data?.data ?? []}
      paginationProps={{
        page,
        pageSize,
        totalItems: query.data?.meta.total ?? 0,
        onPageChange: setPage,
        onPageSizeChange: (nextPageSize) => {
          setPageSize(nextPageSize)
          setPage(PO_CONFIG.defaultPage)
        },
      }}
      searchProps={{
        value: searchInput,
        onChange: setSearchInput,
        placeholder: PO_CONFIG.searchPlaceholder,
      }}
      toolbarTitle={PO_CONFIG.toolbarTitle}
    />
  )
}
