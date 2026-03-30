// client/src/features/suppliers/containers/SuppliersContainer.tsx
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuthStore } from '../../../stores/authStore'
import { SuppliersView } from '../components/SuppliersView'
import { SUPPLIERS_CONFIG, SUPPLIER_TIER_FILTERS } from '../constants/suppliersConfig'
import { useSuppliersQuery } from '../hooks/useSuppliersQuery'
import type { SupplierRow, SupplierTier } from '../types'

export function SuppliersContainer(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)

  useEffect(() => {
    if (role === 'warehouse_staff') {
      navigate('/unauthorized')
    }
  }, [navigate, role])

  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState<number>(SUPPLIERS_CONFIG.defaultPage)
  const [pageSize, setPageSize] = useState<number>(SUPPLIERS_CONFIG.defaultPageSize)
  const [tier, setTier] = useState<'all' | SupplierTier>('all')

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      setDebouncedSearch(searchInput.trim())
      setPage(SUPPLIERS_CONFIG.defaultPage)
    }, 300)

    return () => {
      window.clearTimeout(timerId)
    }
  }, [searchInput])

  const query = useSuppliersQuery({
    page,
    pageSize,
    search: debouncedSearch,
    tier,
  })

  const suppliers: SupplierRow[] = useMemo(
    () =>
      (query.data?.data ?? []).map((supplier) => ({
        id: supplier.id,
        name: supplier.name,
        tier: supplier.current_tier,
        creditLimit: supplier.credit_limit,
        leadTimeDays: supplier.lead_time_days,
        paymentTerms: supplier.payment_terms,
        contactEmail: supplier.contact_email,
        status: supplier.is_active ? 'active' : 'inactive',
      })),
    [query.data],
  )

  const totalItems = query.data?.meta.total ?? 0

  return (
    <SuppliersView
      error={query.isError ? (query.error as Error).message : null}
      filterProps={{
        filters: SUPPLIER_TIER_FILTERS,
        activeFilter: tier,
        onFilterChange: (value) => {
          setTier(value as 'all' | SupplierTier)
          setPage(SUPPLIERS_CONFIG.defaultPage)
        },
      }}
      isEmpty={!query.isLoading && !query.isError && suppliers.length === 0}
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
          setPage(SUPPLIERS_CONFIG.defaultPage)
        },
      }}
      searchProps={{
        value: searchInput,
        onChange: setSearchInput,
        placeholder: SUPPLIERS_CONFIG.searchPlaceholder,
      }}
      suppliers={suppliers}
      toolbarTitle={SUPPLIERS_CONFIG.toolbarTitle}
    />
  )
}
