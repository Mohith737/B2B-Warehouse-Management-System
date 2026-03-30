// client/src/features/stock-ledger/containers/StockLedgerContainer.tsx
import { StockLedgerView } from '../components/StockLedgerView'
import { useStockLedgerQuery } from '../hooks/useStockLedgerQuery'

export function StockLedgerContainer(): JSX.Element {
  const query = useStockLedgerQuery()

  return (
    <StockLedgerView
      error={query.isError ? (query.error as Error).message : null}
      isFetchingNextPage={query.isFetchingNextPage}
      isLoading={query.isLoading}
      onLoadMore={() => {
        void query.fetchNextPage()
      }}
      onRetry={() => {
        void query.refetch()
      }}
      pages={query.data?.pages ?? []}
    />
  )
}
